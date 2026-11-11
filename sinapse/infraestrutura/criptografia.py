import bcrypt


def gerar_hash(texto: str) -> str:
    return bcrypt.hashpw(texto.encode(), bcrypt.gensalt()).decode()


def confere_com_hash(texto: str, hash_salvo: str) -> bool:
    return bcrypt.checkpw(texto.encode(), hash_salvo.encode())
