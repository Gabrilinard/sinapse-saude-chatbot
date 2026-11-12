import asyncio
import json

from sinapse.chatbot.catalogo import CatalogoDeFerramentas
from sinapse.chatbot.conversa import ChamadaDeFerramenta, Conversa, Mensagem, Papel, ResultadoDeFerramenta
from sinapse.chatbot.instrucoes import montar_instrucoes
from sinapse.chatbot.portas import ConectarFerramentas, ModeloDeLinguagem, ModeloIndisponivel, ProvedorDeFerramentas
from sinapse.chatbot.seguranca import (AGUARDANDO_CONFIRMACAO, PERGUNTA_DE_CONFIRMACAO, RESPOSTA_DE_EMERGENCIA,
                                       DetectorDeEmergencia, PoliticaDeConfirmacao)
from sinapse.dominio.modelos import SessaoUsuario

MAXIMO_DE_CICLOS = 5
RESPOSTA_VAZIA = "Desculpe, não entendi. Pode repetir?"
LIMITE_DE_CICLOS_ATINGIDO = "Não consegui concluir o pedido agora. Quer que eu transfira para um atendente?"
FERRAMENTA_NAO_PERMITIDA = "Ferramenta não disponível para este perfil."
NAO_EXECUTADA = "NÃO EXECUTADA: o usuário ainda precisa confirmar outra ação desta mesma mensagem."
DESCREVER_ACAO = "descrever_acao"


class Assistente:
    def __init__(self, modelo: ModeloDeLinguagem, conectar_ferramentas: ConectarFerramentas,
                 detector: DetectorDeEmergencia | None = None, politica: PoliticaDeConfirmacao | None = None,
                 maximo_de_ciclos: int = MAXIMO_DE_CICLOS):
        self._modelo = modelo
        self._conectar_ferramentas = conectar_ferramentas
        self._detector = detector or DetectorDeEmergencia()
        self._politica = politica or PoliticaDeConfirmacao()
        self._maximo_de_ciclos = maximo_de_ciclos

    def responder(self, conversa: Conversa, texto_do_usuario: str, sessao: SessaoUsuario) -> str:
        with conversa.tentativa():
            conversa.adicionar(Mensagem.do_usuario(texto_do_usuario))
            if self._detector.detectar(texto_do_usuario):
                conversa.acao_pendente = None
                return self._encerrar_rodada(conversa, RESPOSTA_DE_EMERGENCIA)
            return asyncio.run(self._conversar(conversa, sessao))

    async def _conversar(self, conversa: Conversa, sessao: SessaoUsuario) -> str:
        async with self._conectar_ferramentas() as provedor:
            catalogo = CatalogoDeFerramentas(await provedor.listar(), sessao.perfil)
            instrucoes = montar_instrucoes(sessao)
            confirmada = self._politica.retomar(conversa)
            if confirmada is not None:
                return await self._executar_acao_confirmada(provedor, catalogo, conversa, sessao, instrucoes,
                                                            confirmada.nome, json.loads(confirmada.argumentos))
            for _ in range(self._maximo_de_ciclos):
                resposta = self._modelo.gerar(instrucoes, conversa.mensagens, catalogo.para_o_modelo())
                if not resposta.chamadas:
                    return self._encerrar_rodada(conversa, resposta.texto.strip() or RESPOSTA_VAZIA)
                conversa.adicionar(resposta)
                resultados, pergunta = [], None
                for chamada in resposta.chamadas:
                    if pergunta is not None:
                        resultados.append(ResultadoDeFerramenta(chamada.nome, NAO_EXECUTADA))
                        continue
                    resultado, pergunta = await self._executar(provedor, catalogo, chamada, conversa, sessao)
                    resultados.append(resultado)
                conversa.adicionar(Mensagem.com_resultados(resultados))
                if pergunta is not None:
                    return self._encerrar_rodada(conversa, pergunta)
        return self._encerrar_rodada(conversa, LIMITE_DE_CICLOS_ATINGIDO)

    async def _executar(self, provedor: ProvedorDeFerramentas, catalogo: CatalogoDeFerramentas,
                        chamada: ChamadaDeFerramenta, conversa: Conversa,
                        sessao: SessaoUsuario) -> tuple[ResultadoDeFerramenta, str | None]:
        if not catalogo.permite(chamada.nome):
            return ResultadoDeFerramenta(chamada.nome, FERRAMENTA_NAO_PERMITIDA), None
        argumentos = catalogo.argumentos_do_modelo(chamada.argumentos)
        if self._politica.exige_confirmacao(chamada.nome):
            return await self._propor_acao(provedor, catalogo, chamada.nome, argumentos, conversa, sessao)
        argumentos |= catalogo.argumentos_da_sessao(chamada.nome, sessao)
        return ResultadoDeFerramenta(chamada.nome, await self._chamar(provedor, chamada.nome, argumentos)), None

    async def _propor_acao(self, provedor: ProvedorDeFerramentas, catalogo: CatalogoDeFerramentas, nome: str,
                           argumentos: dict, conversa: Conversa,
                           sessao: SessaoUsuario) -> tuple[ResultadoDeFerramenta, str | None]:
        previa = await self._chamar(provedor, DESCREVER_ACAO, {
            "acao": nome, "argumentos": argumentos, "paciente_id": sessao.paciente_id})
        descricao = _descricao_da_previa(previa)
        if descricao is None:
            return ResultadoDeFerramenta(nome, previa), None
        self._politica.registrar(conversa, nome, argumentos)
        return (ResultadoDeFerramenta(nome, AGUARDANDO_CONFIRMACAO.format(descricao=descricao)),
                PERGUNTA_DE_CONFIRMACAO.format(descricao=descricao))

    async def _executar_acao_confirmada(self, provedor: ProvedorDeFerramentas, catalogo: CatalogoDeFerramentas,
                                        conversa: Conversa, sessao: SessaoUsuario, instrucoes: str, nome: str,
                                        argumentos: dict) -> str:
        if not catalogo.permite(nome):
            return self._encerrar_rodada(conversa, FERRAMENTA_NAO_PERMITIDA)
        completos = argumentos | catalogo.argumentos_da_sessao(nome, sessao)
        resultado = await self._chamar(provedor, nome, completos)
        conversa.adicionar(Mensagem(Papel.MODELO, "", (ChamadaDeFerramenta(nome, argumentos),)))
        conversa.adicionar(Mensagem.com_resultados([ResultadoDeFerramenta(nome, resultado)]))
        try:
            resposta = self._modelo.gerar(instrucoes, conversa.mensagens, catalogo.para_o_modelo(),
                                          somente_texto=True)
            texto = resposta.texto.strip()
        except ModeloIndisponivel:
            texto = ""
        return self._encerrar_rodada(conversa, texto or _resumo_do_resultado(resultado))

    async def _chamar(self, provedor: ProvedorDeFerramentas, nome: str, argumentos: dict) -> str:
        return await provedor.executar(nome, argumentos)

    @staticmethod
    def _encerrar_rodada(conversa: Conversa, texto: str) -> str:
        conversa.adicionar(Mensagem.do_modelo(texto))
        return texto


def _resumo_do_resultado(resultado: str) -> str:
    try:
        dados = json.loads(resultado)
    except (TypeError, ValueError):
        return resultado
    if not isinstance(dados, dict):
        return resultado
    partes = [dados.get("mensagem", "Pronto.")]
    if dados.get("profissional") and dados.get("data_hora"):
        partes.append(f"{dados['profissional']}, {dados['data_hora']}.")
    return " ".join(partes)


def _descricao_da_previa(previa: str) -> str | None:
    try:
        dados = json.loads(previa)
    except (TypeError, ValueError):
        return None
    return dados.get("descricao") if isinstance(dados, dict) else None
