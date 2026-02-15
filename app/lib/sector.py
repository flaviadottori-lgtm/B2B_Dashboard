from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
import re

import pandas as pd

CNAE2_MACRO_GROUPS: List[Dict[str, Any]] = [
    {"key": "agro", "min": 1, "max": 3, "range": "01-03"},
    {"key": "extrativa", "min": 5, "max": 9, "range": "05-09"},
    {"key": "industria", "min": 10, "max": 33, "range": "10-33"},
    {"key": "energia", "min": 35, "max": 35, "range": "35"},
    {"key": "saneamento", "min": 36, "max": 39, "range": "36-39"},
    {"key": "construcao", "min": 41, "max": 43, "range": "41-43"},
    {"key": "comercio", "min": 45, "max": 47, "range": "45-47"},
    {"key": "transporte", "min": 49, "max": 53, "range": "49-53"},
    {"key": "alojamento", "min": 55, "max": 56, "range": "55-56"},
    {"key": "informacao", "min": 58, "max": 63, "range": "58-63"},
    {"key": "financas", "min": 64, "max": 66, "range": "64-66"},
    {"key": "imobiliario", "min": 68, "max": 68, "range": "68"},
    {"key": "profissionais", "min": 69, "max": 75, "range": "69-75"},
    {"key": "administrativas", "min": 77, "max": 82, "range": "77-82"},
    {"key": "publico", "min": 84, "max": 84, "range": "84"},
    {"key": "educacao", "min": 85, "max": 85, "range": "85"},
    {"key": "saude", "min": 86, "max": 88, "range": "86-88"},
    {"key": "artes", "min": 90, "max": 93, "range": "90-93"},
    {"key": "outros_servicos", "min": 94, "max": 96, "range": "94-96"},
    {"key": "domesticos", "min": 97, "max": 99, "range": "97-99"},
]

CNAE_SECAO_KEYS = {
    "A": "cnae_secao_a",
    "B": "cnae_secao_b",
    "C": "cnae_secao_c",
    "D": "cnae_secao_d",
    "E": "cnae_secao_e",
    "F": "cnae_secao_f",
    "G": "cnae_secao_g",
    "H": "cnae_secao_h",
    "I": "cnae_secao_i",
    "J": "cnae_secao_j",
    "K": "cnae_secao_k",
    "L": "cnae_secao_l",
    "M": "cnae_secao_m",
    "N": "cnae_secao_n",
    "O": "cnae_secao_o",
    "P": "cnae_secao_p",
    "Q": "cnae_secao_q",
    "R": "cnae_secao_r",
    "S": "cnae_secao_s",
    "T": "cnae_secao_t",
    "U": "cnae_secao_u",
}


def _parse_cnae2(value: Any) -> Optional[int]:
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    if len(digits) < 2:
        return None
    try:
        return int(digits[:2])
    except ValueError:
        return None


def macro_key_from_cnae2(cnae2_int: Optional[int]) -> Optional[str]:
    if cnae2_int is None:
        return None
    for group in CNAE2_MACRO_GROUPS:
        if group["min"] <= cnae2_int <= group["max"]:
            return group["key"]
    return None


def macro_label_from_key(key: str, t) -> str:
    return t(f"macro_{key}")


def macro_label_from_cnae2(cnae2_int: Optional[int], t) -> str:
    key = macro_key_from_cnae2(cnae2_int)
    if not key:
        return t("macro_outros")
    return macro_label_from_key(key, t)


def macro_label_with_range(key: str, t) -> str:
    for group in CNAE2_MACRO_GROUPS:
        if group["key"] == key:
            return f"{macro_label_from_key(key, t)} ({group['range']})"
    return macro_label_from_key(key, t)


def available_macro_keys_from_cnae2_list(cnae2_list: Iterable[Any]) -> List[str]:
    keys: List[str] = []
    for item in cnae2_list:
        key = macro_key_from_cnae2(_parse_cnae2(item))
        if key and key not in keys:
            keys.append(key)
    return keys


def secao_label(secao: str, t) -> str:
    key = CNAE_SECAO_KEYS.get(secao.upper())
    if not key:
        return secao
    return t(key)


def secao_display_label(secao: str, t) -> str:
    return f"{t('cnae_secao_prefix')} {secao} \u2014 {secao_label(secao, t)}"


def format_cnae_subclasse(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) >= 6:
        return f"{digits[:4]}-{digits[4:6]}"
    if len(digits) >= 4:
        return f"{digits[:4]}-{digits[4:]}" if len(digits) > 4 else digits
    return digits or str(value)


def add_macro_columns(
    df: pd.DataFrame,
    t,
    cnae_subclasse_col: str = "cnae_subclasse",
    cnae_secao_col: Optional[str] = None,
) -> pd.DataFrame:
    if df.empty:
        return df
    if cnae_secao_col and cnae_secao_col in df.columns:
        df["macro_key"] = df[cnae_secao_col].astype(str).str.upper()
        df["macro_label"] = df["macro_key"].apply(lambda secao: secao_display_label(secao, t))
        return df

    if cnae_subclasse_col in df.columns:
        cnae2_series = df[cnae_subclasse_col].astype(str).str.replace(r"\D", "", regex=True).str[:2]
        df["macro_key"] = cnae2_series.apply(
            lambda val: macro_key_from_cnae2(_parse_cnae2(val)) or "outros"
        )
        df["macro_label"] = df["macro_key"].apply(lambda key: macro_label_with_range(key, t))
    else:
        df["macro_key"] = "outros"
        df["macro_label"] = t("macro_outros")
    return df
