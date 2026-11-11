class ErroDeNegocio(Exception):
    mensagem_padrao = "Não foi possível concluir a operação."

    def __init__(self, mensagem: str | None = None):
        super().__init__(mensagem or self.mensagem_padrao)


class LoginNecessario(ErroDeNegocio):
    mensagem_padrao = ("Faça login para continuar: informe CPF, data de nascimento e o código "
                       "recebido, na barra lateral.")


class AcessoNegado(ErroDeNegocio):
    mensagem_padrao = "Acesso negado: acesso restrito a quem participa do cuidado do paciente."


class ApenasProfissional(ErroDeNegocio):
    mensagem_padrao = "Ferramenta disponível apenas para profissionais logados."


class DadoInvalido(ErroDeNegocio):
    mensagem_padrao = "Dado inválido."


class HorarioNaoEncontrado(ErroDeNegocio):
    mensagem_padrao = "Horário não encontrado. Busque os horários livres de novo."


class HorarioPassado(ErroDeNegocio):
    mensagem_padrao = "Esse horário já passou. Escolha outro."


class HorarioOcupado(ErroDeNegocio):
    mensagem_padrao = "Esse horário acabou de ser ocupado. Busque outro horário livre."


class ConsultaNaoEncontrada(ErroDeNegocio):
    mensagem_padrao = "Consulta não encontrada."


class ConsultaInativa(ErroDeNegocio):
    mensagem_padrao = "Essa consulta não está ativa (já foi cancelada, realizada ou já passou)."


class CpfJaCadastrado(ErroDeNegocio):
    mensagem_padrao = "Este CPF já tem cadastro. Entre com CPF e data de nascimento."


class EmailJaCadastrado(ErroDeNegocio):
    mensagem_padrao = "Este e-mail já está cadastrado. Entre com e-mail e senha."


class RegistroJaCadastrado(ErroDeNegocio):
    mensagem_padrao = "Este registro profissional já está cadastrado."


class TermoNaoAceito(ErroDeNegocio):
    mensagem_padrao = "Para se cadastrar é preciso aceitar o termo de uso de dados (LGPD)."


class NadaEncontrado(ErroDeNegocio):
    mensagem_padrao = "Nenhum resultado encontrado."


class ErroDeAutenticacao(Exception):
    pass


class DadosNaoConferem(ErroDeAutenticacao):
    def __init__(self):
        super().__init__("Dados não conferem.")


class AcessoBloqueado(ErroDeAutenticacao):
    def __init__(self, minutos: int):
        super().__init__(f"Acesso bloqueado por excesso de tentativas. Tente de novo em {minutos} min.")


class CodigoExpirado(ErroDeAutenticacao):
    def __init__(self):
        super().__init__("Código expirado. Peça um novo código.")


class CodigoIncorreto(ErroDeAutenticacao):
    def __init__(self, tentativas_restantes: int):
        self.tentativas_restantes = tentativas_restantes
        super().__init__(f"Código incorreto. Restam {tentativas_restantes} tentativa(s).")
