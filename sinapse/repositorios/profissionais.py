from typing import Optional

from sinapse.dominio.modelos import FiltroProfissionais, Localizacao, NovoProfissional
from sinapse.infraestrutura.banco import Executor
from sinapse.repositorios.padroes_like import comeca_com, contem

LIMITE_DE_RESULTADOS = 5

_SQL_PROXIMO_HORARIO = """
    (SELECT MIN(h.data_hora) FROM horarios h
      WHERE h.profissional_id = p.id AND h.livre = 1 AND h.data_hora > NOW())"""

_SQL_FILTROS = """
    WHERE (%s IS NULL OR p.especialidade LIKE %s)
      AND (%s IS NULL OR p.valor_consulta <= %s)
      AND (%s IS NULL OR EXISTS (SELECT 1 FROM profissional_convenios pc
                                  WHERE pc.profissional_id = p.id AND pc.convenio LIKE %s))"""

_SQL_BUSCA_POR_DISTANCIA = f"""
    SELECT p.id, p.nome, p.especialidade, p.valor_consulta, p.endereco,
           ROUND(6371 * ACOS(LEAST(1, COS(RADIANS(%s)) * COS(RADIANS(p.lat))
                 * COS(RADIANS(p.lng) - RADIANS(%s))
                 + SIN(RADIANS(%s)) * SIN(RADIANS(p.lat)))), 1) AS distancia_km,
           {_SQL_PROXIMO_HORARIO} AS proximo_horario
    FROM profissionais p
    {_SQL_FILTROS}
    HAVING (%s IS NULL OR distancia_km <= %s)
    ORDER BY distancia_km, p.valor_consulta
    LIMIT {LIMITE_DE_RESULTADOS}"""

_SQL_BUSCA_POR_VALOR = f"""
    SELECT p.id, p.nome, p.especialidade, p.valor_consulta, p.endereco,
           NULL AS distancia_km,
           {_SQL_PROXIMO_HORARIO} AS proximo_horario
    FROM profissionais p
    {_SQL_FILTROS}
    ORDER BY p.valor_consulta
    LIMIT {LIMITE_DE_RESULTADOS}"""


class RepositorioProfissionais:
    def __init__(self, executor: Executor):
        self._executor = executor

    def buscar(self, filtro: FiltroProfissionais, localizacao: Optional[Localizacao]) -> list[dict]:
        especialidade = comeca_com(filtro.especialidade)
        convenio = contem(filtro.convenio)
        parametros_dos_filtros = (especialidade, especialidade, filtro.valor_max, filtro.valor_max,
                                  convenio, convenio)
        if localizacao is None:
            return self._executor.consultar(_SQL_BUSCA_POR_VALOR, parametros_dos_filtros)
        coordenadas = (localizacao.lat, localizacao.lng, localizacao.lat)
        raio = (filtro.raio_km, filtro.raio_km)
        return self._executor.consultar(_SQL_BUSCA_POR_DISTANCIA, coordenadas + parametros_dos_filtros + raio)

    def convenios(self, profissional_id: int) -> list[str]:
        linhas = self._executor.consultar(
            "SELECT convenio FROM profissional_convenios WHERE profissional_id = %s ORDER BY convenio",
            (profissional_id,),
        )
        return [linha["convenio"] for linha in linhas]

    def especialidades(self) -> list[str]:
        linhas = self._executor.consultar("SELECT DISTINCT especialidade FROM profissionais ORDER BY especialidade")
        return [linha["especialidade"] for linha in linhas]

    def email_cadastrado(self, email: str) -> bool:
        return self._executor.consultar_um("SELECT id FROM profissionais WHERE email = %s", (email,)) is not None

    def registro_cadastrado(self, conselho: str) -> bool:
        return self._executor.consultar_um("SELECT id FROM profissionais WHERE conselho = %s", (conselho,)) is not None

    def criar(self, profissional: NovoProfissional, senha_hash: str) -> int:
        localizacao = profissional.localizacao
        return self._executor.executar(
            """INSERT INTO profissionais
                   (nome, especialidade, conselho, valor_consulta, endereco, lat, lng, email, senha_hash)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (profissional.nome, profissional.especialidade, profissional.conselho, profissional.valor_consulta,
             profissional.endereco, localizacao.lat, localizacao.lng, profissional.email, senha_hash),
        )

    def adicionar_convenios(self, profissional_id: int, convenios: tuple[str, ...]) -> None:
        for convenio in convenios:
            self._executor.executar(
                "INSERT INTO profissional_convenios (profissional_id, convenio) VALUES (%s, %s)",
                (profissional_id, convenio),
            )

    def por_email(self, email: str) -> Optional[dict]:
        return self._executor.consultar_um(
            "SELECT id, nome, especialidade, senha_hash FROM profissionais WHERE email = %s",
            (email,),
        )
