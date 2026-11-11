from dataclasses import replace

from sinapse.chatbot.portas import DefinicaoDeFerramenta
from sinapse.dominio.modelos import Perfil, SessaoUsuario

PARAMETROS_DA_SESSAO = frozenset({"paciente_id", "profissional_id", "lat", "lng"})

_FERRAMENTAS_PUBLICAS = frozenset({"buscar_profissionais", "listar_disponiveis", "buscar_faq", "transferir_atendente"})

FERRAMENTAS_POR_PERFIL = {
    Perfil.VISITANTE: _FERRAMENTAS_PUBLICAS,
    Perfil.PACIENTE: _FERRAMENTAS_PUBLICAS | {
        "buscar_minhas_consultas", "agendar_consulta", "remarcar_consulta", "cancelar_consulta",
        "atualizar_dados", "solicitar_exclusao",
    },
    Perfil.PROFISSIONAL: frozenset({"minha_agenda", "historico_paciente"}),
}


def _sem_parametros_da_sessao(ferramenta: DefinicaoDeFerramenta) -> DefinicaoDeFerramenta:
    parametros = dict(ferramenta.parametros)
    parametros["properties"] = {nome: schema for nome, schema in parametros.get("properties", {}).items()
                                if nome not in PARAMETROS_DA_SESSAO}
    parametros["required"] = [nome for nome in parametros.get("required", []) if nome not in PARAMETROS_DA_SESSAO]
    return replace(ferramenta, parametros=parametros)


def _valores_da_sessao(sessao: SessaoUsuario) -> dict:
    localizacao = sessao.localizacao
    return {
        "paciente_id": sessao.paciente_id,
        "profissional_id": sessao.profissional_id,
        "lat": localizacao.lat if localizacao else None,
        "lng": localizacao.lng if localizacao else None,
    }


class CatalogoDeFerramentas:
    """Decide quais ferramentas o perfil enxerga e monta os argumentos com os dados da sessão."""

    def __init__(self, ferramentas: list[DefinicaoDeFerramenta], perfil: Perfil):
        permitidas = FERRAMENTAS_POR_PERFIL[perfil]
        self._ferramentas = {f.nome: f for f in ferramentas if f.nome in permitidas}

    def para_o_modelo(self) -> list[DefinicaoDeFerramenta]:
        return [_sem_parametros_da_sessao(ferramenta) for ferramenta in self._ferramentas.values()]

    def permite(self, nome: str) -> bool:
        return nome in self._ferramentas

    @staticmethod
    def argumentos_do_modelo(argumentos: dict) -> dict:
        return {nome: valor for nome, valor in argumentos.items() if nome not in PARAMETROS_DA_SESSAO}

    def argumentos_da_sessao(self, nome: str, sessao: SessaoUsuario) -> dict:
        aceitos = set(self._ferramentas[nome].parametros.get("properties", {})) & PARAMETROS_DA_SESSAO
        valores = _valores_da_sessao(sessao)
        return {parametro: valores[parametro] for parametro in aceitos if valores[parametro] is not None}
