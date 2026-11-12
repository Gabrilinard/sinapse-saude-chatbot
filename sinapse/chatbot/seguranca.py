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
    "AGUARDANDO CONFIRMAÇÃO: a ação ainda NÃO foi executada. O sistema perguntou ao usuário se pode {descricao}. "
    "Se o usuário confirmar, o próprio sistema executa a ação."
)
PERGUNTA_DE_CONFIRMACAO = (
    "Antes de continuar, confirme: posso **{descricao}**?\n\n"
    "Responda **\"sim\"** para confirmar ou diga o que prefere mudar."
)

_SINAIS_DE_ALARME = re.compile("|".join([
    r"\bdor\b(?:\W+\w+){0,4}?\W+(?:no|do|na) peito",
    r"(?:aperto|pressao|queimacao|pontada)(?:\W+\w+){0,2}?\W+(?:no|do) peito", r"peito apertado",
    r"falta de ar", r"\bsem ar\b", r"nao consigo respirar", r"dificuldade (?:para|pra|de) respirar",
    r"respirando com dificuldade", r"sufocando",
    r"desmai", r"perd\w+ a consciencia", r"inconsciente", r"nao acorda",
    r"convuls", r"infart", r"\bavc\b", r"derrame",
    r"boca torta", r"rosto torto", r"fala enrolada", r"perd\w+ a forca",
    r"sangramento (?:intenso|forte|muito)", r"sangrando muito", r"sangue nao para", r"hemorragia",
]))

_INICIO_AFIRMATIVO = frozenset({"sim", "s", "pode", "confirmo", "confirma", "confirmar", "confirmado", "ok",
                                "okay", "isso", "claro", "certo", "beleza", "perfeito", "correto", "exato",
                                "fechado", "quero"})
_PALAVRAS_DE_CONFIRMACAO = _INICIO_AFIRMATIVO | frozenset({
    "mesmo", "com", "certeza", "por", "favor", "obrigado", "obrigada", "esta", "ta", "bom",
    "agendar", "marcar", "cancelar", "remarcar", "exatamente", "tudo", "ser", "assim", "e", "o", "a"})
_PALAVRAS_QUE_ANULAM = frozenset({"nao", "mas", "porem", "outro", "outra", "prefiro", "trocar",
                                  "mudar", "espera", "espere", "talvez", "depois", "primeiro", "primeira"})
_MAXIMO_DE_PALAVRAS = 8


def eh_confirmacao(texto: str) -> bool:
    palavras = re.findall(r"\w+", remover_acentos(texto or ""))
    return (0 < len(palavras) <= _MAXIMO_DE_PALAVRAS
            and palavras[0] in _INICIO_AFIRMATIVO
            and not any(p in _PALAVRAS_QUE_ANULAM for p in palavras)
            and all(p in _PALAVRAS_DE_CONFIRMACAO for p in palavras))


class DetectorDeEmergencia:
    def detectar(self, texto: str) -> bool:
        return bool(_SINAIS_DE_ALARME.search(remover_acentos(texto)))


class PoliticaDeConfirmacao:
    ACOES_QUE_EXIGEM_CONFIRMACAO = frozenset({"agendar_consulta", "remarcar_consulta", "cancelar_consulta"})

    def exige_confirmacao(self, nome: str) -> bool:
        return nome in self.ACOES_QUE_EXIGEM_CONFIRMACAO

    @staticmethod
    def registrar(conversa: Conversa, nome: str, argumentos: dict) -> None:
        conversa.acao_pendente = AcaoPendente(nome, json.dumps(argumentos, sort_keys=True), conversa.turno)

    @staticmethod
    def retomar(conversa: Conversa) -> AcaoPendente | None:
        pendente, conversa.acao_pendente = conversa.acao_pendente, None
        if (pendente is not None and pendente.turno == conversa.turno - 1
                and eh_confirmacao(conversa.ultima_fala_do_usuario())):
            return pendente
        return None
