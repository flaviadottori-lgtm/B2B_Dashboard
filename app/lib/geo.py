from __future__ import annotations

import unicodedata
from typing import Tuple

import requests
import streamlit as st

GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"


def normalize_name(value: str) -> str:
    return (
        unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    )


@st.cache_data(show_spinner=False)
def load_geojson() -> dict:
    response = requests.get(GEOJSON_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def resolve_geo_feature_key(geo: dict) -> Tuple[str, str | None]:
    features = geo.get("features") or []
    if not features:
        return "", None
    props = features[0].get("properties") or {}
    prop_keys = {str(key).lower(): key for key in props.keys()}
    for candidate in ["sigla", "uf", "abbr", "abbrev"]:
        if candidate in prop_keys:
            return f"properties.{prop_keys[candidate]}", None
    for candidate in ["name", "nome", "state"]:
        if candidate in prop_keys:
            return "properties.name_norm", prop_keys[candidate]
    return "", None
