import threading
from contextlib import contextmanager
from typing import Any, Iterator, Optional, Protocol, Sequence

import mysql.connector
from mysql.connector import pooling

from sinapse.config import ConfiguracaoBanco

FUSO_DE_TERESINA = "-03:00"
TAMANHO_DO_POOL = 5


class Executor(Protocol):
    def consultar(self, sql: str, parametros: Sequence[Any] = ()) -> list[dict]: ...

    def consultar_um(self, sql: str, parametros: Sequence[Any] = ()) -> Optional[dict]: ...

    def executar(self, sql: str, parametros: Sequence[Any] = ()) -> int: ...


class _ExecutorDeConexao:
    def __init__(self, conexao):
        self._cursor = conexao.cursor(dictionary=True)

    def consultar(self, sql, parametros=()):
        self._cursor.execute(sql, tuple(parametros))
        return self._cursor.fetchall()

    def consultar_um(self, sql, parametros=()):
        linhas = self.consultar(sql, parametros)
        return linhas[0] if linhas else None

    def executar(self, sql, parametros=()):
        self._cursor.execute(sql, tuple(parametros))
        return self._cursor.lastrowid


class BancoDeDados:
    def __init__(self, configuracao: ConfiguracaoBanco):
        self._configuracao = configuracao
        self._pool: Optional[pooling.MySQLConnectionPool] = None
        self._trava = threading.Lock()

    def testar_conexao(self) -> None:
        self._conectar().close()

    @contextmanager
    def transacao(self) -> Iterator[Executor]:
        conexao = self._conectar()
        try:
            conexao.start_transaction()
            yield _ExecutorDeConexao(conexao)
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
        finally:
            conexao.close()

    def _obter_pool(self) -> pooling.MySQLConnectionPool:
        with self._trava:
            if self._pool is None:
                self._pool = pooling.MySQLConnectionPool(
                    pool_name=f"sinapse_{id(self)}",
                    pool_size=TAMANHO_DO_POOL,
                    host=self._configuracao.host,
                    port=self._configuracao.porta,
                    user=self._configuracao.usuario,
                    password=self._configuracao.senha,
                    database=self._configuracao.nome,
                    charset="utf8mb4",
                    collation="utf8mb4_0900_ai_ci",
                )
            return self._pool

    def _conectar(self):
        try:
            conexao = self._obter_pool().get_connection()
            conexao.ping(reconnect=True, attempts=1)
        except pooling.PoolError:
            conexao = mysql.connector.connect(
                host=self._configuracao.host, port=self._configuracao.porta, user=self._configuracao.usuario,
                password=self._configuracao.senha, database=self._configuracao.nome,
                charset="utf8mb4", collation="utf8mb4_0900_ai_ci")
        cursor = conexao.cursor()
        cursor.execute("SET time_zone = %s", (FUSO_DE_TERESINA,))
        cursor.close()
        return conexao
