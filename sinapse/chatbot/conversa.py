from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterator, Optional


class Papel(StrEnum):
    USUARIO = "usuario"
    MODELO = "modelo"
    FERRAMENTA = "ferramenta"


@dataclass(frozen=True)
class ChamadaDeFerramenta:
    nome: str
    argumentos: dict
    assinatura: Optional[object] = None


@dataclass(frozen=True)
class ResultadoDeFerramenta:
    nome: str
    conteudo: str


@dataclass(frozen=True)
class Mensagem:
    papel: Papel
    texto: str = ""
    chamadas: tuple[ChamadaDeFerramenta, ...] = ()
    resultados: tuple[ResultadoDeFerramenta, ...] = ()

    @classmethod
    def do_usuario(cls, texto: str) -> "Mensagem":
        return cls(Papel.USUARIO, texto)

    @classmethod
    def do_modelo(cls, texto: str) -> "Mensagem":
        return cls(Papel.MODELO, texto)

    @classmethod
    def com_resultados(cls, resultados: list[ResultadoDeFerramenta]) -> "Mensagem":
        return cls(Papel.FERRAMENTA, resultados=tuple(resultados))

    @property
    def visivel_ao_usuario(self) -> bool:
        return self.papel != Papel.FERRAMENTA and bool(self.texto) and not self.chamadas


@dataclass(frozen=True)
class AcaoPendente:
    nome: str
    argumentos: str
    turno: int


@dataclass
class Conversa:
    mensagens: list[Mensagem] = field(default_factory=list)
    acao_pendente: Optional[AcaoPendente] = None

    def adicionar(self, mensagem: Mensagem) -> None:
        self.mensagens.append(mensagem)

    @property
    def turno(self) -> int:
        return sum(1 for mensagem in self.mensagens if mensagem.papel == Papel.USUARIO)

    def ultima_fala_do_usuario(self) -> str:
        return next((m.texto for m in reversed(self.mensagens) if m.papel == Papel.USUARIO), "")

    def fala_do_modelo_antes_do_usuario(self) -> str:
        indice_do_usuario = max((i for i, m in enumerate(self.mensagens) if m.papel == Papel.USUARIO), default=0)
        anteriores = self.mensagens[:indice_do_usuario]
        return next((m.texto for m in reversed(anteriores) if m.papel == Papel.MODELO and m.texto), "")

    def mensagens_visiveis(self) -> list[Mensagem]:
        return [mensagem for mensagem in self.mensagens if mensagem.visivel_ao_usuario]

    @contextmanager
    def tentativa(self) -> Iterator[None]:
        tamanho_original = len(self.mensagens)
        try:
            yield
        except Exception:
            del self.mensagens[tamanho_original:]
            raise
