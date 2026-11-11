import json
import sys
import urllib.request
from enum import StrEnum
from typing import Protocol

TEMPO_LIMITE_SEGUNDOS = 5


class Evento(StrEnum):
    LEMBRETE = "lembrete"
    OTP = "otp"
    ATENDENTE = "atendente"


class Notificador(Protocol):
    def notificar(self, evento: Evento, dados: dict) -> bool: ...


class NotificadorN8n:
    """Envia eventos aos webhooks do n8n. Sem URL configurada, apenas registra no stderr."""

    def __init__(self, webhooks: dict[str, str]):
        self._webhooks = webhooks

    def notificar(self, evento: Evento, dados: dict) -> bool:
        corpo = json.dumps(dados, ensure_ascii=False, default=str)
        url = self._webhooks.get(evento.value)
        if not url:
            self._registrar(f"[n8n simulado] {evento.value}: {corpo}")
            return False
        try:
            requisicao = urllib.request.Request(
                url, data=corpo.encode("utf-8"), method="POST",
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(requisicao, timeout=TEMPO_LIMITE_SEGUNDOS).close()
            return True
        except OSError as erro:
            self._registrar(f"[n8n] falha ao enviar {evento.value}: {erro}")
            return False

    @staticmethod
    def _registrar(mensagem: str) -> None:
        print(mensagem, file=sys.stderr, flush=True)
