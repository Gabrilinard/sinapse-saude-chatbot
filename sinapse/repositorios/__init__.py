from contextlib import contextmanager
from typing import Iterator

from sinapse.infraestrutura.banco import BancoDeDados, Executor
from sinapse.repositorios.atendimento import (RepositorioAtendimentosHumanos, RepositorioFaq,
                                               RepositorioSolicitacoesExclusao)
from sinapse.repositorios.auditoria import RepositorioAuditoria
from sinapse.repositorios.consultas import RepositorioConsultas
from sinapse.repositorios.horarios import RepositorioHorarios
from sinapse.repositorios.otp import RepositorioOtp
from sinapse.repositorios.pacientes import RepositorioPacientes
from sinapse.repositorios.profissionais import RepositorioProfissionais


class Repositorios:
    def __init__(self, executor: Executor):
        self.profissionais = RepositorioProfissionais(executor)
        self.horarios = RepositorioHorarios(executor)
        self.consultas = RepositorioConsultas(executor)
        self.pacientes = RepositorioPacientes(executor)
        self.otp = RepositorioOtp(executor)
        self.faq = RepositorioFaq(executor)
        self.atendimentos = RepositorioAtendimentosHumanos(executor)
        self.solicitacoes_exclusao = RepositorioSolicitacoesExclusao(executor)
        self.auditoria = RepositorioAuditoria(executor)


class UnidadeDeTrabalho:
    def __init__(self, banco: BancoDeDados):
        self._banco = banco

    @contextmanager
    def __call__(self) -> Iterator[Repositorios]:
        with self._banco.transacao() as executor:
            yield Repositorios(executor)
