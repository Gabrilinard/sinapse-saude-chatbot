import streamlit as st

from sinapse.dominio.localidades import BAIRROS_DE_TERESINA, localizacao_do_bairro
from sinapse.dominio.modelos import Perfil
from sinapse.fabrica import criar_servicos
from sinapse.interface import icones, login
from sinapse.interface.estado import EstadoDaTela

SEM_LOCALIZACAO = "Não informar"
NOME_DO_PERFIL = {Perfil.PACIENTE: "Paciente", Perfil.PROFISSIONAL: "Profissional"}


def renderizar_barra_lateral(estado: EstadoDaTela) -> None:
    with st.sidebar:
        st.title(f"{icones.MARCA} Sinapse Saúde")
        _seletor_de_localizacao(estado)
        st.divider()
        _mostrar_aviso(estado)
        if estado.sessao.perfil == Perfil.VISITANTE:
            _area_de_login(estado)
        else:
            _usuario_conectado(estado)
        st.divider()
        if st.button("Nova conversa", icon=icones.NOVA_CONVERSA, width="stretch"):
            estado.reiniciar_conversa()
            st.rerun()


def _seletor_de_localizacao(estado: EstadoDaTela) -> None:
    st.subheader(f"{icones.LOCALIZACAO} Localização")
    opcoes = [SEM_LOCALIZACAO, *BAIRROS_DE_TERESINA]
    atual = estado.sessao.localizacao.bairro if estado.sessao.localizacao else SEM_LOCALIZACAO
    bairro = st.selectbox("Seu bairro em Teresina", opcoes, index=opcoes.index(atual))
    st.caption("Usada **apenas** para ordenar os profissionais por distância.")
    estado.sessao.localizacao = (None if bairro == SEM_LOCALIZACAO
                                 else localizacao_do_bairro(bairro))


def _mostrar_aviso(estado: EstadoDaTela) -> None:
    aviso = estado.consumir_aviso()
    if aviso:
        getattr(st, aviso.tipo)(aviso.texto, icon=icones.ERRO)


def _area_de_login(estado: EstadoDaTela) -> None:
    st.subheader(f"{icones.ENTRAR} Entrar")
    perfil = st.radio("Perfil", ["Paciente", "Profissional"], horizontal=True, label_visibility="collapsed")
    if perfil == "Paciente":
        login.formulario_do_paciente(estado)
    else:
        login.formulario_do_profissional(estado)
    st.caption("Sem login você pode buscar profissionais, ver horários e tirar dúvidas.")


def _usuario_conectado(estado: EstadoDaTela) -> None:
    sessao = estado.sessao
    st.success(f"{NOME_DO_PERFIL[sessao.perfil]}: **{sessao.nome}**", icon=icones.USUARIO_CONECTADO)
    if st.button("Sair", icon=icones.SAIR, width="stretch"):
        criar_servicos().auditoria.registrar(sessao.perfil.value, sessao.usuario_id, "logout")
        estado.sair()
        st.rerun()
