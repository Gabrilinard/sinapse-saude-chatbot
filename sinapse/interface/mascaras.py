"""Máscaras de digitação nos campos de texto, aplicadas no navegador enquanto o usuário digita.

Cada regra liga o rótulo do campo (ou o início dele) a um ou mais padrões, em que "0" é um dígito.
"""
import json

import streamlit as st

from sinapse.dominio.validacao import TAMANHO_MAXIMO_DO_REGISTRO

MASCARAS = [
    {"rotulo": "CPF", "prefixo": False, "padroes": ["000.000.000-00"]},
    {"rotulo": "Telefone com DDD", "prefixo": False, "padroes": ["(00) 0000-0000", "(00) 00000-0000"]},
    {"rotulo": "Código", "prefixo": False, "padroes": ["000000"]},
    {"rotulo": "Número do", "prefixo": True, "padroes": ["0" * TAMANHO_MAXIMO_DO_REGISTRO]},
]

TAMANHO_FORMATADO = {regra["rotulo"]: len(regra["padroes"][-1]) for regra in MASCARAS}

_SCRIPT_DAS_MASCARAS = """
(() => {
  if (window.mascarasSinapseAtivas) return;
  window.mascarasSinapseAtivas = true;
  const MASCARAS = %s;
  const quantidadeDeDigitos = (padrao) => (padrao.match(/0/g) || []).length;

  const formatar = (valor, padroes) => {
    const capacidade = Math.max(...padroes.map(quantidadeDeDigitos));
    const digitos = valor.replace(/\\D/g, '').slice(0, capacidade);
    const padrao = padroes.find((p) => quantidadeDeDigitos(p) >= digitos.length) || padroes[padroes.length - 1];
    let resultado = '';
    let posicao = 0;
    for (const caractere of padrao) {
      if (posicao >= digitos.length) break;
      resultado += caractere === '0' ? digitos[posicao++] : caractere;
    }
    return resultado;
  };

  const regraDoCampo = (rotulo) =>
    MASCARAS.find((m) => (m.prefixo ? rotulo.startsWith(m.rotulo) : rotulo === m.rotulo));

  const definirValor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;

  const aplicar = (campo, regra) => {
    const formatado = formatar(campo.value, regra.padroes);
    if (formatado === campo.value) return;
    definirValor.call(campo, formatado);
    campo.dispatchEvent(new Event('input', { bubbles: true }));
  };

  const prepararCampos = () => {
    document.querySelectorAll('input[aria-label]').forEach((campo) => {
      const regra = regraDoCampo(campo.getAttribute('aria-label'));
      if (!regra || campo.dataset.mascara) return;
      campo.dataset.mascara = 'ativa';
      campo.setAttribute('inputmode', 'numeric');
      campo.addEventListener('input', () => aplicar(campo, regra));
      aplicar(campo, regra);
    });
  };

  new MutationObserver(prepararCampos).observe(document.body, { childList: true, subtree: true });
  prepararCampos();
})();
"""


def ativar_mascaras() -> None:
    script = _SCRIPT_DAS_MASCARAS % json.dumps(MASCARAS, ensure_ascii=False)
    st.html(f"<script>{script}</script>", unsafe_allow_javascript=True)
