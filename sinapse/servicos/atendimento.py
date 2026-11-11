import re
from typing import Optional

from sinapse.dominio.erros import NadaEncontrado
from sinapse.dominio.formatacao import remover_acentos
from sinapse.infraestrutura.notificador import Evento, Notificador
from sinapse.servicos import AbrirTransacao

TAMANHO_MINIMO_DA_PALAVRA = 3
MAXIMO_DE_RESPOSTAS = 3
TAMANHO_MAXIMO_DO_MOTIVO = 500


def _palavras_relevantes(texto: str) -> list[str]:
    return [p for p in re.findall(r"\w+", remover_acentos(texto)) if len(p) >= TAMANHO_MINIMO_DA_PALAVRA]


def _pontuacao(item: dict, palavras: list[str]) -> int:
    alvo = remover_acentos(f"{item['palavras_chave']} {item['pergunta']}")
    return sum(1 for palavra in palavras if palavra in alvo)


class ServicoDeAtendimento:
    def __init__(self, abrir_transacao: AbrirTransacao, notificador: Notificador):
        self._abrir_transacao = abrir_transacao
        self._notificador = notificador

    def responder_duvida(self, termo: str) -> list[dict]:
        palavras = _palavras_relevantes(termo or "")
        with self._abrir_transacao() as repositorios:
            perguntas = repositorios.faq.todas()
        pontuadas = [(_pontuacao(item, palavras), item) for item in perguntas]
        relevantes = sorted((par for par in pontuadas if par[0] > 0), key=lambda par: -par[0])
        if not relevantes:
            raise NadaEncontrado("Não encontrei essa informação na FAQ. Ofereça transferir para um atendente.")
        return [{"pergunta": item["pergunta"], "resposta": item["resposta"]}
                for _, item in relevantes[:MAXIMO_DE_RESPOSTAS]]

    def transferir_para_humano(self, paciente_id: Optional[int], motivo: str) -> int:
        motivo = (motivo or "não informado")[:TAMANHO_MAXIMO_DO_MOTIVO]
        with self._abrir_transacao() as repositorios:
            protocolo = repositorios.atendimentos.abrir(paciente_id, motivo)
        self._notificador.notificar(Evento.ATENDENTE,
                                    {"protocolo": protocolo, "paciente_id": paciente_id, "motivo": motivo})
        return protocolo
