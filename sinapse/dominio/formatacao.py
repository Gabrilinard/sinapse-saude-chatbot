import json
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

DIAS_DA_SEMANA = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


def somente_digitos(texto: Optional[str]) -> str:
    return re.sub(r"\D", "", texto or "")


def mascarar_cpf(cpf: str) -> str:
    digitos = somente_digitos(cpf)
    if len(digitos) != 11:
        return "***"
    return f"***.{digitos[3:6]}.{digitos[6:9]}-**"


def remover_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def formatar_data_hora(momento: datetime) -> str:
    return f"{DIAS_DA_SEMANA[momento.weekday()]}, {momento:%d/%m/%Y} às {momento:%H:%M}"


def interpretar_data(texto: Optional[str]) -> Optional[date]:
    if not texto:
        return None
    try:
        return datetime.strptime(texto.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _para_tipo_simples(valor: Any) -> Any:
    if isinstance(valor, list):
        return [_para_tipo_simples(v) for v in valor]
    if isinstance(valor, dict):
        return {chave: _para_tipo_simples(v) for chave, v in valor.items()}
    if isinstance(valor, datetime):
        return formatar_data_hora(valor)
    if isinstance(valor, date):
        return f"{valor:%d/%m/%Y}"
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def para_json(dados: Any) -> str:
    return json.dumps(_para_tipo_simples(dados), ensure_ascii=False)
