from dataclasses import replace

from sinapse.dominio.erros import (CpfJaCadastrado, DadoInvalido, EmailJaCadastrado, RegistroJaCadastrado,
                                   TermoNaoAceito)
from sinapse.dominio.localidades import UFS
from sinapse.dominio.modelos import CONVENIOS_ATENDIDOS, NovoPaciente, NovoProfissional, Perfil, UsuarioAutenticado
from sinapse.dominio.validacao import (validar_convenio, validar_cpf, validar_email, validar_nascimento,
                                       validar_nome, validar_registro_profissional, validar_senha,
                                       validar_telefone, validar_texto_obrigatorio, validar_valor_da_consulta)
from sinapse.infraestrutura.criptografia import gerar_hash
from sinapse.servicos import AbrirTransacao

DIAS_DE_AGENDA_INICIAL = 30


class ServicoDeCadastro:
    def __init__(self, abrir_transacao: AbrirTransacao):
        self._abrir_transacao = abrir_transacao

    def cadastrar_paciente(self, dados: NovoPaciente) -> UsuarioAutenticado:
        paciente = self._validar_paciente(dados)
        with self._abrir_transacao() as repositorios:
            if repositorios.pacientes.cpf_cadastrado(paciente.cpf):
                raise CpfJaCadastrado()
            paciente_id = repositorios.pacientes.criar(paciente)
            repositorios.auditoria.registrar("paciente", paciente_id, "cadastro", "aceitou_termo_lgpd=True")
        return UsuarioAutenticado(Perfil.PACIENTE, paciente_id, paciente.nome)

    def cadastrar_profissional(self, dados: NovoProfissional) -> UsuarioAutenticado:
        profissional = self._validar_profissional(dados)
        with self._abrir_transacao() as repositorios:
            if repositorios.profissionais.email_cadastrado(profissional.email):
                raise EmailJaCadastrado()
            if repositorios.profissionais.registro_cadastrado(profissional.conselho):
                raise RegistroJaCadastrado()
            profissional_id = repositorios.profissionais.criar(profissional, gerar_hash(profissional.senha))
            repositorios.profissionais.adicionar_convenios(profissional_id, profissional.convenios)
            repositorios.horarios.criar_grade(profissional_id, DIAS_DE_AGENDA_INICIAL)
            repositorios.auditoria.registrar("profissional", profissional_id, "cadastro_profissional",
                                             f"conselho={profissional.conselho}")
        return UsuarioAutenticado(Perfil.PROFISSIONAL, profissional_id, profissional.nome)

    @staticmethod
    def _validar_paciente(dados: NovoPaciente) -> NovoPaciente:
        if not dados.aceitou_termo_lgpd:
            raise TermoNaoAceito()
        return replace(
            dados,
            nome=validar_nome(dados.nome),
            cpf=validar_cpf(dados.cpf),
            nascimento=validar_nascimento(dados.nascimento),
            telefone=validar_telefone(dados.telefone),
            email=validar_email(dados.email),
            convenio=validar_convenio(dados.convenio or ""),
        )

    @staticmethod
    def _validar_profissional(dados: NovoProfissional) -> NovoProfissional:
        if dados.especialidade not in dados.profissao.especialidades:
            raise DadoInvalido("Especialidade não corresponde à profissão escolhida.")
        if dados.uf_do_registro not in UFS:
            raise DadoInvalido("UF do registro inválida.")
        if dados.localizacao is None:
            raise DadoInvalido("Escolha o bairro do consultório.")
        if any(convenio not in CONVENIOS_ATENDIDOS for convenio in dados.convenios):
            raise DadoInvalido("Convênio não atendido.")
        return replace(
            dados,
            nome=validar_nome(dados.nome),
            numero_do_registro=validar_registro_profissional(dados.numero_do_registro),
            valor_consulta=validar_valor_da_consulta(dados.valor_consulta),
            endereco=(f"{validar_texto_obrigatorio(dados.endereco, 'o endereço do consultório')}"
                      f" - {dados.localizacao.bairro}"),
            email=validar_email(dados.email),
            senha=validar_senha(dados.senha, dados.confirmacao_da_senha),
        )
