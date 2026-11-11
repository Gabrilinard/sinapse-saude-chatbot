import streamlit as st
from mysql.connector import Error as ErroDoMySQL

from sinapse.config import carregar_configuracao
from sinapse.fabrica import criar_servicos
from sinapse.interface import icones
from sinapse.interface.aba_auditoria import renderizar_auditoria
from sinapse.interface.aba_busca import renderizar_busca
from sinapse.interface.aba_chat import renderizar_chat
from sinapse.interface.barra_lateral import renderizar_barra_lateral
from sinapse.interface.estado import obter_estado
from sinapse.interface.estilo import aplicar_estilo
from sinapse.interface.mascaras import ativar_mascaras


def renderizar() -> None:
    st.set_page_config(page_title="Sinapse Saúde", page_icon=icones.MARCA, layout="centered")
    aplicar_estilo()
    _garantir_banco_disponivel()
    estado = obter_estado()
    renderizar_barra_lateral(estado)

    st.title("Sinapse Saúde")
    st.caption("Atendimento e agendamento de consultas em Teresina")
    abas = {
        f"{icones.CHAT} Chat": lambda: renderizar_chat(estado),
        f"{icones.BUSCA} Buscar sem chat": lambda: renderizar_busca(estado),
    }
    if carregar_configuracao().modo_demo:
        abas[f"{icones.AUDITORIA} Auditoria"] = renderizar_auditoria
    for aba, desenhar in zip(st.tabs(list(abas)), abas.values()):
        with aba:
            desenhar()
    ativar_mascaras()


def _garantir_banco_disponivel() -> None:
    try:
        criar_servicos().banco.testar_conexao()
    except ErroDoMySQL as erro:
        st.error(f"Não foi possível conectar ao MySQL. Confira o .env e se o banco está rodando.\n\n`{erro}`",
                 icon=icones.ERRO)
        st.stop()
