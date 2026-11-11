from dataclasses import dataclass
from typing import AsyncContextManager, Callable, Protocol

from sinapse.chatbot.conversa import Mensagem


@dataclass(frozen=True)
class DefinicaoDeFerramenta:
    nome: str
    descricao: str
    parametros: dict


class ModeloIndisponivel(Exception):
    pass


class LimiteDeUsoAtingido(ModeloIndisponivel):
    pass


class ModeloDeLinguagem(Protocol):
    def gerar(self, instrucoes: str, historico: list[Mensagem],
              ferramentas: list[DefinicaoDeFerramenta]) -> Mensagem: ...


class ProvedorDeFerramentas(Protocol):
    async def listar(self) -> list[DefinicaoDeFerramenta]: ...

    async def executar(self, nome: str, argumentos: dict) -> str: ...


ConectarFerramentas = Callable[[], AsyncContextManager[ProvedorDeFerramentas]]
