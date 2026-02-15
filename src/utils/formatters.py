"""
Utilitários para formatação, limpeza e normalização de strings.
"""

import unicodedata
from typing import Optional


def fmt_int(n) -> str:
    """
    Formata número como string com separador de milhar (ponto).
    
    Exemplo:
        fmt_int(1234567) -> "1.234.567"
    """
    try:
        return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)


def fix_mojibake(s: str) -> str:
    """
    Corrige encoding quebrado (mojibake).
    
    Exemplo:
        fix_mojibake("AmapÃ¡") -> "Amapá"
    """
    if s is None:
        return s

    s = str(s)
    if "Ã" in s or "�" in s:
        try:
            return s.encode("latin1").decode("utf-8")
        except Exception:
            return s
    return s


def strip_accents(s: str) -> str:
    """
    Remove acentos de uma string.
    
    Exemplo:
        strip_accents("São Paulo") -> "Sao Paulo"
    """
    if s is None:
        return s

    s = str(s)
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) 
        if not unicodedata.combining(c)
    )


def clean_label(x) -> str:
    """
    Limpeza completa: corrige encoding, remove espaços extras.
    
    Exemplo:
        clean_label("  Amapá   ") -> "Amapá"
    """
    if x is None:
        return x

    x = fix_mojibake(str(x)).strip()
    x = " ".join(x.split())
    return x


def normalize_uf(value: str) -> Optional[str]:
    """
    Normaliza entrada para UF válido (2 letras maiúsculas).
    
    Suporta:
    - UF já correto: "SP" -> "SP"
    - Nome estado: "São Paulo" -> "SP"
    - Minúsculas: "sp" -> "SP"
    """
    from ..config.constants import STATE_TO_UF, UF_ORDER

    if value is None:
        return None

    value = str(value).strip().upper()

    # Já é UF válido?
    if value in UF_ORDER:
        return value

    # Tenta como nome de estado
    value_pt = value.replace("Á", "A").replace("Â", "A").replace("Ã", "A")
    value_pt = value_pt.replace("É", "E").replace("Ê", "E").replace("Ç", "C")

    if value_pt in STATE_TO_UF:
        return STATE_TO_UF[value_pt]

    # Tenta nome exato
    for state, uf in STATE_TO_UF.items():
        if state.upper() == value:
            return uf

    return None


def macro_sector_from_label(sector_label: str) -> str:
    """
    Mapeia label de setor para macro-setor executivo.
    
    Setores padrão: Agronegócio, Indústria, Comércio, Serviços, Tecnologia
    """
    from ..config.constants import MACRO_SECTORS

    if sector_label is None:
        return "Serviços"  # default

    sector = str(sector_label).lower().strip()

    # Palavras-chave por macro-setor
    keywords = {
        "Agronegócio": [
            "agro", "agricultur", "pecuári", "pesca", "alimento",
            "bebid", "tabaco", "florestal"
        ],
        "Indústria": [
            "indústr", "manufatur", "químic", "farmacêutic", "metal",
            "máquina", "veículo", "minera", "eletrônic", "texto",
            "vestuár", "couro", "papel", "celulose", "petróleo",
            "gás", "construção", "eletricidad"
        ],
        "Comércio": [
            "comércio", "venda", "varejo", "atacado", "distribuição",
            "importação", "exportação", "logística", "transporte"
        ],
        "Tecnologia": [
            "tecnologia", "software", "informática", "telecomun",
            "digital", "dados", "ia", "inteligênc", "programação",
            "web", "desenvolvimento", "tech", "it "
        ],
        "Serviços": [
            "serviço", "consultoria", "assessoria", "administrativo",
            "financeiro", "bancário", "seguros", "educação", "saúde",
            "hotelaria", "gastronomia", "turismo", "lazer"
        ],
    }

    for macro, words in keywords.items():
        for word in words:
            if word in sector:
                return macro

    return "Serviços"  # fallback
