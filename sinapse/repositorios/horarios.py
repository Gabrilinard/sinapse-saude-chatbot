from datetime import date
from typing import Optional

from sinapse.infraestrutura.banco import Executor
from sinapse.repositorios.padroes_like import comeca_com, contem


class RepositorioHorarios:
    def __init__(self, executor: Executor):
        self._executor = executor

    def livres(self, especialidade: Optional[str], profissional_id: Optional[int],
               inicio: Optional[date], fim: Optional[date], limite: int,
               nome_do_profissional: Optional[str] = None) -> list[dict]:
        especialidade_prefixo = comeca_com(especialidade)
        nome = contem(nome_do_profissional)
        return self._executor.consultar(
            """SELECT h.id AS horario_id, p.id AS profissional_id, p.nome AS profissional,
                      p.especialidade, p.valor_consulta, h.data_hora
               FROM horarios h
               JOIN profissionais p ON p.id = h.profissional_id
               WHERE h.livre = 1
                 AND h.data_hora > NOW()
                 AND h.data_hora >= COALESCE(%s, CURDATE())
                 AND h.data_hora <  COALESCE(%s, CURDATE() + INTERVAL 7 DAY) + INTERVAL 1 DAY
                 AND (%s IS NULL OR p.especialidade LIKE %s)
                 AND (%s IS NULL OR p.id = %s)
                 AND (%s IS NULL OR p.nome LIKE %s)
               ORDER BY h.data_hora
               LIMIT %s""",
            (inicio, fim, especialidade_prefixo, especialidade_prefixo, profissional_id, profissional_id,
             nome, nome, limite),
        )

    def criar_grade(self, profissional_id: int, dias: int) -> None:
        self._executor.executar(
            """INSERT INTO horarios (profissional_id, data_hora, livre)
               WITH RECURSIVE dias AS (SELECT 0 AS d UNION ALL SELECT d + 1 FROM dias WHERE d < %s)
               SELECT %s, TIMESTAMP(CURDATE() + INTERVAL dias.d DAY, MAKETIME(turno.hora, 0, 0)), 1
               FROM dias
               CROSS JOIN (SELECT 8 AS hora UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11
                           UNION ALL SELECT 14 UNION ALL SELECT 15 UNION ALL SELECT 16) turno
               WHERE DAYOFWEEK(CURDATE() + INTERVAL dias.d DAY) NOT IN (1, 7)
                 AND TIMESTAMP(CURDATE() + INTERVAL dias.d DAY, MAKETIME(turno.hora, 0, 0)) > NOW()""",
            (dias - 1, profissional_id),
        )

    def travar(self, horario_id: int) -> Optional[dict]:
        return self._executor.consultar_um(
            """SELECT h.id, h.livre, h.data_hora, (h.data_hora > NOW()) AS futuro,
                      p.nome AS profissional, p.especialidade, p.endereco
               FROM horarios h JOIN profissionais p ON p.id = h.profissional_id
               WHERE h.id = %s FOR UPDATE""",
            (horario_id,),
        )

    def ocupar(self, horario_id: int) -> None:
        self._executor.executar("UPDATE horarios SET livre = 0 WHERE id = %s", (horario_id,))

    def liberar(self, horario_id: int) -> None:
        self._executor.executar("UPDATE horarios SET livre = 1 WHERE id = %s", (horario_id,))
