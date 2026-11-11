import streamlit as st

from sinapse.fabrica import criar_servicos
from sinapse.interface import icones

REGISTROS_EXIBIDOS = 50


def renderizar_auditoria() -> None:
    st.caption("Visível só com DEMO_MODE=1, para a apresentação.")
    if st.button("Atualizar", icon=icones.ATUALIZAR):
        st.rerun()
    st.dataframe(criar_servicos().auditoria.ultimos_registros(REGISTROS_EXIBIDOS), width="stretch", hide_index=True)
