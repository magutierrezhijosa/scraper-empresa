"""
Scraper de PDFs — AICA (Asociación de Empresarios de Alcobendas)

Extrae todos los enlaces a PDF desde una página web y los guarda en un CSV.
"""

import csv
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


TARGET_URL = "https://www.empresariosdealcobendas.com/sobre-aica"
CSV_OUTPUT = Path("pdfs_encontrados.csv")


def fetch_html(url: str) -> str:
    """Obtiene el HTML de la URL dada."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_pdfs(html: str, base_url: str) -> list[dict]:
    """
    Recorre el HTML buscando tags <a> que apunten a archivos .pdf
    y devuelve una lista con {titulo, url}.
    """
    soup = BeautifulSoup(html, "lxml")
    pdfs = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        # La URL puede traer query params (ej: ?hsLang=es-es)
        href_clean = href.split("?")[0].split("#")[0]

        if not href_clean.lower().endswith(".pdf"):
            continue

        # Completar URL relativa si hace falta
        full_url = urljoin(base_url, href_clean)

        # Intentar sacar el título del link:
        # 1) Texto directo del <a>
        # 2) Texto de un <div> hijo con clase que contenga "text"
        # 3) Atributo title del <a>
        # 4) Último recurso: el nombre del archivo
        titulo_candidato = a_tag.get_text(strip=True)

        if not titulo_candidato:
            inner_div = a_tag.find("div", class_=lambda c: c and "text" in c.split())
            if inner_div:
                titulo_candidato = inner_div.get_text(strip=True)

        if not titulo_candidato:
            titulo_candidato = a_tag.get("title", "")

        if not titulo_candidato:
            # Extraer nombre del archivo sin extensión
            from urllib.parse import unquote
            filename = Path(unquote(full_url.split("?")[0].split("/")[-1]))
            titulo_candidato = filename.stem.replace("_", " ").replace("-", " ").title()

        pdfs.append({
            "titulo": titulo_candidato.strip(),
            "url": full_url.split("?")[0],  # sin query params de HubSpot
        })

    return pdfs


def guardar_csv(pdfs: list[dict], ruta: Path) -> None:
    """Persiste la lista de PDFs en un archivo CSV."""
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["titulo", "url"])
        writer.writeheader()
        writer.writerows(pdfs)
    print(f"\nCSV guardado: {ruta.resolve()} ({len(pdfs)} archivos)")


def main() -> None:
    print(f"Scrapeando: {TARGET_URL}")
    html = fetch_html(TARGET_URL)

    pdfs = extract_pdfs(html, TARGET_URL)

    if not pdfs:
        print("No se encontraron PDFs en la pagina.")
        return

    print(f"\nPDFs encontrados ({len(pdfs)}):")
    print("-" * 70)
    for i, pdf in enumerate(pdfs, 1):
        print(f"  {i:2d}. {pdf['titulo']}")
        print(f"      {pdf['url']}")
    print("-" * 70)

    guardar_csv(pdfs, CSV_OUTPUT)

    # Resumen
    print(f"\nResumen:")
    print(f"  Total PDFs: {len(pdfs)}")


if __name__ == "__main__":
    main()
