from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.Pipelines.rais.download_rais import download_rais_year
from src.Pipelines.rais.build_rais_agg_parquet import build_agg
from src.Pipelines.rais.publish_to_bigquery import publish_rais_to_bigquery

LOGGER = logging.getLogger(__name__)

REGIOES = ["NORTE", "NORDESTE", "SUDESTE", "SUL", "CENTRO_OESTE"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pipeline RAIS (download -> agg -> publish)")
    p.add_argument(
        "--anos",
        nargs="+",
        type=int,
        required=True,
        help="Lista de anos, ex: --anos 2020 2021 2022",
    )
    p.add_argument(
        "--somente-regioes",
        nargs="*",
        default=None,
        help="Opcional: limitar regiões, ex: --somente-regioes SUL SUDESTE",
    )
    p.add_argument(
        "--ftp-limit",
        type=int,
        default=1,
        help="Quantos arquivos baixar por região (1 é seguro; aumente quando tiver certeza).",
    )
    return p.parse_args()


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    setup_logging()
    args = parse_args()

    regioes = args.somente_regioes if args.somente_regioes else REGIOES
    LOGGER.info(f"Regiões: {', '.join(regioes)}")
    LOGGER.info(f"Anos: {args.anos}")

    for ano in args.anos:
        for reg in regioes:
            LOGGER.info(f"==== RAIS {ano} | {reg} ====")

            # download via FTP (filtra pelo texto, exemplo: "VINC" + região)
            # você já está baixando VINC por região, então usamos filtro "VINC" e depois escolhemos o arquivo certo.
            # Como seu downloader aceita filename_filter, passe a região ou "VINC". Aqui usamos "VINC" para pegar o arquivo de vínculos.
            download_rais_year(
                ano,
                ftp_filter=f"RAIS_VINC_PUB_{reg}",
                ftp_limit=1,
            )

            # agrega usando a tag da região (ex.: CENTRO_OESTE)
            build_agg(ano, reg)

    # publica tudo que estiver em data/processed/rais/agg_parquet/**
    LOGGER.info("==== PUBLICANDO PARA BIGQUERY (RAW -> GOLD) ====")
    publish_rais_to_bigquery(base_dir=Path("data/processed/rais/agg_parquet"))

    LOGGER.info("✅ Pipeline RAIS concluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
