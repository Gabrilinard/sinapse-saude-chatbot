import re
from dataclasses import replace
from typing import Optional

from sinapse.dominio.erros import DadoInvalido
from sinapse.dominio.formatacao import interpretar_data, remover_acentos
from sinapse.dominio.modelos import FiltroProfissionais, Localizacao
from sinapse.servicos import AbrirTransacao

SINONIMOS_DE_PARTICULAR = {"particular", "nenhum", "sem convenio"}
SEM_CONVENIO = ["apenas particular"]
_TITULOS = re.compile(r"^\s*(?:dr|dra|doutor|doutora|prof|profa)\.?\s+", re.IGNORECASE)


def _nome_sem_titulo(nome: Optional[str]) -> Optional[str]:
    if not nome or not nome.strip():
        return None
    return _TITULOS.sub("", nome.strip()) or None


class ServicoDeBusca:
    def __init__(self, abrir_transacao: AbrirTransacao):
        self._abrir_transacao = abrir_transacao

    def buscar_profissionais(self, filtro: FiltroProfissionais, localizacao: Optional[Localizacao]) -> list[dict]:
        filtro = self._normalizar(filtro, localizacao)
        with self._abrir_transacao() as repositorios:
            profissionais = repositorios.profissionais.buscar(filtro, localizacao)
            for profissional in profissionais:
                profissional["convenios"] = repositorios.profissionais.convenios(profissional["id"]) or SEM_CONVENIO
        return profissionais

    def horarios_livres(self, especialidade: Optional[str] = None, profissional_id: Optional[int] = None,
                        data_inicio: Optional[str] = None, data_fim: Optional[str] = None,
                        limite: int = 10, nome_do_profissional: Optional[str] = None) -> list[dict]:
        nome = _nome_sem_titulo(nome_do_profissional)
        if nome:
            profissional_id = None
        if not especialidade and not profissional_id and not nome:
            raise DadoInvalido("Informe a especialidade, o nome ou o profissional.")
        with self._abrir_transacao() as repositorios:
            return repositorios.horarios.livres(especialidade, profissional_id, interpretar_data(data_inicio),
                                                interpretar_data(data_fim), limite, nome)

    def especialidades(self) -> list[str]:
        with self._abrir_transacao() as repositorios:
            return repositorios.profissionais.especialidades()

    @staticmethod
    def _normalizar(filtro: FiltroProfissionais, localizacao: Optional[Localizacao]) -> FiltroProfissionais:
        if filtro.valor_max is not None and filtro.valor_max <= 0:
            raise DadoInvalido("O valor máximo precisa ser maior que zero.")
        convenio = filtro.convenio
        if convenio and remover_acentos(convenio.strip()) in SINONIMOS_DE_PARTICULAR:
            convenio = None
        raio_km = filtro.raio_km if localizacao else None
        return replace(filtro, convenio=convenio, raio_km=raio_km)
