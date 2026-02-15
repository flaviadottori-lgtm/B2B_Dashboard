# src/Pipelines/caged/download_caged_xlsx.py
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urljoin

import requests

# =========================
# Config
# =========================
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "raw" / "caged" / "caged_xlsx"
OUT.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
        )
    }
)

MESES = [
    "janeiro",
    "fevereiro",
    "marco",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]


@dataclass(frozen=True)
class MonthRef:
    year: int
    month: int  # 1..12

    @property
    def yyyymm(self) -> str:
        return f"{self.year}{self.month:02d}"

    @property
    def mes_nome(self) -> str:
        return MESES[self.month - 1]

    def out_name(self) -> str:
        # padrão de nome consistente no seu projeto
        return f"novo_caged_{self.year}_{self.month:02d}.xlsx"


# =========================
# Helpers
# =========================
def http_get(url: str, *, timeout: int = 30, retries: int = 4) -> requests.Response:
    last_exc = None
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, timeout=timeout)
            # 503/502/504: tenta novamente
            if resp.status_code in (502, 503, 504):
                wait = 1.5 * (attempt + 1)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_exc = e
            wait = 1.5 * (attempt + 1)
            time.sleep(wait)
    raise last_exc  # type: ignore


def looks_like_html(head_bytes: bytes) -> bool:
    b = head_bytes.lstrip().lower()
    return b.startswith(b"<!doctype html") or b.startswith(b"<html") or b.startswith(b"<!")


def find_tables_link_in_html(page_url: str, html: str) -> Optional[str]:
    """
    Procura um link que pareça ser o arquivo de Tabelas (.xls/.xlsx) no HTML.
    Aceita tanto links diretos quanto links .../view (conteúdo do gov.br).
    """
    # captura todos href
    hrefs = re.findall(r'href="([^"]+)"', html, flags=re.IGNORECASE)

    # prioriza “tabelas” e extensões
    candidates = []
    for h in hrefs:
        h_low = h.lower()
        if "tabela" in h_low or "tabelas" in h_low:
            if (".xls" in h_low) or (".xlsx" in h_low) or ("/view" in h_low):
                candidates.append(h)

    # fallback: alguns portais escrevem "3-tabelas" no link
    if not candidates:
        for h in hrefs:
            h_low = h.lower()
            if "3-tabelas" in h_low and (".xls" in h_low or ".xlsx" in h_low or "/view" in h_low):
                candidates.append(h)

    if not candidates:
        return None

    # pega o mais promissor: primeiro que contenha "tabelas" + xls/xlsx
    def score(u: str) -> int:
        ul = u.lower()
        s = 0
        if "tabelas" in ul:
            s += 5
        if "3-" in ul or "3." in ul or "3tabel" in ul:
            s += 2
        if ".xlsx" in ul:
            s += 2
        if ".xls" in ul:
            s += 1
        if "/view" in ul:
            s += 1
        return s

    best = sorted(candidates, key=score, reverse=True)[0]
    return urljoin(page_url, best)


def normalize_download_url(u: str) -> str:
    """
    No gov.br, frequentemente:
    - link vem como .../arquivo.xlsx/view
      e o download real é .../arquivo.xlsx/@@download/file
    """
    if u.endswith("/view"):
        return u.replace("/view", "/@@download/file")
    return u


def download_file(url: str, out_path: Path) -> bool:
    """
    Faz download e valida se não veio HTML.
    Retorna True se sucesso.
    """
    r = http_get(url, timeout=60, retries=5)

    # valida conteúdo (primeiros bytes)
    head = r.content[:256]
    if looks_like_html(head):
        return False

    out_path.write_bytes(r.content)
    return True


# =========================
# Single-competencia helper
# =========================
def download_competencia(year: int, month: int, out_dir: Optional[Path] = None) -> Path:
    """
    Download a single competencia XLSX into the raw directory.
    Returns the output path on success.
    """
    target_dir = out_dir or OUT
    target_dir.mkdir(parents=True, exist_ok=True)

    ref = MonthRef(year=year, month=month)
    out_path = target_dir / ref.out_name()

    if out_path.exists() and out_path.stat().st_size > 50_000:
        print(f"OK: already exists {out_path.name}")
        return out_path

    dl = resolve_tables_download_url(ref)
    if not dl:
        raise RuntimeError(f"No tables link found for {year}-{month:02d}")

    ok = download_file(dl, out_path)
    if not ok:
        if out_path.exists():
            out_path.unlink(missing_ok=True)
        raise RuntimeError(f"Download returned HTML for {year}-{month:02d}")

    return out_path


# =========================
# URL patterns (tentativas)
# =========================
def candidate_month_pages(ref: MonthRef) -> Iterable[str]:
    """
    Tenta padrões reais do portal (mudam por ano).
    1) 2025 costuma estar em /novo-caged/2025/<mes>/
    2) 2024 costuma estar em /novo-caged/novo-caged-2024/<mes>/
    3) 2023 costuma estar em /novo-caged/novo-caged-2023/<mes>/
    4) fallback: página “novo-caged-<mes>-<ano>” (às vezes existe, mas pode ter link quebrado)
    """
    base = "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/novo-caged/"
    mes = ref.mes_nome

    yield f"{base}{ref.year}/{mes}"
    yield f"{base}novo-caged-{ref.year}/{mes}"
    yield f"{base}novo-caged-{ref.year}/novo-caged-{mes}-{ref.year}"
    # também tenta sem mês (caso exista pasta por competência)
    yield f"{base}novo-caged-{ref.year}/{ref.yyyymm}"


def resolve_tables_download_url(ref: MonthRef) -> Optional[str]:
    """
    Abre as páginas candidatas do mês e tenta achar o link de Tabelas.
    Se achar, normaliza para URL de download.
    """
    for page in candidate_month_pages(ref):
        try:
            resp = http_get(page, timeout=30, retries=3)
        except Exception:
            continue

        link = find_tables_link_in_html(page, resp.text)
        if not link:
            continue

        dl = normalize_download_url(link)
        return dl

    return None


# =========================
# Main
# =========================
def main(year_start: int = 2024, year_end: int = 2025):
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"📁 Pasta: {OUT}")

    for year in range(year_start, year_end + 1):
        for m in range(1, 13):
            ref = MonthRef(year=year, month=m)
            out_path = OUT / ref.out_name()

            if out_path.exists() and out_path.stat().st_size > 50_000:
                print(f"✅ Já existe: {ref.year}/{ref.mes_nome}")
                continue

            print(f"⬇️  {ref.year}/{ref.mes_nome}: procurando link…")
            dl = resolve_tables_download_url(ref)

            if not dl:
                print(f"⚠️  Sem link de Tabelas na página: {ref.year}/{ref.mes_nome}")
                continue

            print(f"   🔗 {dl}")
            try:
                ok = download_file(dl, out_path)
                if not ok:
                    # se veio HTML, apaga e marca falha
                    if out_path.exists():
                        out_path.unlink(missing_ok=True)
                    print(f"❌ {ref.year}/{ref.mes_nome}: veio HTML (bloqueio/redirecionamento).")
                    continue

                print(
                    f"✅ OK: {ref.year}/{ref.mes_nome} -> {out_path.name} ({out_path.stat().st_size/1e6:.2f} MB)"
                )

            except Exception as e:
                if out_path.exists():
                    out_path.unlink(missing_ok=True)
                print(f"⚠️  Falhou {ref.year}/{ref.mes_nome}: {e}")

    print("🏁 Fim.")


if __name__ == "__main__":
    # Por padrão: baixa 2024-2025 (mais estável). Ajuste se quiser.
    main(2024, 2025)
