# scripts/noticias.py

import os
import sys
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin  # Melhor para lidar com links

# ====================================
# Configurações de diretório e arquivo de saída
# ====================================

# Diretório raiz do projeto
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ARQUIVO_SAIDA = DATA_DIR / "noticia_investimentos.csv"

# ============================
# Parâmetros de scraping
# ============================

PALAVRAS_CHAVE = [
    "ipca", "inflação", "selic", "juros", "bovespa", "ações", "investimentos", 
    "bolsa", "ibovespa", "economia", "mercado", "taxa básica", "taxa de juros"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    )
}

SITES = {
    "CNN Brasil": "https://www.cnnbrasil.com.br/economia/",
    "G1 Economia": "https://g1.globo.com/economia/",
    "InfoMoney Mercados": "https://www.infomoney.com.br/mercados/",
    "Exame Economia": "https://exame.com/economia/"
}

# ===========
# Funções auxiliares
# ===========

def filtrar_noticias(html: str, base_url: str, fonte: str) -> list[dict]:
    """
    Recebe o HTML, filtra links por palavras-chave e retorna lista de dicionários.
    """
    # CORREÇÃO: soup.find_all (com underline)
    soup = BeautifulSoup(html, "html.parser")
    encontrados: list[dict] = []

    for a in soup.find_all("a", href=True):
        titulo = a.get_text().strip()
        titulo_lower = titulo.lower()
        link = a["href"].strip()

        # Ignorar títulos vazios ou muito curtos
        if not titulo or len(titulo) < 15:
            continue

        # CORREÇÃO: Adicionado dois-pontos (:) ao final do if
        if not any(palavra in titulo_lower for palavra in PALAVRAS_CHAVE):
            continue

        # Normalizar link usando urljoin (mais seguro que rstrip)
        link_completo = urljoin(base_url, link)

        # CORREÇÃO: Verificar se começa com http (estava repetido http:// no seu código)
        if not (link_completo.startswith("http://") or link_completo.startswith("https://")):
            continue

        encontrados.append({
            "titulo": titulo,
            "link": link_completo,
            "fonte": fonte,
            "data_coleta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    return encontrados

# ================
# Execução Principal
# ================
def main():
    noticias_totais: list[dict] = []

    # CORREÇÃO: SITES.items() (faltavam os parênteses)
    for nome_site, url in SITES.items():
        print(f"Coletando notícias de: {nome_site}...")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"Erro de conexão ao acessar {nome_site}: {e}")
            continue

        try:
            # Usamos a URL original como base para links relativos
            encontrados = filtrar_noticias(resp.text, url, nome_site)
            print(f"-> Encontradas {len(encontrados)} notícias relevantes.")
            noticias_totais.extend(encontrados)
        except Exception as e:
            print(f"Erro ao processar HTML de {nome_site}: {e}")
            continue

    if not noticias_totais:
        print("\nNenhuma notícia encontrada com os filtros atuais.")
        return

    # Criar DataFrame e remover duplicadas
    df = pd.DataFrame(noticias_totais)
    antes = len(df)
    # Remove duplicadas baseadas no título (mais comum em portais de notícias)
    df = df.drop_duplicates(subset=["titulo"])
    depois = len(df)

    print(f"\nResumo: Removidas {antes - depois} duplicatas. Total Final: {depois} notícias.")

    try:
        df.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")
        print(f"Sucesso! Arquivo salvo em: {ARQUIVO_SAIDA}")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()