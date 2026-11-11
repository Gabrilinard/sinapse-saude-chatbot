from sinapse.dominio.modelos import Localizacao

UF_PADRAO = "PI"

UFS = ("AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE",
       "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO")

BAIRROS_DE_TERESINA = {
    "Centro": (-5.0892, -42.8016),
    "Jóquei": (-5.0745, -42.7875),
    "Fátima": (-5.0710, -42.7960),
    "Ininga": (-5.0580, -42.7920),
    "São Cristóvão": (-5.0640, -42.7700),
    "Horto Florestal": (-5.0620, -42.7810),
    "Noivos": (-5.0800, -42.7800),
    "Piçarra": (-5.1000, -42.7980),
    "Cristo Rei": (-5.1170, -42.8070),
    "Dirceu Arcoverde": (-5.1060, -42.7380),
    "Mocambinho": (-5.0230, -42.8100),
    "Buenos Aires": (-5.0450, -42.8150),
    "Santa Maria da Codipi": (-4.9970, -42.7900),
}


def localizacao_do_bairro(bairro: str) -> Localizacao:
    return Localizacao(bairro, *BAIRROS_DE_TERESINA[bairro])
