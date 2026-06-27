import os
import sys
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ================================
# Carregar variáveis de ambiente
# ================================
load_dotenv()

# ================================
# Configurações de diretório
# ================================
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ARQUIVO_SAIDA = DATA_DIR / "indicadores_economicos.csv"

# =====================================
# Mapeamento dos indicadores e códigos
# =====================================
INDICADORES_SGS = {
    "IPCA": 433,
    "SELIC": 432,
    "PIB": 4380,
    "DÓLAR": 1,
    "COMMODITIES": 22795,
    "IGP-M": 189,
}

# =====================
# Função para coletar indicadores
# ======================
def coletar_indicadores_bacen(indicadores: dict, n_ultimos: int = 20) -> pd.DataFrame:
    """
    Coleta os últimos 'n_ultimos' registros de cada série do SGS (BACEN).
    """
    todos_dados = []

    for nome, codigo in indicadores.items():
        # CORREÇÃO: Atribuição correta da variável url
        url = (
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}"
            f"/dados/ultimos/{n_ultimos}?formato=json"
        )

        print(f"Coletando indicador '{nome}' (código {codigo})...")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status() # Verifica se houve erro HTTP
            dados = response.json()
        except Exception as e:
            print(f"Erro ao buscar {nome} (código {codigo}): {e}")
            continue

        if not dados:
            print(f"Nenhum dado retornado para {nome}.")
            continue

        df = pd.DataFrame(dados)

        if "valor" not in df.columns or "data" not in df.columns:
            print(f"Estrutura inesperada para {nome}: {df.columns.tolist()}")
            continue

        # Limpeza e conversão
        df["valor"] = (
            df["valor"]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df.dropna(subset=["valor"], inplace=True)

        if df.empty:
            print(f"Após conversão, não há valores numéricos para {nome}")
            continue

        df["indicador"] = nome
        df["data_coleta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        todos_dados.append(df)

    # CORREÇÃO: O processamento final deve ser FORA do loop 'for'
    if not todos_dados:
        print("Nenhum indicador pôde ser coletado.")
        return pd.DataFrame(columns=["data", "valor", "indicador", "data_coleta"])
    
    df_final = pd.concat(todos_dados, ignore_index=True)
    return df_final

# =========
# Execução principal (FORA da função anterior)
# =========
def main():
    df_indicadores = coletar_indicadores_bacen(INDICADORES_SGS, n_ultimos=20)

    if df_indicadores.empty:
        print("Nenhum dado consolidado para salvar.")
        return
    
    try:
        # Salva em CSV (encoding utf-8-sig é bom para Excel em PT-BR)
        df_indicadores.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")
        print(f"\nSucesso! Arquivo salvo em: {ARQUIVO_SAIDA}")
        print(f"Total de registros: {len(df_indicadores)}")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()