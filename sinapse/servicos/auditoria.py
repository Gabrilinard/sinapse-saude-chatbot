from typing import Optional

from sinapse.servicos import AbrirTransacao


class ServicoDeAuditoria:
    def __init__(self, abrir_transacao: AbrirTransacao):
        self._abrir_transacao = abrir_transacao

    def registrar(self, usuario_tipo: str, usuario_id: Optional[int], acao: str, detalhe: str = "") -> None:
        with self._abrir_transacao() as repositorios:
            repositorios.auditoria.registrar(usuario_tipo, usuario_id, acao, detalhe)

    def ultimos_registros(self, limite: int = 50) -> list[dict]:
        with self._abrir_transacao() as repositorios:
            return repositorios.auditoria.ultimas(limite)
