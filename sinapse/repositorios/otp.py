from typing import Optional

from sinapse.infraestrutura.banco import Executor

VALIDADE_MINUTOS = 5
BLOQUEIO_MINUTOS = 15


class RepositorioOtp:
    def __init__(self, executor: Executor):
        self._executor = executor

    def estado(self, paciente_id: int) -> Optional[dict]:
        return self._executor.consultar_um(
            """SELECT codigo_hash, tentativas,
                      (expira_em IS NULL OR expira_em < NOW())                AS expirado,
                      (bloqueado_ate IS NOT NULL AND bloqueado_ate > NOW())   AS bloqueado,
                      CEIL(TIMESTAMPDIFF(SECOND, NOW(), bloqueado_ate) / 60)  AS minutos_bloqueio
               FROM otp WHERE paciente_id = %s FOR UPDATE""",
            (paciente_id,),
        )

    def salvar(self, paciente_id: int, codigo_hash: str) -> None:
        self._executor.executar(
            f"""INSERT INTO otp (paciente_id, codigo_hash, expira_em, tentativas)
                VALUES (%s, %s, NOW() + INTERVAL {VALIDADE_MINUTOS} MINUTE, 0)
                ON DUPLICATE KEY UPDATE codigo_hash = VALUES(codigo_hash),
                                        expira_em   = VALUES(expira_em),
                                        tentativas  = 0""",
            (paciente_id, codigo_hash),
        )

    def registrar_tentativa(self, paciente_id: int, tentativas: int) -> None:
        self._executor.executar("UPDATE otp SET tentativas = %s WHERE paciente_id = %s", (tentativas, paciente_id))

    def bloquear(self, paciente_id: int) -> None:
        self._executor.executar(
            f"""UPDATE otp SET tentativas = 0, codigo_hash = NULL, expira_em = NULL,
                               bloqueado_ate = NOW() + INTERVAL {BLOQUEIO_MINUTOS} MINUTE
                WHERE paciente_id = %s""",
            (paciente_id,),
        )

    def consumir(self, paciente_id: int) -> None:
        self._executor.executar(
            """UPDATE otp SET codigo_hash = NULL, expira_em = NULL, tentativas = 0, bloqueado_ate = NULL
               WHERE paciente_id = %s""",
            (paciente_id,),
        )
