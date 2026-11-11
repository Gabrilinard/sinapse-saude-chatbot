import streamlit as st

ESTILO_DOS_CAMPOS = """
<style>
  [data-testid="InputInstructions"] { display: none; }

  [data-testid="stTextInputRootElement"],
  [data-testid="stNumberInputContainer"],
  [data-testid="stDateInputField"],
  [data-baseweb="select"] > div {
    min-height: 2.6rem;
    border-radius: 0.5rem;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }

  [data-testid="stTextInputRootElement"]:focus-within,
  [data-testid="stNumberInputContainer"]:focus-within {
    box-shadow: 0 0 0 2px rgba(43, 179, 192, 0.25);
  }

  input::placeholder { color: #6B7785 !important; opacity: 1; }

  [data-testid="stWidgetLabel"] p { font-size: 0.85rem; font-weight: 500; color: #AEB8C4; }

  [data-testid="stForm"] { padding: 1rem; border-radius: 0.75rem; }
  [data-testid="stForm"] [data-testid="stVerticalBlock"] { gap: 0.6rem; }
</style>
"""


def aplicar_estilo() -> None:
    st.html(ESTILO_DOS_CAMPOS)
