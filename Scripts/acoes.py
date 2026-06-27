import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime

# =====================================
# Configurações de diretório
# =====================================
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ARQUIVO_SAIDA = DATA_DIR / "top_10_acoes.csv"

# =====================================
# Lista das 10 ações (Exemplo das mais líquidas da B3)
# Adicionamos ".SA" para o Yahoo Finance reconhecer como B3
# =====================================
TICKERS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA",
    "BBAS3.SA", "ITSA4.SA", "B3SA3.SA", "WEGE3.SA", "HAPV3.SA"
]

def coletar_dados_acoes(tickers, periodo="60d", intervalo="1d"):
    """
    Coleta dados históricos das ações e formata conforme a imagem.
    periodo: "1mo", "3mo", "1y", etc.
    """
    lista_dfs = []

    for ticker_sa in tickers:
        print(f"Coletando dados de {ticker_sa}...")
        try:
            # Baixa os dados
            acao = yf.Ticker(ticker_sa)
            df = acao.history(period=periodo, interval=intervalo)

            if df.empty:
                print(f"Aviso: Nenhum dado encontrado para {ticker_sa}")
                continue

            # Resetar o index para a data virar uma coluna
            df = df.reset_index()

            # Selecionar e renomear colunas para o padrão da sua imagem
            # O Yahoo retorna: Date, Open, High, Low, Close, Volume...
            df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
            
            df.columns = ["data", "abertura", "alta", "baixa", "fechamento", "volume"]

            # Adicionar a coluna ticker (removendo o .SA para ficar igual à imagem)
            df["ticker"] = ticker_sa.replace(".SA", "")

            # Formatar a data para string (YYYY-MM-DD)
            df["data"] = df["data"].dt.strftime("%Y-%m-%d")

            lista_dfs.append(df)

        except Exception as e:
            print(f"Erro ao processar {ticker_sa}: {e}")

    if not lista_dfs:
        return pd.DataFrame()

    # Concatenar todos os DataFrames
    df_final = pd.concat(lista_dfs, ignore_index=True)
    return df_final

def main():
    print("Iniciando extração de dados da B3...")
    
    df_acoes = coletar_dados_acoes(TICKERS)

    if df_acoes.empty:
        print("Erro: Nenhum dado foi coletado.")
        return

    try:
        # Salvar no formato da imagem
        # O index=True (padrão) criaria aquela primeira coluna sem nome da imagem
        # Mas aqui usaremos a coluna 'data' como a primeira
        df_acoes.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8")
        print(f"\nSucesso! Arquivo '{ARQUIVO_SAIDA}' gerado com {len(df_acoes)} linhas.")
        
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

if __name__ == "__main__":
    main()