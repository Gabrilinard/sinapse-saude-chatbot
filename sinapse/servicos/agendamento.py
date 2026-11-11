from typing import Optional

from sinapse.dominio.erros import (ConsultaInativa, ConsultaNaoEncontrada, HorarioNaoEncontrado,
                                   HorarioOcupado, HorarioPassado)
from sinapse.dominio.modelos import STATUS_ATIVOS
from sinapse.infraestrutura.notificador import Evento, Notificador
from sinapse.repositorios import Repositorios
from sinapse.servicos import AbrirTransacao, exigir_paciente


class ServicoDeAgendamento:
    def __init__(self, abrir_transacao: AbrirTransacao, notificador: Notificador):
        self._abrir_transacao = abrir_transacao
        self._notificador = notificador

    def agendar(self, paciente_id: Optional[int], horario_id: int) -> dict:
        exigir_paciente(paciente_id)
        with self._abrir_transacao() as repositorios:
            horario = self._reservar_horario(repositorios, horario_id)
            consulta_id = repositorios.consultas.criar(paciente_id, horario_id)
            paciente = repositorios.pacientes.por_id(paciente_id)
        agendamento = {
            "consulta_id": consulta_id,
            "profissional": horario["profissional"],
            "especialidade": horario["especialidade"],
            "endereco": horario["endereco"],
            "data_hora": horario["data_hora"],
        }
        self._agendar_lembrete(paciente, agendamento)
        return agendamento

    def remarcar(self, paciente_id: Optional[int], consulta_id: int, novo_horario_id: int) -> dict:
        exigir_paciente(paciente_id)
        with self._abrir_transacao() as repositorios:
            consulta = self._consulta_ativa(repositorios, consulta_id, paciente_id)
            novo_horario = self._reservar_horario(repositorios, novo_horario_id)
            repositorios.horarios.liberar(consulta["horario_id"])
            repositorios.consultas.mudar_horario(consulta_id, novo_horario_id)
        return {"consulta_id": consulta_id, "profissional": novo_horario["profissional"],
                "data_hora": novo_horario["data_hora"]}

    def cancelar(self, paciente_id: Optional[int], consulta_id: int) -> None:
        exigir_paciente(paciente_id)
        with self._abrir_transacao() as repositorios:
            consulta = self._consulta_ativa(repositorios, consulta_id, paciente_id)
            repositorios.consultas.cancelar(consulta_id)
            repositorios.horarios.liberar(consulta["horario_id"])

    @staticmethod
    def _reservar_horario(repositorios: Repositorios, horario_id: int) -> dict:
        horario = repositorios.horarios.travar(horario_id)
        if not horario:
            raise HorarioNaoEncontrado()
        if not horario["futuro"]:
            raise HorarioPassado()
        if not horario["livre"]:
            raise HorarioOcupado()
        repositorios.horarios.ocupar(horario_id)
        return horario

    @staticmethod
    def _consulta_ativa(repositorios: Repositorios, consulta_id: int, paciente_id: int) -> dict:
        consulta = repositorios.consultas.travar(consulta_id)
        if not consulta or consulta["paciente_id"] != paciente_id:
            raise ConsultaNaoEncontrada()
        if consulta["status"] not in STATUS_ATIVOS or not consulta["futura"]:
            raise ConsultaInativa()
        return consulta

    def _agendar_lembrete(self, paciente: dict, agendamento: dict) -> None:
        self._notificador.notificar(Evento.LEMBRETE, {
            **agendamento,
            "paciente": paciente["nome"],
            "email": paciente["email"],
            "telefone": paciente["telefone"],
        })
