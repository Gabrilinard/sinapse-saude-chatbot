from datetime import date
from typing import Optional

from sinapse.dominio.modelos import Periodo
from sinapse.infraestrutura.banco import Executor


class RepositorioConsultas:
    def __init__(self, executor: Executor):
        self._executor = executor

    def criar(self, paciente_id: int, horario_id: int) -> int:
        return self._executor.executar(
            "INSERT INTO consultas (paciente_id, horario_id, status) VALUES (%s, %s, 'agendada')",
            (paciente_id, horario_id),
        )

    def travar(self, consulta_id: int) -> Optional[dict]:
        return self._executor.consultar_um(
            """SELECT c.id, c.paciente_id, c.status, c.horario_id, (h.data_hora > NOW()) AS futura
               FROM consultas c JOIN horarios h ON h.id = c.horario_id
               WHERE c.id = %s FOR UPDATE""",
            (consulta_id,),
        )

    def detalhes(self, consulta_id: int) -> Optional[dict]:
        return self._executor.consultar_um(
            """SELECT p.nome AS profissional, p.especialidade, h.data_hora
               FROM consultas c
               JOIN horarios h      ON h.id = c.horario_id
               JOIN profissionais p ON p.id = h.profissional_id
               WHERE c.id = %s""",
            (consulta_id,),
        )

    def mudar_horario(self, consulta_id: int, novo_horario_id: int) -> None:
        self._executor.executar(
            """UPDATE consultas SET horario_id = %s, status = 'remarcada', lembrete_enviado = 0
               WHERE id = %s""",
            (novo_horario_id, consulta_id),
        )

    def cancelar(self, consulta_id: int) -> None:
        self._executor.executar("UPDATE consultas SET status = 'cancelada' WHERE id = %s", (consulta_id,))

    def do_paciente(self, paciente_id: int, periodo: Periodo) -> list[dict]:
        return self._executor.consultar(
            """SELECT c.id AS consulta_id, c.status, h.data_hora,
                      p.nome AS profissional, p.especialidade, p.endereco
               FROM consultas c
               JOIN horarios h      ON h.id = c.horario_id
               JOIN profissionais p ON p.id = h.profissional_id
               WHERE c.paciente_id = %s
                 AND (%s = 'todas'
                      OR (%s = 'futuras'  AND h.data_hora >= NOW() AND c.status <> 'cancelada')
                      OR (%s = 'passadas' AND h.data_hora <  NOW()))
               ORDER BY h.data_hora""",
            (paciente_id, periodo.value, periodo.value, periodo.value),
        )

    def agenda_do_profissional(self, profissional_id: int, inicio: Optional[date], fim: Optional[date]) -> list[dict]:
        return self._executor.consultar(
            """SELECT c.id AS consulta_id, c.status, h.data_hora,
                      pa.id AS paciente_id, pa.nome AS paciente, pa.cpf
               FROM consultas c
               JOIN horarios h   ON h.id = c.horario_id
               JOIN pacientes pa ON pa.id = c.paciente_id
               WHERE h.profissional_id = %s
                 AND c.status <> 'cancelada'
                 AND h.data_hora >= COALESCE(%s, CURDATE())
                 AND h.data_hora <  COALESCE(%s, CURDATE() + INTERVAL 7 DAY) + INTERVAL 1 DAY
               ORDER BY h.data_hora""",
            (profissional_id, inicio, fim),
        )

    def existe_vinculo(self, profissional_id: int, paciente_id: int) -> bool:
        return self._executor.consultar_um(
            """SELECT 1 AS vinculo FROM consultas c JOIN horarios h ON h.id = c.horario_id
               WHERE c.paciente_id = %s AND h.profissional_id = %s AND c.status <> 'cancelada'
               LIMIT 1""",
            (paciente_id, profissional_id),
        ) is not None
