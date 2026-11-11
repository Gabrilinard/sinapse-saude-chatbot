from dataclasses import dataclass
from functools import lru_cache

from sinapse.chatbot.assistente import Assistente
from sinapse.chatbot.cliente_mcp import ClienteMCP
from sinapse.chatbot.gemini import ModeloGemini
from sinapse.config import carregar_configuracao
from sinapse.infraestrutura.banco import BancoDeDados
from sinapse.infraestrutura.notificador import NotificadorN8n
from sinapse.repositorios import UnidadeDeTrabalho
from sinapse.servicos.agendamento import ServicoDeAgendamento
from sinapse.servicos.atendimento import ServicoDeAtendimento
from sinapse.servicos.auditoria import ServicoDeAuditoria
from sinapse.servicos.autenticacao import ServicoDeAutenticacao
from sinapse.servicos.busca import ServicoDeBusca
from sinapse.servicos.cadastro import ServicoDeCadastro
from sinapse.servicos.paciente import ServicoDoPaciente
from sinapse.servicos.profissional import ServicoDoProfissional


@dataclass(frozen=True)
class Servicos:
    banco: BancoDeDados
    busca: ServicoDeBusca
    agendamento: ServicoDeAgendamento
    paciente: ServicoDoPaciente
    profissional: ServicoDoProfissional
    atendimento: ServicoDeAtendimento
    autenticacao: ServicoDeAutenticacao
    cadastro: ServicoDeCadastro
    auditoria: ServicoDeAuditoria


@lru_cache(maxsize=1)
def criar_servicos() -> Servicos:
    configuracao = carregar_configuracao()
    banco = BancoDeDados(configuracao.banco)
    abrir_transacao = UnidadeDeTrabalho(banco)
    notificador = NotificadorN8n(configuracao.webhooks_n8n)
    return Servicos(
        banco=banco,
        busca=ServicoDeBusca(abrir_transacao),
        agendamento=ServicoDeAgendamento(abrir_transacao, notificador),
        paciente=ServicoDoPaciente(abrir_transacao),
        profissional=ServicoDoProfissional(abrir_transacao),
        atendimento=ServicoDeAtendimento(abrir_transacao, notificador),
        autenticacao=ServicoDeAutenticacao(abrir_transacao, notificador),
        cadastro=ServicoDeCadastro(abrir_transacao),
        auditoria=ServicoDeAuditoria(abrir_transacao),
    )


def criar_assistente() -> Assistente:
    return Assistente(ModeloGemini(carregar_configuracao().gemini), ClienteMCP)
