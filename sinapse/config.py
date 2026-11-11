import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent

load_dotenv(RAIZ_DO_PROJETO / ".env")

MODELO_PADRAO = "gemini-3.6-flash"
MODELOS_RESERVA_PADRAO = "gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite"


@dataclass(frozen=True)
class ConfiguracaoBanco:
    host: str
    porta: int
    usuario: str
    senha: str
    nome: str


@dataclass(frozen=True)
class ConfiguracaoGemini:
    chave_api: str
    modelo: str
    modelos_reserva: tuple[str, ...]
    temperatura: float

    @property
    def modelos_em_ordem(self) -> tuple[str, ...]:
        return (self.modelo, *self.modelos_reserva)


@dataclass(frozen=True)
class Configuracao:
    banco: ConfiguracaoBanco
    gemini: ConfiguracaoGemini
    webhooks_n8n: dict[str, str]
    modo_demo: bool


def _lista(texto: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in texto.split(",") if item.strip())


@lru_cache(maxsize=1)
def carregar_configuracao() -> Configuracao:
    return Configuracao(
        banco=ConfiguracaoBanco(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            porta=int(os.getenv("DB_PORT", "3306")),
            usuario=os.getenv("DB_USER", "sinapse_app"),
            senha=os.getenv("DB_PASSWORD", ""),
            nome=os.getenv("DB_NAME", "sinapse"),
        ),
        gemini=ConfiguracaoGemini(
            chave_api=os.getenv("GEMINI_API_KEY", ""),
            modelo=os.getenv("GEMINI_MODEL", MODELO_PADRAO),
            modelos_reserva=_lista(os.getenv("GEMINI_MODELOS_RESERVA", MODELOS_RESERVA_PADRAO)),
            temperatura=float(os.getenv("GEMINI_TEMPERATURE", "0.2")),
        ),
        webhooks_n8n={
            "lembrete": os.getenv("N8N_WEBHOOK_LEMBRETE", "").strip(),
            "otp": os.getenv("N8N_WEBHOOK_OTP", "").strip(),
            "atendente": os.getenv("N8N_WEBHOOK_ATENDENTE", "").strip(),
        },
        modo_demo=os.getenv("DEMO_MODE", "0") == "1",
    )
