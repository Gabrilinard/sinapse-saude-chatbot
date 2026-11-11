from datetime import date
from typing import Optional

from sinapse.dominio.modelos import CampoEditavel, NovoPaciente
from sinapse.infraestrutura.banco import Executor

_SQL_ATUALIZACAO_POR_CAMPO = {
    CampoEditavel.TELEFONE: "UPDATE pacientes SET telefone = %s WHERE id = %s",
    CampoEditavel.EMAIL: "UPDATE pacientes SET email = %s WHERE id = %s",
    CampoEditavel.CONVENIO: "UPDATE pacientes SET convenio = %s WHERE id = %s",
}


class RepositorioPacientes:
    def __init__(self, executor: Executor):
        self._executor = executor

    def por_id(self, paciente_id: int) -> Optional[dict]:
        return self._executor.consultar_um(
            """SELECT id, nome, cpf, data_nascimento, telefone, email, convenio
               FROM pacientes WHERE id = %s AND excluido_em IS NULL""",
            (paciente_id,),
        )

    def por_cpf_e_nascimento(self, cpf: str, nascimento: date) -> Optional[dict]:
        return self._executor.consultar_um(
            """SELECT id, nome, email, telefone FROM pacientes
               WHERE cpf = %s AND data_nascimento = %s AND excluido_em IS NULL""",
            (cpf, nascimento),
        )

    def cpf_cadastrado(self, cpf: str) -> bool:
        return self._executor.consultar_um("SELECT id FROM pacientes WHERE cpf = %s", (cpf,)) is not None

    def criar(self, paciente: NovoPaciente) -> int:
        return self._executor.executar(
            """INSERT INTO pacientes (nome, cpf, data_nascimento, telefone, email, convenio)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (paciente.nome, paciente.cpf, paciente.nascimento, paciente.telefone, paciente.email, paciente.convenio),
        )

    def atualizar(self, paciente_id: int, campo: CampoEditavel, valor: Optional[str]) -> None:
        self._executor.executar(_SQL_ATUALIZACAO_POR_CAMPO[campo], (valor, paciente_id))

    def exames(self, paciente_id: int) -> list[dict]:
        return self._executor.consultar(
            """SELECT e.data, e.descricao, p.nome AS profissional
               FROM exames e JOIN profissionais p ON p.id = e.profissional_id
               WHERE e.paciente_id = %s ORDER BY e.data DESC""",
            (paciente_id,),
        )

    def receitas(self, paciente_id: int) -> list[dict]:
        return self._executor.consultar(
            """SELECT r.data, r.descricao, p.nome AS profissional
               FROM receitas r JOIN profissionais p ON p.id = r.profissional_id
               WHERE r.paciente_id = %s ORDER BY r.data DESC""",
            (paciente_id,),
        )
