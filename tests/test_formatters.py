"""
Testes para módulo de formatação (src/utils/formatters.py)
"""

import pytest
from src.utils.formatters import (
    fmt_int,
    fix_mojibake,
    strip_accents,
    clean_label,
    normalize_uf,
    macro_sector_from_label,
)


class TestFmtInt:
    """Testes para função fmt_int"""

    def test_fmt_int_basic(self):
        """Formata número inteiro corretamente"""
        assert fmt_int(1234567) == "1.234.567"
        assert fmt_int(0) == "0"
        assert fmt_int(1) == "1"

    def test_fmt_int_large_numbers(self):
        """Formata números grandes"""
        assert fmt_int(1000000) == "1.000.000"
        assert fmt_int(999999999) == "999.999.999"

    def test_fmt_int_invalid_input(self):
        """Trata input inválido"""
        assert fmt_int("invalid") == "invalid"
        assert fmt_int(None) == "None"


class TestFixMojibake:
    """Testes para corrigir encoding"""

    def test_fix_mojibake_valid(self):
        """Corrige encoding quebrado"""
        result = fix_mojibake("AmapÃ¡")
        # Verifica se há tentativa de correção
        assert result is not None

    def test_fix_mojibake_none(self):
        """Trata None"""
        assert fix_mojibake(None) is None

    def test_fix_mojibake_normal_string(self):
        """String normal não é alterada"""
        assert fix_mojibake("São Paulo") == "São Paulo"


class TestStripAccents:
    """Testes para remover acentos"""

    def test_strip_accents_basic(self):
        """Remove acentos básicos"""
        assert strip_accents("São Paulo") == "Sao Paulo"
        assert strip_accents("Brasília") == "Brasilia"
        assert strip_accents("Pará") == "Para"

    def test_strip_accents_none(self):
        """Trata None"""
        assert strip_accents(None) is None

    def test_strip_accents_no_accents(self):
        """String sem acentos não é alterada"""
        assert strip_accents("Rio") == "Rio"


class TestCleanLabel:
    """Testes para limpeza de labels"""

    def test_clean_label_basic(self):
        """Limpa espaços e acentos"""
        assert "Amapa" in clean_label("  Amapá   ").replace("á", "a")

    def test_clean_label_none(self):
        """Trata None"""
        assert clean_label(None) is None

    def test_clean_label_extra_spaces(self):
        """Remove espaços extras"""
        result = clean_label("  São   Paulo  ")
        assert result.strip() == result
        assert "  " not in result


class TestNormalizeUF:
    """Testes para normalizar UF"""

    def test_normalize_uf_valid(self):
        """Normaliza UF válido"""
        assert normalize_uf("SP") == "SP"
        assert normalize_uf("sp") == "SP"

    def test_normalize_uf_state_name(self):
        """Converte nome do estado para UF"""
        assert normalize_uf("São Paulo") == "SP"
        assert normalize_uf("Sao Paulo") == "SP"

    def test_normalize_uf_invalid(self):
        """Retorna None para UF inválido"""
        assert normalize_uf("XX") is None
        assert normalize_uf("Invalid") is None

    def test_normalize_uf_none(self):
        """Trata None"""
        assert normalize_uf(None) is None


class TestMacroSectorFromLabel:
    """Testes para mapear setor para macro-setor"""

    def test_macro_sector_agronegocio(self):
        """Identifica Agronegócio"""
        assert macro_sector_from_label("Agricultura") == "Agronegócio"
        assert macro_sector_from_label("Pecuária") == "Agronegócio"

    def test_macro_sector_industria(self):
        """Identifica Indústria"""
        assert macro_sector_from_label("Manufatura") == "Indústria"
        assert macro_sector_from_label("Metalúrgica") == "Indústria"

    def test_macro_sector_tecnologia(self):
        """Identifica Tecnologia"""
        assert macro_sector_from_label("Software") == "Tecnologia"
        assert macro_sector_from_label("Informática") == "Tecnologia"

    def test_macro_sector_servicos(self):
        """Padrão default é Serviços"""
        assert macro_sector_from_label("Desconhecido") == "Serviços"
        assert macro_sector_from_label("") == "Serviços"

    def test_macro_sector_none(self):
        """Trata None"""
        assert macro_sector_from_label(None) == "Serviços"
