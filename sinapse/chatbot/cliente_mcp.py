import sys
from contextlib import AsyncExitStack
from os import environ

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

from sinapse.chatbot.portas import DefinicaoDeFerramenta
from sinapse.config import RAIZ_DO_PROJETO

MODULO_DO_SERVIDOR = "sinapse.mcp.servidor"


class ClienteMCP:
    """Inicia o servidor MCP como subprocesso (stdio) e expõe as ferramentas dele."""

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
