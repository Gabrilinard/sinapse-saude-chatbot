from typing import Callable, Optional

from sinapse.dominio.erros import NadaEncontrado
from sinapse.dominio.modelos import CampoEditavel, Periodo, TipoRegistro
from sinapse.dominio.validacao import validar_convenio, validar_email, validar_telefone
from sinapse.servicos import AbrirTransacao, exigir_paciente

AVISO_PRAZO_LEGAL = ("Pedido de exclusão registrado e será analisado. Dados de saúde podem ter prazo legal "
                     "de guarda, por isso não são apagados na hora.")

VALIDADORES: dict[CampoEditavel, Callable[[str], Optional[str]]] = {
    CampoEditavel.TELEFONE: validar_telefone,
    CampoEditavel.EMAIL: validar_email,
    CampoEditavel.CONVENIO: validar_convenio,
}


class ServicoDoPaciente:
    def __init__(self, abrir_transacao: AbrirTransacao):
        self._abrir_transacao = abrir_transacao

    def registros(self, paciente_id: Optional[int], tipo: TipoRegistro, periodo: Periodo) -> dict:
        exigir_paciente(paciente_id)
        registros = {}
        with self._abrir_transacao() as repositorios:
            if tipo in (TipoRegistro.CONSULTAS, TipoRegistro.TODOS):
                registros["consultas"] = repositorios.consultas.do_paciente(paciente_id, periodo)
            if tipo in (TipoRegistro.EXAMES, TipoRegistro.TODOS):
                registros["exames"] = repositorios.pacientes.exames(paciente_id)
            if tipo in (TipoRegistro.RECEITAS, TipoRegistro.TODOS):
                registros["receitas"] = repositorios.pacientes.receitas(paciente_id)
        if not any(registros.values()):
            raise NadaEncontrado(f"Nenhum registro encontrado ({tipo}, {periodo}).")
        return registros

    def atualizar_cadastro(self, paciente_id: Optional[int], campo: CampoEditavel, novo_valor: str) -> None:
        exigir_paciente(paciente_id)
        valor = VALIDADORES[campo](novo_valor or "")
        with self._abrir_transacao() as repositorios:
            repositorios.pacientes.atualizar(paciente_id, campo, valor)

    def solicitar_exclusao(self, paciente_id: Optional[int]) -> dict:
        exigir_paciente(paciente_id)
        with self._abrir_transacao() as repositorios:
            pedido_em_aberto = repositorios.solicitacoes_exclusao.em_aberto(paciente_id)
            if pedido_em_aberto:
                return {"mensagem": "Já existe um pedido de exclusão em análise.",
                        "protocolo": pedido_em_aberto["id"]}
            protocolo = repositorios.solicitacoes_exclusao.criar(paciente_id)
        return {"mensagem": AVISO_PRAZO_LEGAL, "protocolo": protocolo}
