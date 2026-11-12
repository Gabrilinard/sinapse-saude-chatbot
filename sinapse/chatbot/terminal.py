from sinapse.chatbot.conversa import Conversa
from sinapse.chatbot.instrucoes import TERMO_LGPD
from sinapse.chatbot.portas import ModeloIndisponivel
from sinapse.dominio.modelos import Localizacao, SessaoUsuario
from sinapse.fabrica import criar_assistente

LOCALIZACAO_PADRAO = Localizacao("Centro", -5.0892, -42.8016)


def main() -> None:
    assistente = criar_assistente()
    conversa = Conversa()
    sessao = SessaoUsuario(localizacao=LOCALIZACAO_PADRAO)
    print(TERMO_LGPD, "\n")
    while pergunta := input("Você: ").strip():
        try:
            print("Sinapse:", assistente.responder(conversa, pergunta, sessao), "\n")
        except ModeloIndisponivel as erro:
            print(f"[assistente indisponível] {erro}\n")


if __name__ == "__main__":
    main()
