import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def mapa_uf_com_valor(
    scores_df: pd.DataFrame,
    geojson_path: str = "data/geo/brazil_states.geojson",
    value_col: str = "opportunity_score",
    year: int = 2021,
    title: str = "Opportunity Score por Estado (2021)",
):
    # 1) Carregar GeoJSON
    with open(geojson_path, "r", encoding="utf-8") as f:
        geo = json.load(f)

    # 2) Filtrar ano
    df = scores_df.copy()
    if "year" in df.columns:
        df = df[df["year"] == year].copy()

    # Garantias mínimas
    needed = {"state", value_col, "units"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(
            f"Scores sem colunas necessárias: {missing}. Colunas atuais: {list(df.columns)}"
        )

    # 3) Agregar um valor por UF (média ponderada por units)
    def weighted_score(x: pd.DataFrame) -> float:
        denom = x["units"].sum()
        if denom and denom > 0:
            return float((x[value_col] * x["units"]).sum() / denom)
        return float(x[value_col].mean())

    agg = (
        df.groupby("state", as_index=False)
        .apply(weighted_score)
        .reset_index(drop=True)
        .rename(columns={0: value_col})
    )

    # 4) Descobrir qual campo no GeoJSON guarda a UF (sigla)
    possible_keys = ["sigla", "UF", "uf", "abbr", "id", "name"]
    sample_props = geo["features"][0]["properties"]
    prop_key = None
    for k in possible_keys:
        if k in sample_props:
            prop_key = k
            break
    if prop_key is None:
        raise ValueError(
            f"Não encontrei campo de UF no GeoJSON. Propriedades disponíveis: {list(sample_props.keys())}"
        )

    # 5) Mapa pintado
    # ✅ Correção do bug: usar hover_name e deixar hover_data só com o valor
    fig = px.choropleth(
        agg,
        geojson=geo,
        locations="state",
        featureidkey=f"properties.{prop_key}",
        color=value_col,
        hover_name="state",
        hover_data={value_col: ":.2f"},
        title=title,
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(template="plotly_dark", margin={"r": 0, "t": 40, "l": 0, "b": 0})

    # 6) Texto em cima (sem shapely): centroides (manual)
    centroids = {
        "AC": (-9.97499, -67.82430),
        "AL": (-9.66599, -35.73500),
        "AP": (0.03493, -51.06940),
        "AM": (-3.11903, -60.02173),
        "BA": (-12.9714, -38.5014),
        "CE": (-3.73186, -38.52667),
        "DF": (-15.7939, -47.8828),
        "ES": (-20.3155, -40.3128),
        "GO": (-16.6869, -49.2648),
        "MA": (-2.53073, -44.3068),
        "MT": (-15.6014, -56.0979),
        "MS": (-20.4697, -54.6201),
        "MG": (-19.9167, -43.9345),
        "PA": (-1.4558, -48.4902),
        "PB": (-7.1195, -34.8450),
        "PR": (-25.4284, -49.2733),
        "PE": (-8.0476, -34.8770),
        "PI": (-5.0892, -42.8016),
        "RJ": (-22.9068, -43.1729),
        "RN": (-5.7945, -35.2110),
        "RS": (-30.0346, -51.2177),
        "RO": (-8.7608, -63.8999),
        "RR": (2.8235, -60.6753),
        "SC": (-27.5954, -48.5480),
        "SP": (-23.5505, -46.6333),
        "SE": (-10.9472, -37.0731),
        "TO": (-10.1841, -48.3336),
    }

    lats, lons, texts = [], [], []
    for _, row in agg.iterrows():
        uf = row["state"]
        val = row[value_col]
        if uf in centroids and pd.notna(val):
            lat, lon = centroids[uf]
            lats.append(lat)
            lons.append(lon)
            texts.append(f"{val:.1f}")

    fig.add_trace(go.Scattergeo(lat=lats, lon=lons, text=texts, mode="text", hoverinfo="skip"))

    return fig
