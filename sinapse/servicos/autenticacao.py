import secrets
from datetime import date
from typing import Callable, Optional

from sinapse.dominio.erros import AcessoBloqueado, CodigoExpirado, CodigoIncorreto, DadosNaoConferem
from sinapse.dominio.formatacao import somente_digitos
from sinapse.dominio.modelos import CodigoEnviado, Perfil, UsuarioAutenticado
from sinapse.infraestrutura.criptografia import confere_com_hash, gerar_hash
from sinapse.infraestrutura.notificador import Evento, Notificador
from sinapse.repositorios import Repositorios
from sinapse.repositorios.otp import BLOQUEIO_MINUTOS
from sinapse.servicos import AbrirTransacao

MAXIMO_DE_TENTATIVAS = 3


def gerar_codigo_de_seis_digitos() -> str:
    return f"{secrets.randbelow(10**6):06d}"


class ServicoDeAutenticacao:
    def __init__(self, abrir_transacao: AbrirTransacao, notificador: Notificador,
                 gerar_codigo: Callable[[], str] = gerar_codigo_de_seis_digitos):
        self._abrir_transacao = abrir_transacao
        self._notificador = notificador
        self._gerar_codigo = gerar_codigo

    def solicitar_codigo(self, cpf: str, nascimento: Optional[date]) -> CodigoEnviado:
        with self._abrir_transacao() as repositorios:
            paciente = repositorios.pacientes.por_cpf_e_nascimento(somente_digitos(cpf), nascimento)
            if not paciente:
                repositorios.auditoria.registrar("anonimo", None, "login_falhou", "cpf/nascimento não conferem")
        if not paciente:
            raise DadosNaoConferem()
        return self.reenviar_codigo(paciente["id"])

    def reenviar_codigo(self, paciente_id: int) -> CodigoEnviado:
        codigo = self._gerar_codigo()
        with self._abrir_transacao() as repositorios:
            self._garantir_desbloqueado(repositorios, paciente_id)
            paciente = repositorios.pacientes.por_id(paciente_id)
            repositorios.otp.salvar(paciente_id, gerar_hash(codigo))
            repositorios.auditoria.registrar("anonimo", None, "otp_enviado", f"paciente_id={paciente_id}")
        enviado = self._notificador.notificar(
            Evento.OTP, {"email": paciente["email"], "telefone": paciente["telefone"], "codigo": codigo})
        return CodigoEnviado(paciente_id, paciente["nome"], None if enviado else codigo)

    def verificar_codigo(self, paciente_id: int, codigo: str) -> UsuarioAutenticado:
        with self._abrir_transacao() as repositorios:
            self._garantir_desbloqueado(repositorios, paciente_id)
            estado = repositorios.otp.estado(paciente_id)
            if not estado or not estado["codigo_hash"] or estado["expirado"]:
                raise CodigoExpirado()
            if confere_com_hash((codigo or "").strip(), estado["codigo_hash"]):
                repositorios.otp.consumir(paciente_id)
                repositorios.auditoria.registrar("paciente", paciente_id, "login_ok")
                paciente = repositorios.pacientes.por_id(paciente_id)
                return UsuarioAutenticado(Perfil.PACIENTE, paciente_id, paciente["nome"])
            erro = self._registrar_erro(repositorios, paciente_id, estado["tentativas"] + 1)
        raise erro

    def autenticar_profissional(self, email: str, senha: str) -> UsuarioAutenticado:
        with self._abrir_transacao() as repositorios:
            profissional = repositorios.profissionais.por_email((email or "").strip().lower())
            if profissional and confere_com_hash(senha or "", profissional["senha_hash"]):
                repositorios.auditoria.registrar("profissional", profissional["id"], "login_ok")
                return UsuarioAutenticado(Perfil.PROFISSIONAL, profissional["id"], profissional["nome"])
            repositorios.auditoria.registrar("anonimo", None, "login_profissional_falhou")
        raise DadosNaoConferem()

    @staticmethod
    def _garantir_desbloqueado(repositorios: Repositorios, paciente_id: int) -> None:
        estado = repositorios.otp.estado(paciente_id)
        if estado and estado["bloqueado"]:
            raise AcessoBloqueado(int(estado["minutos_bloqueio"]))

    @staticmethod
    def _registrar_erro(repositorios: Repositorios, paciente_id: int, tentativas: int) -> Exception:
        repositorios.auditoria.registrar("anonimo", None, "otp_incorreto", f"paciente_id={paciente_id}")
        if tentativas >= MAXIMO_DE_TENTATIVAS:
            repositorios.otp.bloquear(paciente_id)
            return AcessoBloqueado(BLOQUEIO_MINUTOS)
        repositorios.otp.registrar_tentativa(paciente_id, tentativas)
        return CodigoIncorreto(MAXIMO_DE_TENTATIVAS - tentativas)
