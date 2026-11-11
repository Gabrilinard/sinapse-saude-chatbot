from typing import Optional

from sinapse.dominio.erros import AcessoNegado, NadaEncontrado
from sinapse.dominio.formatacao import interpretar_data, mascarar_cpf
from sinapse.dominio.modelos import Periodo
from sinapse.servicos import AbrirTransacao, exigir_profissional

AVISO_RESUMO_IA = "Resumo gerado por IA, revise antes da consulta."


class ServicoDoProfissional:
    def __init__(self, abrir_transacao: AbrirTransacao):
        self._abrir_transacao = abrir_transacao

    def agenda(self, profissional_id: Optional[int], data_inicio: Optional[str], data_fim: Optional[str]) -> list[dict]:
        exigir_profissional(profissional_id)
        with self._abrir_transacao() as repositorios:
            agenda = repositorios.consultas.agenda_do_profissional(
                profissional_id, interpretar_data(data_inicio), interpretar_data(data_fim))
        if not agenda:
            raise NadaEncontrado("Nenhuma consulta nesse período.")
        return [{**item, "cpf": mascarar_cpf(item["cpf"])} for item in agenda]

    def historico_do_paciente(self, profissional_id: Optional[int], paciente_id: int) -> dict:
        exigir_profissional(profissional_id)
        with self._abrir_transacao() as repositorios:
            if not repositorios.consultas.existe_vinculo(profissional_id, paciente_id):
                raise AcessoNegado()
            paciente = repositorios.pacientes.por_id(paciente_id)
            if not paciente:
                raise NadaEncontrado("Paciente não encontrado.")
            return {
                "aviso": AVISO_RESUMO_IA,
                "paciente": {
                    "nome": paciente["nome"],
                    "cpf": mascarar_cpf(paciente["cpf"]),
                    "data_nascimento": paciente["data_nascimento"],
                    "convenio": paciente["convenio"] or "Particular",
                },
                "consultas": repositorios.consultas.do_paciente(paciente_id, Periodo.TODAS),
                "exames": repositorios.pacientes.exames(paciente_id),
                "receitas": repositorios.pacientes.receitas(paciente_id),
            }
