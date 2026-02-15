import requests
from typing import List
import re
import os


def fetch_caged_links(year: str, month: str) -> List[str]:
    # Exemplo: busca links oficiais do gov.br para o Novo CAGED
    # (ajustar para fonte real do projeto)
    url = f"https://pdet.mte.gov.br/novo-caged"
    resp = requests.get(url)
    # Regex para encontrar links do mês/ano
    pattern = re.compile(rf"href=\"(.*?{year}{month}.*?3tabelas.*?)\"")
    links = pattern.findall(resp.text)
    return [l if l.startswith("http") else f"https://pdet.mte.gov.br{l}" for l in links]


def download_caged_file(url: str, dest: str):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
