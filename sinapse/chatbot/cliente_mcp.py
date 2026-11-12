import asyncio
import atexit
import sys
import threading
from contextlib import AsyncExitStack, asynccontextmanager
from os import environ
from typing import Any, Awaitable, Callable

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

from sinapse.chatbot.portas import DefinicaoDeFerramenta
from sinapse.config import RAIZ_DO_PROJETO

MODULO_DO_SERVIDOR = "sinapse.mcp.servidor"


class ClienteMCP:
    def __init__(self):
        self._pilha = AsyncExitStack()
        self._sessao: ClientSession | None = None

    async def __aenter__(self) -> "ClienteMCP":
        parametros = StdioServerParameters(
            command=sys.executable,
            args=["-m", MODULO_DO_SERVIDOR],
            cwd=str(RAIZ_DO_PROJETO),
            env=dict(environ),
        )
        leitura, escrita = await self._pilha.enter_async_context(stdio_client(parametros))
        self._sessao = await self._pilha.enter_async_context(ClientSession(leitura, escrita))
        await self._sessao.initialize()
        return self

    async def __aexit__(self, *detalhes_do_erro) -> None:
        await self._pilha.aclose()

    async def listar(self) -> list[DefinicaoDeFerramenta]:
        resposta = await self._sessao.list_tools()
        return [DefinicaoDeFerramenta(f.name, f.description or "", f.inputSchema) for f in resposta.tools]

    async def executar(self, nome: str, argumentos: dict) -> str:
        try:
            resultado = await self._sessao.call_tool(nome, argumentos)
        except McpError as erro:
            return f"ERRO ao executar a ferramenta: {erro}"
        texto = "\n".join(c.text for c in resultado.content if c.type == "text") or "(sem retorno)"
        return f"ERRO: {texto}" if resultado.isError else texto


class ConexaoMCPCompartilhada:
    def __init__(self, fabrica: Callable[[], ClienteMCP] = ClienteMCP):
        self._fabrica = fabrica
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, name="servidor-mcp", daemon=True).start()
        self._cliente: ClienteMCP | None = None
        self._fechar: asyncio.Event | None = None
        self._tarefa: asyncio.Task | None = None
        self._ferramentas: list[DefinicaoDeFerramenta] | None = None
        atexit.register(self.encerrar)

    @asynccontextmanager
    async def __call__(self):
        yield _ProvedorCompartilhado(self)

    async def chamar(self, operacao: Callable[[ClienteMCP], Awaitable[Any]]) -> Any:
        futuro = asyncio.run_coroutine_threadsafe(self._chamar_no_loop(operacao), self._loop)
        return await asyncio.wrap_future(futuro)

    async def listar(self) -> list[DefinicaoDeFerramenta]:
        if self._ferramentas is None:
            self._ferramentas = await self.chamar(lambda cliente: cliente.listar())
        return self._ferramentas

    async def _chamar_no_loop(self, operacao):
        for tentativa in range(2):
            cliente = await self._garantir_aberto()
            try:
                return await operacao(cliente)
            except Exception as erro:
                print(f"[mcp] conexão perdida ({type(erro).__name__}), reabrindo", file=sys.stderr)
                await self._fechar_no_loop()
                if tentativa == 1:
                    raise

    async def _garantir_aberto(self) -> ClienteMCP:
        if self._cliente is not None and self._tarefa is not None and not self._tarefa.done():
            return self._cliente
        pronto = self._loop.create_future()
        self._fechar = asyncio.Event()
        self._tarefa = self._loop.create_task(self._manter_aberto(pronto, self._fechar))
        return await pronto

    async def _manter_aberto(self, pronto: asyncio.Future, fechar: asyncio.Event) -> None:
        try:
            async with self._fabrica() as cliente:
                self._cliente = cliente
                pronto.set_result(cliente)
                await fechar.wait()
        except Exception as erro:
            if not pronto.done():
                pronto.set_exception(erro)
        finally:
            self._cliente = None

    async def _fechar_no_loop(self) -> None:
        if self._fechar is not None:
            self._fechar.set()
        if self._tarefa is not None:
            await asyncio.wait({self._tarefa}, timeout=5)

    def encerrar(self) -> None:
        if self._loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self._fechar_no_loop(), self._loop).result(timeout=5)
            except Exception:
                pass


class _ProvedorCompartilhado:
    def __init__(self, conexao: ConexaoMCPCompartilhada):
        self._conexao = conexao

    async def listar(self) -> list[DefinicaoDeFerramenta]:
        return await self._conexao.listar()

    async def executar(self, nome: str, argumentos: dict) -> str:
        return await self._conexao.chamar(lambda cliente: cliente.executar(nome, argumentos))
