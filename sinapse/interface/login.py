from datetime import date

import streamlit as st

from sinapse.dominio.erros import AcessoBloqueado, CodigoExpirado, ErroDeAutenticacao
from sinapse.fabrica import criar_servicos
from sinapse.interface import icones
from sinapse.interface.cadastro import (DATA_MINIMA_DE_NASCIMENTO, formulario_cadastro_paciente,
                                        formulario_cadastro_profissional)
from sinapse.interface.estado import EstadoDaTela, EtapaDoLogin
from sinapse.interface.mascaras import TAMANHO_FORMATADO


def formulario_do_paciente(estado: EstadoDaTela) -> None:
    etapas = {
        EtapaDoLogin.CODIGO: _pedir_codigo,
        EtapaDoLogin.CADASTRO_PACIENTE: formulario_cadastro_paciente,
    }
    etapas.get(estado.etapa_do_login, _pedir_dados_pessoais)(estado)


def formulario_do_profissional(estado: EstadoDaTela) -> None:
    if estado.etapa_do_login == EtapaDoLogin.CADASTRO_PROFISSIONAL:
        formulario_cadastro_profissional(estado)
    else:
        _entrar_como_profissional(estado)


def _entrar_como_profissional(estado: EstadoDaTela) -> None:
    with st.form("login_profissional"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        enviou = st.form_submit_button("Entrar", icon=icones.ENTRAR, width="stretch")
    if st.button("Criar cadastro", icon=icones.CADASTRAR, width="stretch", key="cadastro_profissional"):
        estado.abrir_cadastro(EtapaDoLogin.CADASTRO_PROFISSIONAL)
        st.rerun()
    if not enviou:
        return
    try:
        estado.entrar(criar_servicos().autenticacao.autenticar_profissional(email, senha))
    except ErroDeAutenticacao:
        st.error("E-mail ou senha incorretos.", icon=icones.ERRO)
        return
    st.rerun()


def _pedir_dados_pessoais(estado: EstadoDaTela) -> None:
    with st.form("login_paciente"):
        cpf = st.text_input("CPF", placeholder="000.000.000-00", max_chars=TAMANHO_FORMATADO["CPF"])
        nascimento = st.date_input("Data de nascimento", value=None, format="DD/MM/YYYY",
                                   min_value=DATA_MINIMA_DE_NASCIMENTO, max_value=date.today())
        enviou = st.form_submit_button("Receber código", icon=icones.SMS, width="stretch")
    if st.button("Criar cadastro", icon=icones.CADASTRAR, width="stretch"):
        estado.abrir_cadastro(EtapaDoLogin.CADASTRO_PACIENTE)
        st.rerun()
    if not enviou:
        return
    try:
        estado.aguardar_codigo(criar_servicos().autenticacao.solicitar_codigo(cpf, nascimento))
    except ErroDeAutenticacao as erro:
        st.error(str(erro), icon=icones.ERRO)
        return
    st.rerun()


def _pedir_codigo(estado: EstadoDaTela) -> None:
    _mostrar_como_o_codigo_chegou(estado)
    with st.form("codigo_otp"):
        codigo = st.text_input("Código", max_chars=6)
        enviou = st.form_submit_button("Entrar", icon=icones.ENTRAR, width="stretch")
    if enviou:
        _verificar_codigo(estado, codigo)
    reenviar, voltar = st.columns(2)
    if reenviar.button("Reenviar código", width="stretch"):
        _reenviar_codigo(estado)
    if voltar.button("Voltar", width="stretch"):
        estado.voltar_para_dados()
        st.rerun()


def _mostrar_como_o_codigo_chegou(estado: EstadoDaTela) -> None:
    codigo_para_demo = estado.codigo_enviado.codigo_para_demo
    if codigo_para_demo:
        st.info(f"**SMS simulado** (demo): seu código é **{codigo_para_demo}**. Vale por 5 minutos.",
                icon=icones.SMS)
    else:
        st.info("Enviamos um código de 6 dígitos para o seu contato cadastrado. Vale por 5 minutos.", icon=icones.SMS)


def _verificar_codigo(estado: EstadoDaTela, codigo: str) -> None:
    try:
        estado.entrar(criar_servicos().autenticacao.verificar_codigo(estado.codigo_enviado.paciente_id, codigo))
    except AcessoBloqueado as erro:
        estado.voltar_para_dados()
        estado.avisar("error", str(erro))
    except CodigoExpirado as erro:
        st.error(f"{erro} Clique em “Reenviar código”.", icon=icones.ERRO)
        return
    except ErroDeAutenticacao as erro:
        st.error(str(erro), icon=icones.ERRO)
        return
    st.rerun()


def _reenviar_codigo(estado: EstadoDaTela) -> None:
    try:
        estado.aguardar_codigo(criar_servicos().autenticacao.reenviar_codigo(estado.codigo_enviado.paciente_id))
    except AcessoBloqueado as erro:
        estado.voltar_para_dados()
        estado.avisar("error", str(erro))
    st.rerun()
