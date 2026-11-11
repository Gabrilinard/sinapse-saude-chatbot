from datetime import date

import streamlit as st

from sinapse.dominio.erros import ErroDeNegocio
from sinapse.dominio.localidades import BAIRROS_DE_TERESINA, UF_PADRAO, UFS, localizacao_do_bairro
from sinapse.dominio.modelos import CONVENIOS_ATENDIDOS, PROFISSOES, NovoPaciente, NovoProfissional
from sinapse.dominio.validacao import TAMANHO_MINIMO_DA_SENHA, VALOR_MAXIMO_DA_CONSULTA, VALOR_MINIMO_DA_CONSULTA
from sinapse.fabrica import criar_servicos
from sinapse.interface import icones
from sinapse.interface.estado import EstadoDaTela
from sinapse.interface.mascaras import TAMANHO_FORMATADO

DATA_MINIMA_DE_NASCIMENTO = date(1900, 1, 1)
SEM_CONVENIO = "Particular (sem convênio)"
VALOR_SUGERIDO_DA_CONSULTA = 150.0
PROFISSOES_POR_NOME = {profissao.nome: profissao for profissao in PROFISSOES}
TERMO_DO_PACIENTE = "Li e aceito que meus dados sejam usados apenas para atendimento e agendamento (LGPD, art. 6º)."


def formulario_cadastro_paciente(estado: EstadoDaTela) -> None:
    st.markdown("**Cadastro de paciente**")
    with st.form("cadastro_paciente"):
        nome = st.text_input("Nome completo")
        cpf = st.text_input("CPF", placeholder="000.000.000-00", max_chars=TAMANHO_FORMATADO["CPF"])
        nascimento = st.date_input("Data de nascimento", value=None, format="DD/MM/YYYY",
                                   min_value=DATA_MINIMA_DE_NASCIMENTO, max_value=date.today())
        telefone = st.text_input("Telefone com DDD", placeholder="(86) 99999-9999",
                                 max_chars=TAMANHO_FORMATADO["Telefone com DDD"])
        email = st.text_input("E-mail")
        convenio = st.selectbox("Convênio", [SEM_CONVENIO, *CONVENIOS_ATENDIDOS])
        aceitou = st.checkbox(TERMO_DO_PACIENTE)
        enviou = st.form_submit_button("Cadastrar", icon=icones.CADASTRAR, width="stretch")
    _botao_ja_tenho_cadastro(estado)
    if enviou:
        novo_paciente = NovoPaciente(nome, cpf, nascimento, telefone, email,
                                     None if convenio == SEM_CONVENIO else convenio, aceitou)
        _concluir(estado, lambda: criar_servicos().cadastro.cadastrar_paciente(novo_paciente))


def formulario_cadastro_profissional(estado: EstadoDaTela) -> None:
    st.markdown("**Cadastro de profissional**")
    profissao = PROFISSOES_POR_NOME[st.selectbox("Profissão", list(PROFISSOES_POR_NOME))]
    with st.form("cadastro_profissional"):
        nome = st.text_input("Nome completo")
        especialidade = st.selectbox("Especialidade", profissao.especialidades,
                                     disabled=len(profissao.especialidades) == 1)
        coluna_numero, coluna_uf = st.columns([2, 1])
        numero = coluna_numero.text_input(f"Número do {profissao.conselho}", placeholder="12345",
                                          max_chars=TAMANHO_FORMATADO["Número do"])
        uf = coluna_uf.selectbox("UF", UFS, index=UFS.index(UF_PADRAO))
        valor = st.number_input("Valor da consulta (R$)", min_value=float(VALOR_MINIMO_DA_CONSULTA),
                                max_value=float(VALOR_MAXIMO_DA_CONSULTA), value=VALOR_SUGERIDO_DA_CONSULTA, step=10.0)
        endereco = st.text_input("Endereço do consultório", placeholder="Rua, número")
        bairro = st.selectbox("Bairro", list(BAIRROS_DE_TERESINA))
        convenios = st.multiselect("Convênios aceitos", CONVENIOS_ATENDIDOS, placeholder="Apenas particular")
        email = st.text_input("E-mail (usado no login)")
        senha = st.text_input(f"Senha (mínimo {TAMANHO_MINIMO_DA_SENHA} caracteres)", type="password")
        confirmacao = st.text_input("Confirme a senha", type="password")
        enviou = st.form_submit_button("Cadastrar", icon=icones.CADASTRAR, width="stretch")
    _botao_ja_tenho_cadastro(estado)
    if enviou:
        novo_profissional = NovoProfissional(
            nome=nome, profissao=profissao, especialidade=especialidade, numero_do_registro=numero,
            uf_do_registro=uf, valor_consulta=valor, endereco=endereco, localizacao=localizacao_do_bairro(bairro),
            convenios=tuple(convenios), email=email, senha=senha, confirmacao_da_senha=confirmacao,
        )
        _concluir(estado, lambda: criar_servicos().cadastro.cadastrar_profissional(novo_profissional))


def _botao_ja_tenho_cadastro(estado: EstadoDaTela) -> None:
    if st.button("Já tenho cadastro", icon=icones.ENTRAR, width="stretch"):
        estado.voltar_para_dados()
        st.rerun()


def _concluir(estado: EstadoDaTela, cadastrar) -> None:
    try:
        estado.entrar(cadastrar())
    except ErroDeNegocio as erro:
        st.error(str(erro), icon=icones.ERRO)
        return
    st.rerun()
