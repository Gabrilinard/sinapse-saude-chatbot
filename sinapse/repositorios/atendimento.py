from typing import Optional

from sinapse.infraestrutura.banco import Executor


class RepositorioFaq:
    def __init__(self, executor: Executor):
        self._executor = executor

    def todas(self) -> list[dict]:
        return self._executor.consultar("SELECT id, pergunta, resposta, palavras_chave FROM faq")


class RepositorioAtendimentosHumanos:
    def __init__(self, executor: Executor):
        self._executor = executor

    def abrir(self, paciente_id: Optional[int], motivo: str) -> int:
        return self._executor.executar(
            "INSERT INTO atendimentos_humanos (paciente_id, motivo) VALUES (%s, %s)",
            (paciente_id, motivo),
        )


class RepositorioSolicitacoesExclusao:
    def __init__(self, executor: Executor):
        self._executor = executor

    def em_aberto(self, paciente_id: int) -> Optional[dict]:
        return self._executor.consultar_um(
            """SELECT id, criado_em FROM solicitacoes_exclusao
               WHERE paciente_id = %s AND status IN ('pendente', 'em_analise')""",
            (paciente_id,),
        )

    def criar(self, paciente_id: int) -> int:
        return self._executor.executar("INSERT INTO solicitacoes_exclusao (paciente_id) VALUES (%s)", (paciente_id,))
