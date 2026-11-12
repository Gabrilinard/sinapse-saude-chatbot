from typing import Optional

TAMANHO_DO_PREFIXO = 6


def comeca_com(texto: Optional[str]) -> Optional[str]:
    return f"{texto.strip()[:TAMANHO_DO_PREFIXO]}%" if texto else None


def contem(texto: Optional[str]) -> Optional[str]:
    return f"%{texto.strip()}%" if texto else None
