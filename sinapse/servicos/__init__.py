from typing import Callable, ContextManager, Optional

from sinapse.dominio.erros import ApenasProfissional, LoginNecessario
from sinapse.repositorios import Repositorios

AbrirTransacao = Callable[[], ContextManager[Repositorios]]


def exigir_paciente(paciente_id: Optional[int]) -> None:
    if not paciente_id:
        raise LoginNecessario()


def exigir_profissional(profissional_id: Optional[int]) -> None:
    if not profissional_id:
        raise ApenasProfissional()
