import json
import re

from sinapse.chatbot.conversa import AcaoPendente, Conversa
from sinapse.dominio.formatacao import remover_acentos

RESPOSTA_DE_EMERGENCIA = (
    "**Atenção: isso pode ser uma emergência.** Ligue agora para o **SAMU (192)** ou vá ao pronto-socorro "
    "mais próximo. Não espere por uma consulta agendada.\n\n"
    "Eu não consigo avaliar sintomas, mas posso ajudar com agendamentos depois que você estiver seguro(a)."
)

AGUARDANDO_CONFIRMACAO = (
    "AGUARDANDO CONFIRMAÇÃO: a ação ainda NÃO foi executada. Descreva ao usuário exatamente o que será "
    "feito (profissional, dia e hora) e pergunte se pode confirmar. Quando ele responder que sim, chame "
    "esta mesma ferramenta de novo com os mesmos parâmetros."
)

_SINAIS_DE_ALARME = re.compile("|".join([
    r"dor (forte )?no peito", r"aperto no peito", r"falta de ar", r"nao consigo respirar", r"desmai",
    r"sangramento (intenso|forte|muito)", r"sangrando muito", r"convuls", r"infarto", r"\bavc\b",
    r"perdi a forca", r"boca torta",
]))

_RESPOSTA_AFIRMATIVA = re.compile(
    r"^\s*(sim|s|pode|confirmo|confirma|confirmar|ok|okay|isso|claro|certo|beleza|quero|perfeito|correto)\b")


class DetectorDeEmergencia:
    def detectar(self, texto: str) -> bool:
        return bool(_SINAIS_DE_ALARME.search(remover_acentos(texto)))


class PoliticaDeConfirmacao:
    """Garante no código que agendar, remarcar e cancelar só rodam depois de um "sim" do usuário."""

    ACOES_QUE_EXIGEM_CONFIRMACAO = frozenset({"agendar_consulta", "remarcar_consulta", "cancelar_consulta"})

    def autorizar(self, conversa: Conversa, nome: str, argumentos: dict) -> bool:
        if nome not in self.ACOES_QUE_EXIGEM_CONFIRMACAO:
            return True
        acao = AcaoPendente(nome, json.dumps(argumentos, sort_keys=True), conversa.turno)
        if self._usuario_acabou_de_confirmar(conversa) or self._repetiu_acao_pendente(conversa, acao):
            conversa.acao_pendente = None
            return True
        conversa.acao_pendente = acao
        return False

    @staticmethod
    def _usuario_acabou_de_confirmar(conversa: Conversa) -> bool:
        pergunta_anterior = conversa.fala_do_modelo_antes_do_usuario()
        resposta = remover_acentos(conversa.ultima_fala_do_usuario())
        return "?" in pergunta_anterior and bool(_RESPOSTA_AFIRMATIVA.match(resposta))

    @staticmethod
    def _repetiu_acao_pendente(conversa: Conversa, acao: AcaoPendente) -> bool:
        pendente = conversa.acao_pendente
        return (pendente is not None and pendente.nome == acao.nome
                and pendente.argumentos == acao.argumentos and pendente.turno < acao.turno)
