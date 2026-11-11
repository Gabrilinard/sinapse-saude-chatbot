from typing import Optional

from sinapse.infraestrutura.banco import Executor

TAMANHO_MAXIMO_DETALHE = 1000


class RepositorioAuditoria:
    def __init__(self, executor: Executor):
        self._executor = executor

    def registrar(self, usuario_tipo: str, usuario_id: Optional[int], acao: str, detalhe: str = "") -> None:
        self._executor.executar(
            "INSERT INTO auditoria (usuario_tipo, usuario_id, acao, detalhe) VALUES (%s, %s, %s, %s)",
            (usuario_tipo, usuario_id, acao, detalhe[:TAMANHO_MAXIMO_DETALHE]),
        )

    def ultimas(self, limite: int) -> list[dict]:
        return self._executor.consultar(
            """SELECT id, usuario_tipo, usuario_id, acao, detalhe, data_hora
               FROM auditoria ORDER BY id DESC LIMIT %s""",
            (limite,),
        )
