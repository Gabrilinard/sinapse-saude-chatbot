import asyncio

from sinapse.chatbot.catalogo import CatalogoDeFerramentas
from sinapse.chatbot.conversa import ChamadaDeFerramenta, Conversa, Mensagem, ResultadoDeFerramenta
from sinapse.chatbot.instrucoes import montar_instrucoes
from sinapse.chatbot.portas import ConectarFerramentas, ModeloDeLinguagem, ProvedorDeFerramentas
from sinapse.chatbot.seguranca import (AGUARDANDO_CONFIRMACAO, RESPOSTA_DE_EMERGENCIA, DetectorDeEmergencia,
                                       PoliticaDeConfirmacao)
from sinapse.dominio.modelos import SessaoUsuario

MAXIMO_DE_CICLOS = 5
RESPOSTA_VAZIA = "Desculpe, não entendi. Pode repetir?"
LIMITE_DE_CICLOS_ATINGIDO = "Não consegui concluir o pedido agora. Quer que eu transfira para um atendente?"
FERRAMENTA_NAO_PERMITIDA = "Ferramenta não disponível para este perfil."


class Assistente:
    def __init__(self, modelo: ModeloDeLinguagem, conectar_ferramentas: ConectarFerramentas,
                 detector: DetectorDeEmergencia | None = None, politica: PoliticaDeConfirmacao | None = None,
                 maximo_de_ciclos: int = MAXIMO_DE_CICLOS):
        self._modelo = modelo
        self._conectar_ferramentas = conectar_ferramentas
        self._detector = detector or DetectorDeEmergencia()
        self._politica = politica or PoliticaDeConfirmacao()
        self._maximo_de_ciclos = maximo_de_ciclos

    def responder(self, conversa: Conversa, texto_do_usuario: str, sessao: SessaoUsuario) -> str:
        with conversa.tentativa():
            conversa.adicionar(Mensagem.do_usuario(texto_do_usuario))
            if self._detector.detectar(texto_do_usuario):
                return self._encerrar_rodada(conversa, RESPOSTA_DE_EMERGENCIA)
            return asyncio.run(self._conversar(conversa, sessao))

    async def _conversar(self, conversa: Conversa, sessao: SessaoUsuario) -> str:
        async with self._conectar_ferramentas() as provedor:
            catalogo = CatalogoDeFerramentas(await provedor.listar(), sessao.perfil)
            instrucoes = montar_instrucoes(sessao)
            for _ in range(self._maximo_de_ciclos):
                resposta = self._modelo.gerar(instrucoes, conversa.mensagens, catalogo.para_o_modelo())
                if not resposta.chamadas:
                    return self._encerrar_rodada(conversa, resposta.texto.strip() or RESPOSTA_VAZIA)
                conversa.adicionar(resposta)
                resultados = [await self._executar(provedor, catalogo, chamada, conversa, sessao)
                              for chamada in resposta.chamadas]
                conversa.adicionar(Mensagem.com_resultados(resultados))
        return self._encerrar_rodada(conversa, LIMITE_DE_CICLOS_ATINGIDO)

    async def _executar(self, provedor: ProvedorDeFerramentas, catalogo: CatalogoDeFerramentas,
                        chamada: ChamadaDeFerramenta, conversa: Conversa,
                        sessao: SessaoUsuario) -> ResultadoDeFerramenta:
        if not catalogo.permite(chamada.nome):
            return ResultadoDeFerramenta(chamada.nome, FERRAMENTA_NAO_PERMITIDA)
        argumentos = catalogo.argumentos_do_modelo(chamada.argumentos)
        if not self._politica.autorizar(conversa, chamada.nome, argumentos):
            return ResultadoDeFerramenta(chamada.nome, AGUARDANDO_CONFIRMACAO)
        argumentos |= catalogo.argumentos_da_sessao(chamada.nome, sessao)
        return ResultadoDeFerramenta(chamada.nome, await provedor.executar(chamada.nome, argumentos))

    @staticmethod
    def _encerrar_rodada(conversa: Conversa, texto: str) -> str:
        conversa.adicionar(Mensagem.do_modelo(texto))
        return texto
