# streamlit/helpers.py

import json
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# Funções de carregamento de dados
# ============================================================

@st.cache_data
def carregar_relatorio_md(caminho: Path) -> str:
    """Carrega relatório markdown com tratamento de erros."""
    if caminho.exists():
        try:
            return caminho.read_text(encoding="utf-8")
        except Exception as e:
            return f"Erro ao ler o relatório: {e}"
    return "Relatório não encontrado. Execute a análise dos agentes primeiro."


@st.cache_data
def carregar_csv(caminho: Path) -> pd.DataFrame | str:
    """Carrega CSV com validação e tratamento de erros."""
    if not caminho.exists():
        return f"Arquivo {caminho.name} não encontrado."
    try:
        df = pd.read_csv(caminho)
        if df.empty:
            return f"Arquivo {caminho.name} está vazio."
        return df
    except pd.errors.EmptyDataError:
        return f"Arquivo {caminho.name} não contém dados para parsear."
    except Exception as e:
        return f"Erro ao carregar {caminho.name}: {e}"


# ============================================================
# Helpers de UI - Seções padronizadas
# ============================================================

def render_secao_entrada(titulo: str = "Entrada"):
    """Renderiza cabeçalho de seção de entrada."""
    st.markdown(f"### {titulo}")
    st.caption("Configure os parâmetros abaixo")


def render_secao_contexto(titulo: str = "Contexto"):
    """Renderiza cabeçalho de seção de contexto."""
    st.markdown(f"### {titulo}")
    st.caption("Informações e dados disponíveis")


def render_secao_saida(titulo: str = "Saída"):
    """Renderiza cabeçalho de seção de saída."""
    st.markdown(f"### {titulo}")
    st.caption("Resultados da análise")


# ============================================================
# Helpers de gráficos
# ============================================================

def criar_grafico_linha_neon(
    df: pd.DataFrame,
    x: str,
    y: str,
    titulo: str,
    cor: str = "#22c55e"
) -> go.Figure:
    """Cria gráfico de linha com estilo neon."""
    fig = px.line(df, x=x, y=y, title=titulo, markers=False)

    fig.update_traces(line=dict(color=cor, width=2.5))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#020617",
        font=dict(color="#e5e7eb"),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(showgrid=False, zeroline=False, showline=False),
        yaxis=dict(showgrid=False, zeroline=False, showline=False),
    )

    return fig


def criar_grafico_area_neon(
    df: pd.DataFrame,
    x: str,
    y: str,
    titulo: str,
    cor: str = "#22c55e"
) -> go.Figure:
    """Cria gráfico de área com estilo neon."""
    fig = px.area(df, x=x, y=y, title=titulo)

    fig.update_traces(
        line=dict(color=cor, width=2.0),
        fillcolor=f"rgba({int(cor[1:3], 16)},{int(cor[3:5], 16)},{int(cor[5:7], 16)},0.15)",
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#020617",
        font=dict(color="#e5e7eb"),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(showgrid=False, zeroline=False, showline=False),
        yaxis=dict(showgrid=False, zeroline=False, showline=False),
    )

    return fig


# ============================================================
# Helpers de processamento de dados
# ============================================================

def detectar_coluna_data(df: pd.DataFrame) -> Tuple[Optional[str], pd.DataFrame]:
    """Detecta e converte coluna de data em DataFrame."""
    candidatos = ["Unnamed: 0", "data", "Data", "Date", "date"]

    for candidato in candidatos:
        if candidato in df.columns:
            conv = pd.to_datetime(df[candidato], errors="coerce")
            if conv.notna().any():
                df_novo = df.copy()
                df_novo["data_plot"] = conv
                return candidato, df_novo

    return None, df


def preparar_dados_acao(df: pd.DataFrame, ticker: str) -> Tuple[Optional[pd.DataFrame], str]:
    """Prepara dados de ação para visualização."""
    df_ticker = df[df["ticker"] == ticker].copy()

    date_col, df_ticker = detectar_coluna_data(df_ticker)

    if date_col is None:
        return None, "Não foi possível identificar a coluna de data."

    df_ticker = df_ticker.dropna(subset=["data_plot"])
    df_ticker = df_ticker.sort_values("data_plot")

    if "fechamento" not in df_ticker.columns or df_ticker.empty:
        return None, f"Não há dados de fechamento válidos para {ticker}."

    return df_ticker, ""


def preparar_dados_indicador(df: pd.DataFrame, indicador: str) -> Tuple[Optional[pd.DataFrame], str]:
    """Prepara dados de indicador para visualização."""
    df_plot = df[df["indicador"] == indicador].copy()

    if df_plot.empty:
        return None, f"Não há dados para o indicador '{indicador}'."

    if not pd.api.types.is_numeric_dtype(df_plot["valor"]):
        df_plot["valor"] = pd.to_numeric(df_plot["valor"], errors="coerce")
        df_plot = df_plot.dropna(subset=["valor"])

    if df_plot.empty:
        return None, f"Não há valores numéricos válidos para '{indicador}'."

    df_plot = df_plot.sort_values("data")

    return df_plot, ""


# ============================================================
# Helpers de histórico
# ============================================================

def render_historico_com_acoes(
    historico_key: str,
    titulo: str = "Histórico de Consultas",
    permitir_download: bool = True
):
    """Renderiza histórico com botões de ação."""
    if historico_key not in st.session_state:
        st.session_state[historico_key] = []

    historico = st.session_state[historico_key]

    if not historico:
        st.info("Nenhuma consulta no histórico ainda.")
        return

    with st.expander(f"{titulo} ({len(historico)} itens)", expanded=False):
        col1, col2 = st.columns([3, 1])

        with col2:
            if st.button("Limpar Histórico", key=f"limpar_{historico_key}", type="secondary"):
                st.session_state[historico_key] = []
                st.rerun()

            if permitir_download and historico:
                dados_json = json.dumps(historico, ensure_ascii=False, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=dados_json,
                    file_name=f"{historico_key}.json",
                    mime="application/json",
                    key=f"download_{historico_key}"
                )

        st.divider()

        for i, item in enumerate(reversed(historico)):
            st.markdown(f"**#{len(historico) - i}**")
            for chave, valor in item.items():
                if isinstance(valor, str) and len(valor) > 200:
                    st.text_area(f"{chave}:", valor[:200] + "...", key=f"{historico_key}_{i}_{chave}", height=100, disabled=True)
                else:
                    st.text(f"{chave}: {valor}")
            if i < len(historico) - 1:
                st.markdown("---")


def adicionar_ao_historico(historico_key: str, item: dict):
    """Adiciona item ao histórico."""
    if historico_key not in st.session_state:
        st.session_state[historico_key] = []

    st.session_state[historico_key].append(item)


# ============================================================
# Helpers de sidebar
# ============================================================

def render_info_sidebar(data_dir: Path):
    """Renderiza informações do sistema na sidebar."""
    st.sidebar.divider()
    st.sidebar.markdown("### Status do Sistema")

    arquivos = {
        "Relatório Agentes": data_dir / "relatorio_indicacao_acoes.md",
        "Ações": data_dir / "top_10_acoes.csv",
        "Indicadores": data_dir / "indicadores_economicos.csv",
        "Notícias": data_dir / "noticias_investimentos.csv",
    }

    for nome, caminho in arquivos.items():
        if caminho.exists():
            st.sidebar.success(f"{nome}: OK")
        else:
            st.sidebar.error(f"{nome}: Não encontrado")

    st.sidebar.divider()
    st.sidebar.caption(f"Atualizado: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")


def render_menu_navegacao() -> str:
    """Renderiza menu de navegação na sidebar e retorna página selecionada."""
    st.sidebar.title("Navegação")

    paginas = {
        "Home": "Dashboard Principal",
        "Análise Agentes": "Relatório CrewAI",
        "Ações": "Análise de Ações",
        "Indicadores": "Indicadores Econômicos",
        "Notícias": "Notícias do Mercado",
        "Chat": "Assistente IA"
    }

    pagina = st.sidebar.radio(
        "Selecione a página:",
        list(paginas.keys()),
        format_func=lambda x: f"{x}",
        key="navegacao_principal"
    )

    st.sidebar.caption(paginas[pagina])

    return pagina


# ============================================================
# Helpers de alertas e status
# ============================================================

def render_status_arquivo(caminho: Path, nome: str = "Arquivo"):
    """Renderiza status de arquivo com ícone."""
    if caminho.exists():
        st.success(f"{nome} carregado com sucesso")
        return True
    else:
        st.error(f"{nome} não encontrado: {caminho.name}")
        return False


def render_metrica_card(titulo: str, valor: str, descricao: str = "", delta: str = None):
    """Renderiza card de métrica estilizado."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(label=titulo, value=valor, delta=delta, help=descricao)