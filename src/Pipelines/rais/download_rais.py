from __future__ import annotations

import re
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

import requests
import py7zr
from ftplib import FTP


GOVBR_INDEX_URL = (
    "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/"
    "microdados-rais-e-caged"
)

# FTP público historicamente usado para microdados (a página do gov.br menciona o modelo via FTP)
FTP_HOST = "ftp.mtps.gov.br"
FTP_BASE_DIR = "/pdet/microdados/RAIS"  # dentro daqui costuma haver pastas por ano

DEFAULT_RAW_DIR = Path("data/raw/rais")


@dataclass
class DownloadResult:
    year: int
    downloaded_files: List[Path]
    extracted_dir: Optional[Path] = None


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _find_archive_links(html: str) -> list[str]:
    """
    Captura links que contenham .zip/.7z/.rar mesmo que tenham querystring (ex: .zip?download=1).
    """
    pattern = r'href="([^"]*(?:\.zip|\.7z|\.rar)(?:[^"]*)?)"'
    links = re.findall(pattern, html, flags=re.IGNORECASE)
    return [l.replace("&amp;", "&") for l in links]


def _pick_link_for_year(links: list[str], year: int) -> Optional[str]:
    y = str(year)
    candidates = [l for l in links if y in l]
    if not candidates:
        return None
    # escolhe o link "mais curto" como heurística simples
    return sorted(candidates, key=len)[0]


def _download_http_file(url: str, dest: Path, timeout: int = 120) -> Path:
    _ensure_dir(dest.parent)
    print(f"⬇️  Baixando via HTTP: {url}")
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"✅ Salvo em: {dest}")
    return dest


def _ftp_list_files(year: int) -> list[str]:
    """
    Lista arquivos disponíveis no FTP para o ano.
    """
    year_dir = f"{FTP_BASE_DIR}/{year}"
    print(f"🔎 Conectando no FTP para listar: ftp://{FTP_HOST}{year_dir}/")

    ftp = FTP(FTP_HOST, timeout=60)
    ftp.login()  # anônimo
    ftp.cwd(year_dir)

    files = ftp.nlst()
    ftp.quit()
    return files



def _ftp_download_files(year: int, out_dir: Path, filename_filter: Optional[str] = None, limit: Optional[int] = None) -> list[Path]:
    """
    Baixa arquivos do FTP. Voce pode filtrar por texto (filename_filter) e limitar quantidade (limit).
    """
    year_dir = f"{FTP_BASE_DIR}/{year}"
    target_dir = out_dir / f"ano={year}" / "ftp"
    _ensure_dir(target_dir)

    ftp: Optional[FTP] = None
    try:
        ftp = FTP(FTP_HOST, timeout=120)
        ftp.login()
        ftp.cwd(year_dir)

        files = ftp.nlst()
        if filename_filter:
            files = [f for f in files if filename_filter.lower() in f.lower()]

        if limit is not None:
            files = files[:limit]

        if not files:
            raise RuntimeError(f"Nenhum arquivo encontrado no FTP para ano={year} com filtro={filename_filter!r}.")

        print(f"Arquivos encontrados ({len(files)}). Vou baixar {len(files)} arquivo(s).")
        downloaded: list[Path] = []

        for fname in files:
            dest = target_dir / fname
            if dest.exists():
                print(f"Arquivo ja existe, pulando download: {dest}")
                downloaded.append(dest)
            else:
                for attempt in range(1, 4):
                    try:
                        print(f"FTP download: {fname}")
                        with open(dest, "wb") as f:
                            ftp.retrbinary(f"RETR {fname}", f.write)
                        downloaded.append(dest)
                        print(f"Salvo: {dest}")
                        break
                    except Exception:
                        if attempt >= 3:
                            raise
                        print(f"FTP falhou, tentativa {attempt}/3")
                        time.sleep(5)

            if dest.suffix.lower() == ".7z":
                expected_txt = dest.with_suffix(".txt")
                if expected_txt.exists():
                    print(f"TXT ja existe, pulando extracao: {expected_txt}")
                else:
                    start_time = time.time()
                    print(f"Extraindo 7z: {dest}")
                    with py7zr.SevenZipFile(dest, "r") as archive:
                        archive.extractall(path=dest.parent)

                    region_hint = dest.stem.replace("RAIS_VINC_PUB_", "")
                    txt_candidates = sorted(dest.parent.glob("*.txt"))
                    preferred = None
                    for candidate in txt_candidates:
                        name = candidate.name.upper()
                        if dest.stem.upper() in name or region_hint.upper() in name:
                            preferred = candidate
                            break

                    if preferred is None:
                        recent = [c for c in txt_candidates if c.stat().st_mtime >= start_time]
                        if len(recent) == 1:
                            preferred = recent[0]

                    if preferred is None:
                        raise RuntimeError(f"Nao foi possivel identificar o .txt extraido de {dest}")

                    extracted_txt = preferred
                    if extracted_txt != expected_txt:
                        if expected_txt.exists():
                            expected_txt.replace(expected_txt.with_suffix(".txt.bak"))
                        extracted_txt.replace(expected_txt)
                        extracted_txt = expected_txt

                    print(f"Extraido: {extracted_txt}")
    finally:
        if ftp is not None:
            try:
                ftp.quit()
            except Exception:
                pass

    return downloaded


def download_rais_year(
    year: int,
    out_dir: Path = DEFAULT_RAW_DIR,
    timeout: int = 120,
    ftp_filter: Optional[str] = None,
    ftp_limit: Optional[int] = 1,
) -> DownloadResult:
    """
    Estratégia:
    1) tenta achar um arquivo compactado (zip/7z/rar) no HTML do gov.br
    2) se não achar, cai para FTP e baixa (por padrão, 1 arquivo para teste)
    """
    year_dir = out_dir / f"ano={year}"
    _ensure_dir(year_dir)

    print(f"🔎 Buscando links de RAIS no gov.br… ({GOVBR_INDEX_URL})")
    resp = requests.get(GOVBR_INDEX_URL, timeout=timeout)
    resp.raise_for_status()

    links = _find_archive_links(resp.text)
    link = _pick_link_for_year(links, year)

    downloaded_files: list[Path] = []
    extracted_dir: Optional[Path] = None

    if link:
        # normaliza URL relativa
        if link.startswith("/"):
            link = "https://www.gov.br" + link

        # baixa
        ext = Path(urlparse(link).path).suffix.lower() or ".bin"
        archive_path = year_dir / f"rais_{year}{ext}"
        downloaded_files.append(_download_http_file(link, archive_path, timeout=timeout))

        # se for zip, extrai (7z/rar exigiriam libs extras, deixamos só baixar)
        if archive_path.suffix.lower() == ".zip":
            extracted_dir = year_dir / "extracted"
            _ensure_dir(extracted_dir)
            print("📦 Extraindo ZIP…")
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(extracted_dir)
            print(f"✅ Extraído em: {extracted_dir}")

        return DownloadResult(year=year, downloaded_files=downloaded_files, extracted_dir=extracted_dir)

    # fallback FTP
    print("ℹ️ Não encontrei link .zip/.7z/.rar no HTML. Vou tentar via FTP (automático).")
    downloaded_files = _ftp_download_files(
        year=year,
        out_dir=out_dir,
        filename_filter=ftp_filter,
        limit=ftp_limit,
    )
    return DownloadResult(year=year, downloaded_files=downloaded_files, extracted_dir=None)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m src.Pipelines.rais.download_rais <ANO>")
        sys.exit(1)

    year = int(sys.argv[1])
    # padrão: baixa só 1 arquivo no FTP para teste (evita peso)
    download_rais_year(year)
