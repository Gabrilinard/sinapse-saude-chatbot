"""Plano B (Quadro 10): busca por filtros que funciona mesmo com o LLM fora do ar."""
import streamlit as st

from sinapse.dominio.erros import ErroDeNegocio
from sinapse.dominio.formatacao import formatar_data_hora
from sinapse.dominio.modelos import CONVENIOS_ATENDIDOS, FiltroProfissionais, Perfil
from sinapse.fabrica import criar_servicos
from sinapse.interface import icones
from sinapse.interface.estado import EstadoDaTela, escapar_cifrao

TODAS = "Todas"
QUALQUER_CONVENIO = "Qualquer / particular"
VALOR_MINIMO, VALOR_MAXIMO, PASSO_DO_VALOR = 50, 400, 10
HORARIOS_POR_PROFISSIONAL = 6


def renderizar_busca(estado: EstadoDaTela) -> None:
    st.caption("Funciona mesmo se o assistente estiver fora do ar.")
    filtro = _formulario_de_filtros()
    if filtro:
        _buscar(estado, filtro)
    _mostrar_resultados(estado)


def _formulario_de_filtros() -> FiltroProfissionais | None:
    with st.form("filtros"):
        coluna_especialidade, coluna_convenio = st.columns(2)
        especialidade = coluna_especialidade.selectbox("Especialidade", [TODAS, *criar_servicos().busca.especialidades()])
        convenio = coluna_convenio.selectbox("Convênio", [QUALQUER_CONVENIO, *CONVENIOS_ATENDIDOS])
        valor_max = st.slider("Valor máximo (R$)", VALOR_MINIMO, VALOR_MAXIMO, VALOR_MAXIMO, step=PASSO_DO_VALOR)
        enviou = st.form_submit_button("Buscar", icon=icones.BUSCA, width="stretch")
    if not enviou:
        return None
    return FiltroProfissionais(
        especialidade=None if especialidade == TODAS else especialidade,
        valor_max=valor_max,
        convenio=None if convenio == QUALQUER_CONVENIO else convenio,
    )


def _buscar(estado: EstadoDaTela, filtro: FiltroProfissionais) -> None:
    servicos = criar_servicos()
    estado.resultado_da_busca = servicos.busca.buscar_profissionais(filtro, estado.sessao.localizacao)
    usuario_tipo = estado.sessao.perfil.value if estado.sessao.usuario_id else "anonimo"
    servicos.auditoria.registrar(usuario_tipo, estado.sessao.usuario_id, "plano_b_busca",
                                 f"{filtro} resultados={len(estado.resultado_da_busca)}")


def _mostrar_resultados(estado: EstadoDaTela) -> None:
    if estado.resultado_da_busca is None:
        return
    if not estado.resultado_da_busca:
        st.warning("Nenhum profissional encontrado com esses filtros.", icon=icones.ALERTA)
        return
    if estado.sessao.localizacao is None:
        st.info("Escolha seu bairro na barra lateral para ordenar por distância.", icon=icones.LOCALIZACAO)
    for profissional in estado.resultado_da_busca:
        with st.container(border=True):
            _cartao_do_profissional(profissional)
            _horarios_do_profissional(estado, profissional)


def _cartao_do_profissional(profissional: dict) -> None:
    distancia = (f" · {icones.DISTANCIA} {profissional['distancia_km']} km"
                 if profissional["distancia_km"] is not None else "")
    st.markdown(f"**{profissional['nome']}** · {profissional['especialidade']}")
    st.markdown(escapar_cifrao(
        f"{icones.VALOR} R$ {profissional['valor_consulta']:.2f}{distancia}  \n"
        f"{icones.ENDERECO} {profissional['endereco']}  \n"
        f"{icones.CONVENIOS} {', '.join(profissional['convenios'])}"
    ))


def _horarios_do_profissional(estado: EstadoDaTela, profissional: dict) -> None:
    horarios = criar_servicos().busca.horarios_livres(profissional_id=profissional["id"],
                                                      limite=HORARIOS_POR_PROFISSIONAL)
    if not horarios:
        st.caption("Sem horários livres nos próximos 7 dias.")
        return
    opcoes = {h["horario_id"]: formatar_data_hora(h["data_hora"]) for h in horarios}
    if estado.sessao.perfil == Perfil.PACIENTE:
        _agendar_pela_busca(estado, profissional, opcoes)
    else:
        st.caption(f"{icones.HORARIOS} Próximos horários: " + " · ".join(list(opcoes.values())[:3]))


def _agendar_pela_busca(estado: EstadoDaTela, profissional: dict, opcoes: dict[int, str]) -> None:
    chave = profissional["id"]
    horario_id = st.selectbox("Horário", list(opcoes), format_func=opcoes.get, key=f"horario_{chave}")
    confirmou = st.checkbox(f"Confirmo o agendamento com {profissional['nome']}", key=f"confirmo_{chave}")
    if not st.button("Agendar", icon=icones.AGENDAR, key=f"agendar_{chave}", disabled=not confirmou):
        return
    paciente_id = estado.sessao.paciente_id
    servicos = criar_servicos()
    try:
        agendamento = servicos.agendamento.agendar(paciente_id, horario_id)
        situacao = "ok"
        st.success(f"Consulta agendada: {formatar_data_hora(agendamento['data_hora'])} "
                   f"com {agendamento['profissional']}.", icon=icones.SUCESSO)
    except ErroDeNegocio as erro:
        situacao = type(erro).__name__
        st.error(str(erro), icon=icones.ERRO)
    servicos.auditoria.registrar("paciente", paciente_id, "plano_b_agendar",
                                 f"horario_id={horario_id} resultado={situacao}")
