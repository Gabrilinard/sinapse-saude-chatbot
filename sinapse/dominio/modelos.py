from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Optional

CONVENIOS_ATENDIDOS = ("Unimed", "Hapvida", "Bradesco Saúde", "SulAmérica")
STATUS_ATIVOS = ("agendada", "remarcada")


@dataclass(frozen=True)
class Profissao:
    nome: str
    conselho: str
    especialidades: tuple[str, ...]


PROFISSOES = (
    Profissao("Médico", "CRM", ("Cardiologia", "Dermatologia", "Clínica Geral", "Pediatria",
                                "Ortopedia", "Ginecologia", "Psiquiatria", "Oftalmologia")),
    Profissao("Dentista", "CRO", ("Odontologia",)),
    Profissao("Fisioterapeuta", "CREFITO", ("Fisioterapia",)),
    Profissao("Nutricionista", "CRN", ("Nutrição",)),
    Profissao("Fonoaudiólogo", "CRFa", ("Fonoaudiologia",)),
)
ESPECIALIDADES = tuple(especialidade for profissao in PROFISSOES for especialidade in profissao.especialidades)


class Perfil(StrEnum):
    VISITANTE = "visitante"
    PACIENTE = "paciente"
    PROFISSIONAL = "profissional"


class TipoRegistro(StrEnum):
    CONSULTAS = "consultas"
    EXAMES = "exames"
    RECEITAS = "receitas"
    TODOS = "todos"


class Periodo(StrEnum):
    FUTURAS = "futuras"
    PASSADAS = "passadas"
    TODAS = "todas"


class CampoEditavel(StrEnum):
    TELEFONE = "telefone"
    EMAIL = "email"
    CONVENIO = "convenio"


@dataclass(frozen=True)
class Localizacao:
    bairro: str
    lat: float
    lng: float


@dataclass(frozen=True)
class FiltroProfissionais:
    especialidade: Optional[str] = None
    valor_max: Optional[float] = None
    convenio: Optional[str] = None
    raio_km: Optional[float] = None


@dataclass
class SessaoUsuario:
    perfil: Perfil = Perfil.VISITANTE
    usuario_id: Optional[int] = None
    nome: str = ""
    localizacao: Optional[Localizacao] = None

    @property
    def paciente_id(self) -> Optional[int]:
        return self.usuario_id if self.perfil == Perfil.PACIENTE else None

    @property
    def profissional_id(self) -> Optional[int]:
        return self.usuario_id if self.perfil == Perfil.PROFISSIONAL else None

    def autenticar(self, perfil: Perfil, usuario_id: int, nome: str) -> None:
        self.perfil, self.usuario_id, self.nome = perfil, usuario_id, nome

    def encerrar(self) -> None:
        self.perfil, self.usuario_id, self.nome = Perfil.VISITANTE, None, ""


@dataclass(frozen=True)
class NovoPaciente:
    nome: str
    cpf: str
    nascimento: Optional[date]
    telefone: str
    email: str
    convenio: Optional[str]
    aceitou_termo_lgpd: bool


@dataclass(frozen=True)
class NovoProfissional:
    nome: str
    profissao: Profissao
    especialidade: str
    numero_do_registro: str
    uf_do_registro: str
    valor_consulta: float
    endereco: str
    localizacao: Optional[Localizacao]
    convenios: tuple[str, ...]
    email: str
    senha: str
    confirmacao_da_senha: str

    @property
    def conselho(self) -> str:
        return f"{self.profissao.conselho}-{self.uf_do_registro} {self.numero_do_registro}"


@dataclass(frozen=True)
class CodigoEnviado:
    paciente_id: int
    nome: str
    codigo_para_demo: Optional[str]


@dataclass(frozen=True)
class UsuarioAutenticado:
    perfil: Perfil
    usuario_id: int
    nome: str
