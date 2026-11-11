import re
from datetime import date
from typing import Optional

from sinapse.dominio.erros import DadoInvalido
from sinapse.dominio.formatacao import remover_acentos, somente_digitos
from sinapse.dominio.modelos import CONVENIOS_ATENDIDOS

TAMANHO_DO_CPF = 11
IDADE_MAXIMA = 130
TAMANHO_MINIMO_DO_NOME = 5
TAMANHO_MINIMO_DO_REGISTRO, TAMANHO_MAXIMO_DO_REGISTRO = 4, 7
TAMANHO_MINIMO_DA_SENHA = 8
VALOR_MINIMO_DA_CONSULTA, VALOR_MAXIMO_DA_CONSULTA = 30, 2000


def _digito_verificador(digitos: str) -> int:
    peso_inicial = len(digitos) + 1
    soma = sum(int(digito) * peso for digito, peso in zip(digitos, range(peso_inicial, 1, -1)))
    resto = soma * 10 % 11
    return 0 if resto == 10 else resto


def validar_cpf(valor: str) -> str:
    cpf = somente_digitos(valor)
    if len(cpf) != TAMANHO_DO_CPF or cpf == cpf[0] * TAMANHO_DO_CPF:
        raise DadoInvalido("CPF inválido.")
    primeiro = _digito_verificador(cpf[:9])
    segundo = _digito_verificador(cpf[:9] + str(primeiro))
    if cpf[9:] != f"{primeiro}{segundo}":
        raise DadoInvalido("CPF inválido.")
    return cpf


def validar_nome(valor: str) -> str:
    nome = " ".join((valor or "").split())
    if len(nome) < TAMANHO_MINIMO_DO_NOME or " " not in nome:
        raise DadoInvalido("Informe o nome completo.")
    return nome


def validar_nascimento(valor: Optional[date]) -> date:
    hoje = date.today()
    if valor is None or valor > hoje or hoje.year - valor.year > IDADE_MAXIMA:
        raise DadoInvalido("Data de nascimento inválida.")
    return valor


def validar_telefone(valor: str) -> str:
    telefone = somente_digitos(valor)
    if len(telefone) not in (10, 11):
        raise DadoInvalido("Telefone inválido. Informe DDD + número (10 ou 11 dígitos).")
    return telefone


def validar_email(valor: str) -> str:
    email = (valor or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise DadoInvalido("E-mail inválido.")
    return email


def validar_convenio(valor: str) -> Optional[str]:
    escolhido = remover_acentos((valor or "").strip())
    if escolhido in ("", "particular", "nenhum"):
        return None
    for convenio in CONVENIOS_ATENDIDOS:
        if remover_acentos(convenio) == escolhido:
            return convenio
    raise DadoInvalido("Convênio não atendido. Opções: " + ", ".join(CONVENIOS_ATENDIDOS) + " ou Particular.")


def validar_registro_profissional(valor: str) -> str:
    registro = somente_digitos(valor)
    if not TAMANHO_MINIMO_DO_REGISTRO <= len(registro) <= TAMANHO_MAXIMO_DO_REGISTRO:
        raise DadoInvalido(f"Número do registro inválido. Informe de {TAMANHO_MINIMO_DO_REGISTRO} a "
                           f"{TAMANHO_MAXIMO_DO_REGISTRO} dígitos.")
    return registro


def validar_senha(senha: str, confirmacao: str) -> str:
    if len(senha or "") < TAMANHO_MINIMO_DA_SENHA:
        raise DadoInvalido(f"A senha precisa ter pelo menos {TAMANHO_MINIMO_DA_SENHA} caracteres.")
    if senha != confirmacao:
        raise DadoInvalido("As senhas não conferem.")
    return senha


def validar_valor_da_consulta(valor: float) -> float:
    if not VALOR_MINIMO_DA_CONSULTA <= valor <= VALOR_MAXIMO_DA_CONSULTA:
        raise DadoInvalido(f"Valor da consulta deve ficar entre R$ {VALOR_MINIMO_DA_CONSULTA} e "
                           f"R$ {VALOR_MAXIMO_DA_CONSULTA}.")
    return round(valor, 2)


def validar_texto_obrigatorio(valor: str, campo: str) -> str:
    texto = " ".join((valor or "").split())
    if not texto:
        raise DadoInvalido(f"Informe {campo}.")
    return texto
