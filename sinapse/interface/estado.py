from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional

import streamlit as st

from sinapse.chatbot.conversa import Conversa
from sinapse.dominio.modelos import CodigoEnviado, SessaoUsuario, UsuarioAutenticado

CHAVE_DO_ESTADO = "estado_da_tela"


class EtapaDoLogin(StrEnum):
    DADOS = "dados"
    CODIGO = "codigo"
    CADASTRO_PACIENTE = "cadastro_paciente"
    CADASTRO_PROFISSIONAL = "cadastro_profissional"


@dataclass
class Aviso:
    tipo: str
    texto: str


@dataclass
class EstadoDaTela:
    sessao: SessaoUsuario = field(default_factory=SessaoUsuario)
    conversa: Conversa = field(default_factory=Conversa)
    etapa_do_login: EtapaDoLogin = EtapaDoLogin.DADOS
    codigo_enviado: Optional[CodigoEnviado] = None
    resultado_da_busca: Optional[list[dict]] = None
    aviso: Optional[Aviso] = None

    def reiniciar_conversa(self) -> None:
        self.conversa = Conversa()

    def aguardar_codigo(self, codigo: CodigoEnviado) -> None:
        self.codigo_enviado = codigo
        self.etapa_do_login = EtapaDoLogin.CODIGO

    def abrir_cadastro(self, etapa: EtapaDoLogin) -> None:
        self.etapa_do_login = etapa

    def voltar_para_dados(self) -> None:
        self.codigo_enviado = None
        self.etapa_do_login = EtapaDoLogin.DADOS

    def entrar(self, usuario: UsuarioAutenticado) -> None:
        self.sessao.autenticar(usuario.perfil, usuario.usuario_id, usuario.nome)
        self.voltar_para_dados()
        self.reiniciar_conversa()

    def sair(self) -> None:
        self.sessao.encerrar()
        self.resultado_da_busca = None
        self.reiniciar_conversa()

    def avisar(self, tipo: str, texto: str) -> None:
        self.aviso = Aviso(tipo, texto)

    def consumir_aviso(self) -> Optional[Aviso]:
        aviso, self.aviso = self.aviso, None
        return aviso


def obter_estado() -> EstadoDaTela:
    if CHAVE_DO_ESTADO not in st.session_state:
        st.session_state[CHAVE_DO_ESTADO] = EstadoDaTela()
    return st.session_state[CHAVE_DO_ESTADO]


def escapar_cifrao(texto: str) -> str:
    """Evita que o Streamlit leia 'R$ 100 ... R$ 200' como fórmula LaTeX."""
    return texto.replace("$", "\\$")
