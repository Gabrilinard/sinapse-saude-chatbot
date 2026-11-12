import sys
import time
from dataclasses import dataclass

import httpx
from google import genai
from google.genai import errors, types

from sinapse.chatbot.conversa import ChamadaDeFerramenta, Mensagem, Papel
from sinapse.chatbot.portas import DefinicaoDeFerramenta, LimiteDeUsoAtingido, ModeloIndisponivel
from sinapse.config import ConfiguracaoGemini

CHAVES_IGNORADAS_NO_SCHEMA = {"title", "default"}
LIMITE_DE_USO = 429
SOBRECARGA = 503
ERROS_TEMPORARIOS = {LIMITE_DE_USO, SOBRECARGA}
PAUSA_APOS_ERRO_TEMPORARIO = 60
ASSINATURA_NEUTRA = b"skip_thought_signature_validator"
SEM_RETENTATIVAS_INTERNAS = types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=1))


@dataclass(frozen=True)
class AssinaturaGemini:
    modelo: str
    valor: bytes

    def para(self, modelo: str) -> bytes:
        return self.valor if modelo == self.modelo else ASSINATURA_NEUTRA


def _adaptar_schema(schema):
    if isinstance(schema, list):
        return [_adaptar_schema(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    opcoes = schema.get("anyOf")
    if opcoes:
        nao_nulas = [opcao for opcao in opcoes if opcao.get("type") != "null"]
        if len(nao_nulas) == 1:
            restante = {chave: valor for chave, valor in schema.items() if chave != "anyOf"}
            return _adaptar_schema({**nao_nulas[0], **restante})
    return {chave: _adaptar_schema(valor) for chave, valor in schema.items()
            if chave not in CHAVES_IGNORADAS_NO_SCHEMA}


def _para_declaracao(ferramenta: DefinicaoDeFerramenta) -> types.FunctionDeclaration:
    return types.FunctionDeclaration(
        name=ferramenta.nome,
        description=ferramenta.descricao,
        parameters_json_schema=_adaptar_schema(ferramenta.parametros),
    )


def _assinatura_para(chamada: ChamadaDeFerramenta, modelo: str) -> bytes:
    if isinstance(chamada.assinatura, AssinaturaGemini):
        return chamada.assinatura.para(modelo)
    return ASSINATURA_NEUTRA


def _para_conteudo(mensagem: Mensagem, modelo: str) -> types.Content:
    if mensagem.papel == Papel.USUARIO:
        return types.Content(role="user", parts=[types.Part(text=mensagem.texto)])
    if mensagem.papel == Papel.FERRAMENTA:
        return types.Content(role="user", parts=[
            types.Part.from_function_response(name=r.nome, response={"resultado": r.conteudo})
            for r in mensagem.resultados
        ])
    partes = [types.Part(text=mensagem.texto)] if mensagem.texto else []
    partes += [
        types.Part(function_call=types.FunctionCall(name=c.nome, args=c.argumentos),
                   thought_signature=_assinatura_para(c, modelo))
        for c in mensagem.chamadas
    ]
    return types.Content(role="model", parts=partes)


def _para_mensagem(resposta: types.GenerateContentResponse, modelo: str) -> Mensagem:
    candidato = resposta.candidates[0] if resposta.candidates else None
    partes = (candidato.content.parts or []) if candidato and candidato.content else []
    texto = "".join(parte.text for parte in partes if parte.text and not parte.thought)
    chamadas = tuple(
        ChamadaDeFerramenta(
            parte.function_call.name,
            dict(parte.function_call.args or {}),
            AssinaturaGemini(modelo, parte.thought_signature) if parte.thought_signature else None,
        )
        for parte in partes if parte.function_call
    )
    return Mensagem(Papel.MODELO, texto, chamadas)


class _PausaDosModelos:
    def __init__(self):
        self._ate: dict[str, float] = {}

    def pausar(self, modelo: str) -> None:
        self._ate[modelo] = time.monotonic() + PAUSA_APOS_ERRO_TEMPORARIO

    def disponiveis(self, modelos: tuple[str, ...]) -> tuple[str, ...]:
        agora = time.monotonic()
        livres = tuple(m for m in modelos if self._ate.get(m, 0) <= agora)
        return livres or modelos


_PAUSA = _PausaDosModelos()


class ModeloGemini:
    def __init__(self, configuracao: ConfiguracaoGemini):
        self._configuracao = configuracao
        self._cliente = (
            genai.Client(api_key=configuracao.chave_api, http_options=SEM_RETENTATIVAS_INTERNAS)
            if configuracao.chave_api else None
        )

    def gerar(self, instrucoes: str, historico: list[Mensagem], ferramentas: list[DefinicaoDeFerramenta],
              somente_texto: bool = False) -> Mensagem:
        if self._cliente is None:
            raise ModeloIndisponivel("GEMINI_API_KEY não configurada no .env")
        ultimo_erro = None
        for modelo in _PAUSA.disponiveis(self._configuracao.modelos_em_ordem):
            try:
                return self._gerar_com(modelo, instrucoes, historico, ferramentas, somente_texto)
            except errors.APIError as erro:
                if erro.code not in ERROS_TEMPORARIOS:
                    raise ModeloIndisponivel(str(erro)) from erro
                print(f"[gemini] {modelo} indisponível ({erro.code}), tentando o próximo", file=sys.stderr)
                _PAUSA.pausar(modelo)
                ultimo_erro = erro
            except httpx.HTTPError as erro:
                raise ModeloIndisponivel(str(erro)) from erro
        if ultimo_erro.code == LIMITE_DE_USO:
            raise LimiteDeUsoAtingido(str(ultimo_erro)) from ultimo_erro
        raise ModeloIndisponivel(str(ultimo_erro)) from ultimo_erro

    def _gerar_com(self, modelo: str, instrucoes: str, historico: list[Mensagem],
                   ferramentas: list[DefinicaoDeFerramenta], somente_texto: bool) -> Mensagem:
        modo = "NONE" if somente_texto else "AUTO"
        resposta = self._cliente.models.generate_content(
            model=modelo,
            contents=[_para_conteudo(mensagem, modelo) for mensagem in historico],
            config=types.GenerateContentConfig(
                system_instruction=instrucoes,
                temperature=self._configuracao.temperatura,
                tools=[types.Tool(function_declarations=[_para_declaracao(f) for f in ferramentas])],
                tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(mode=modo)),
            ),
        )
        return _para_mensagem(resposta, modelo)
