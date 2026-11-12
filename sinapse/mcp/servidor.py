import functools
from typing import Annotated, Any, Callable, Literal, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from sinapse.dominio.erros import ErroDeNegocio
from sinapse.dominio.formatacao import para_json
from sinapse.dominio.modelos import (CONVENIOS_ATENDIDOS, ESPECIALIDADES, CampoEditavel, FiltroProfissionais,
                                     Localizacao, Periodo, TipoRegistro)
from sinapse.fabrica import criar_servicos

PARAMETROS_DA_SESSAO = frozenset({"paciente_id", "profissional_id", "lat", "lng"})
PARAMETROS_SIGILOSOS = frozenset({"novo_valor"})
NOMES_DOS_CAMPOS = {"telefone": "Telefone", "email": "E-mail", "convenio": "Convênio"}

Especialidade = Annotated[Optional[str], Field(description=f"Especialidade. Valores: {', '.join(ESPECIALIDADES)}")]
DataInicio = Annotated[Optional[str], Field(description="Data inicial no formato AAAA-MM-DD (padrão: hoje)")]
DataFim = Annotated[Optional[str], Field(description="Data final no formato AAAA-MM-DD (padrão: daqui a 7 dias)")]
ConsultaId = Annotated[int, Field(description="consulta_id retornado por buscar_minhas_consultas")]
HorarioId = Annotated[int, Field(description="horario_id retornado por listar_disponiveis")]

mcp = FastMCP("sinapse", log_level="WARNING")
servicos = criar_servicos()


def _identificar_usuario(argumentos: dict) -> tuple[str, Optional[int]]:
    if argumentos.get("profissional_id"):
        return "profissional", argumentos["profissional_id"]
    if argumentos.get("paciente_id"):
        return "paciente", argumentos["paciente_id"]
    return "anonimo", None


def _descrever(argumentos: dict, situacao: str) -> str:
    visiveis = {chave: valor for chave, valor in argumentos.items()
                if chave not in PARAMETROS_DA_SESSAO | PARAMETROS_SIGILOSOS and valor is not None}
    if "lat" in argumentos:
        visiveis["com_localizacao"] = argumentos["lat"] is not None
    return f"{visiveis} resultado={situacao}"


def ferramenta(funcao: Callable[..., Any]):
    @functools.wraps(funcao)
    def executar(**argumentos) -> str:
        try:
            resultado, situacao = funcao(**argumentos), "ok"
        except ErroDeNegocio as erro:
            resultado, situacao = str(erro), type(erro).__name__
        servicos.auditoria.registrar(*_identificar_usuario(argumentos), funcao.__name__,
                                     _descrever(argumentos, situacao))
        return resultado if isinstance(resultado, str) else para_json(resultado)

    return mcp.tool(structured_output=False)(executar)


@ferramenta
def buscar_profissionais(
    especialidade: Especialidade = None,
    valor_max: Annotated[Optional[float], Field(description="Valor máximo da consulta em reais")] = None,
    convenio: Annotated[Optional[str], Field(description=f"Convênio: {', '.join(CONVENIOS_ATENDIDOS)}")] = None,
    raio_km: Annotated[Optional[float], Field(
        description="Distância máxima em km. Preencha SOMENTE se o usuário disser um limite de distância")] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    paciente_id: Optional[int] = None,
):
    """Busca profissionais de saúde por especialidade, valor máximo e convênio, ordenados do mais
    próximo para o mais distante. Retorna até 5 profissionais com valor, distância em km e o próximo
    horário livre. Use para pedidos como 'cardiologista até R$ 200 perto de mim'."""
    localizacao = Localizacao("", lat, lng) if lat is not None and lng is not None else None
    filtro = FiltroProfissionais(especialidade, valor_max, convenio, raio_km)
    profissionais = servicos.busca.buscar_profissionais(filtro, localizacao)
    if not profissionais:
        return "Nenhum profissional encontrado com esses filtros."
    aviso = None if localizacao else "Localização não informada: resultados ordenados por valor."
    return {"aviso": aviso, "profissionais": profissionais}


@ferramenta
def listar_disponiveis(
    especialidade: Especialidade = None,
    nome_do_profissional: Annotated[Optional[str], Field(
        description="Nome do profissional como o usuário falou, ex.: 'Dr. Felipe' ou 'Ana Carvalho'. "
                    "Prefira este campo quando o usuário citar o profissional pelo nome")] = None,
    profissional_id_escolhido: Annotated[Optional[int], Field(
        description="Campo 'id' de um profissional que buscar_profissionais JÁ retornou nesta conversa. "
                    "Nunca deduza ou invente este número")] = None,
    data_inicio: DataInicio = None,
    data_fim: DataFim = None,
    paciente_id: Optional[int] = None,
):
    """Lista os próximos horários livres por especialidade, por nome do profissional ou por profissional, em
    ordem de data. Retorna o horario_id de cada horário, usado em agendar_consulta e remarcar_consulta."""
    horarios = servicos.busca.horarios_livres(especialidade, profissional_id_escolhido, data_inicio, data_fim,
                                              nome_do_profissional=nome_do_profissional)
    return horarios or "Não há horários livres nesse período."


@ferramenta
def buscar_minhas_consultas(
    tipo: Annotated[Literal["consultas", "exames", "receitas", "todos"], Field(description="O que buscar")] = "consultas",
    periodo: Annotated[Literal["futuras", "passadas", "todas"], Field(description="Período das consultas")] = "futuras",
    paciente_id: Optional[int] = None,
):
    """Mostra as consultas, exames e/ou receitas do paciente logado. Cada consulta traz o consulta_id,
    usado para remarcar ou cancelar."""
    return servicos.paciente.registros(paciente_id, TipoRegistro(tipo), Periodo(periodo))


@ferramenta
def buscar_faq(
    termo: Annotated[str, Field(description="Palavras-chave da dúvida, ex.: 'unimed', 'documentos', 'cancelar'")],
    paciente_id: Optional[int] = None,
):
    """Responde dúvidas gerais sobre a clínica (convênios aceitos, documentos, horário de funcionamento,
    cancelamento, uso de dados). Não precisa de login."""
    return servicos.atendimento.responder_duvida(termo)


@ferramenta
def agendar_consulta(horario_id: HorarioId, paciente_id: Optional[int] = None):
    """Agenda uma consulta para o paciente logado no horário escolhido. Só chame depois que o paciente
    confirmar o dia, a hora e o profissional."""
    return {"mensagem": "Consulta agendada.", **servicos.agendamento.agendar(paciente_id, horario_id)}


@ferramenta
def remarcar_consulta(consulta_id: ConsultaId, novo_horario_id: HorarioId, paciente_id: Optional[int] = None):
    """Remarca uma consulta ativa do paciente logado para outro horário livre. Só chame depois que o
    paciente confirmar o novo horário."""
    return {"mensagem": "Consulta remarcada.",
            **servicos.agendamento.remarcar(paciente_id, consulta_id, novo_horario_id)}


@ferramenta
def cancelar_consulta(consulta_id: ConsultaId, paciente_id: Optional[int] = None):
    """Cancela uma consulta do paciente logado (o histórico é mantido). Só chame depois que o paciente
    confirmar o cancelamento."""
    servicos.agendamento.cancelar(paciente_id, consulta_id)
    return "Consulta cancelada."


@ferramenta
def descrever_acao(
    acao: Literal["agendar_consulta", "remarcar_consulta", "cancelar_consulta"],
    argumentos: dict,
    paciente_id: Optional[int] = None,
):
    """Uso interno do assistente (o modelo não recebe esta ferramenta): valida e descreve, com dados do banco,
    a ação que será confirmada pelo usuário, sem executá-la."""
    return {"descricao": servicos.agendamento.descrever(paciente_id, acao, argumentos)}


@ferramenta
def atualizar_dados(
    campo: Annotated[Literal["telefone", "email", "convenio"], Field(description="Campo a corrigir")],
    novo_valor: Annotated[str, Field(
        description=f"Novo valor. Para convênio: {', '.join(CONVENIOS_ATENDIDOS)} ou Particular")],
    paciente_id: Optional[int] = None,
):
    """Corrige telefone, e-mail ou convênio do paciente logado (LGPD, art. 18). CPF e data de
    nascimento não podem ser alterados pelo chat."""
    servicos.paciente.atualizar_cadastro(paciente_id, CampoEditavel(campo), novo_valor)
    return f"{NOMES_DOS_CAMPOS[campo]} atualizado com sucesso."


@ferramenta
def solicitar_exclusao(paciente_id: Optional[int] = None):
    """Registra o pedido do paciente logado para excluir seus dados (LGPD, art. 18). O pedido é
    analisado pela equipe; dados de saúde podem ter prazo legal de guarda."""
    return servicos.paciente.solicitar_exclusao(paciente_id)


@ferramenta
def transferir_atendente(
    motivo: Annotated[str, Field(description="Resumo curto do motivo da transferência")],
    paciente_id: Optional[int] = None,
):
    """Transfere a conversa para um atendente humano da recepção. Use quando o usuário pedir para falar
    com uma pessoa ou quando você não conseguir resolver."""
    protocolo = servicos.atendimento.transferir_para_humano(paciente_id, motivo)
    return {"mensagem": "Pedido enviado à recepção. Um atendente vai entrar em contato.", "protocolo": protocolo}


@ferramenta
def minha_agenda(data_inicio: DataInicio = None, data_fim: DataFim = None, profissional_id: Optional[int] = None):
    """Mostra a agenda do profissional logado no período, com nome do paciente, CPF mascarado,
    paciente_id e status da consulta."""
    return servicos.profissional.agenda(profissional_id, data_inicio, data_fim)


@ferramenta
def historico_paciente(
    paciente_alvo_id: Annotated[int, Field(description="paciente_id que aparece em minha_agenda")],
    profissional_id: Optional[int] = None,
):
    """Retorna o histórico (consultas, exames e receitas) de um paciente da agenda do profissional logado,
    para você resumir. Só funciona se o paciente tem ou já teve consulta com esse profissional."""
    return servicos.profissional.historico_do_paciente(profissional_id, paciente_alvo_id)


if __name__ == "__main__":
    mcp.run()
