import sys

import streamlit as st

from sinapse.chatbot.conversa import Papel
from sinapse.chatbot.instrucoes import TERMO_LGPD
from sinapse.chatbot.portas import LimiteDeUsoAtingido, ModeloIndisponivel
from sinapse.config import carregar_configuracao
from sinapse.fabrica import criar_assistente
from sinapse.interface import icones
from sinapse.interface.estado import EstadoDaTela, escapar_cifrao

ASSISTENTE_FORA_DO_AR = ("O assistente está indisponível no momento. Use a aba **Buscar sem chat** "
                         "para encontrar profissionais e horários.")
LIMITE_ATINGIDO = ("O limite de uso gratuito do Gemini foi atingido. Aguarde cerca de 1 minuto e tente "
                   "de novo, ou use a aba **Buscar sem chat**.")
CHAVE_AUSENTE = ("Chat desativado: preencha `GEMINI_API_KEY` no arquivo `.env` "
                 "(gere em aistudio.google.com/apikey) e reinicie o app.")
PAPEL_NA_TELA = {Papel.USUARIO: "user", Papel.MODELO: "assistant"}
AVATARES = {"user": icones.AVATAR_USUARIO, "assistant": icones.AVATAR_ASSISTENTE}


def renderizar_chat(estado: EstadoDaTela) -> None:
    if not carregar_configuracao().gemini.chave_api:
        st.warning(CHAVE_AUSENTE, icon=icones.ALERTA)
    area_das_mensagens = st.container()
    pergunta = st.chat_input("Digite sua mensagem…")
    with area_das_mensagens:
        _balao("assistant", TERMO_LGPD)
        for mensagem in estado.conversa.mensagens_visiveis():
            _balao(PAPEL_NA_TELA[mensagem.papel], mensagem.texto)
        if pergunta:
            _responder_na_tela(estado, pergunta)


def _responder_na_tela(estado: EstadoDaTela, pergunta: str) -> None:
    _balao("user", pergunta)
    with st.chat_message("assistant", avatar=icones.AVATAR_ASSISTENTE):
        with st.spinner("Pensando…"):
            resposta = _responder(estado, pergunta)
        st.markdown(escapar_cifrao(resposta))


def _balao(papel: str, texto: str) -> None:
    with st.chat_message(papel, avatar=AVATARES[papel]):
        st.markdown(escapar_cifrao(texto))


def _responder(estado: EstadoDaTela, pergunta: str) -> str:
    try:
        return criar_assistente().responder(estado.conversa, pergunta, estado.sessao)
    except LimiteDeUsoAtingido:
        return LIMITE_ATINGIDO
    except ModeloIndisponivel as erro:
        print(f"[chat] modelo indisponível: {erro}", file=sys.stderr)
        return ASSISTENTE_FORA_DO_AR
