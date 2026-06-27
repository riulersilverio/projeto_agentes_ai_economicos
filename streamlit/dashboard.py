# streamlit/dashboard.py

import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from helpers import (
    carregar_relatorio_md,
    carregar_csv,
    render_secao_entrada,
    render_secao_contexto,
    render_secao_saida,
    criar_grafico_linha_neon,
    criar_grafico_area_neon,
    preparar_dados_acao,
    preparar_dados_indicador,
    render_historico_com_acoes,
    adicionar_ao_historico,
    render_info_sidebar,
    render_menu_navegacao,
    render_status_arquivo,
    render_metrica_card,
)


# ============================================================
# Configuração da página
# ============================================================
st.set_page_config(
    layout="wide",
    page_title="Painel de Análise de Investimentos",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# CSS customizado
CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #02040a;
        color: #f9fafb;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #22c55e;
    }
    .stButton>button:hover {
        background-color: #22c55e;
        color: #020617;
    }
    .metric-card {
        background-color: #050816;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #22c55e;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# Caminhos de arquivos
# ============================================================
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

ARQUIVO_RELATORIO_AGENTES = DATA_DIR / "relatorio_indicacao_acoes.md"
ARQUIVO_ACOES = DATA_DIR / "top_10_acoes.csv"
ARQUIVO_INDICADORES_ECONOMICOS = DATA_DIR / "indicadores_economicos.csv"
ARQUIVO_NOTICIAS = DATA_DIR / "noticia_investimentos.csv"

# ============================================================
# Carregar variáveis de ambiente
# ============================================================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ============================================================
# Inicialização do modelo de chat
# ============================================================
chat_model = None
if OPENAI_API_KEY:
    try:
        chat_model = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.4,
            api_key=OPENAI_API_KEY,
        )
    except Exception as e:
        st.error(f"Erro ao inicializar o modelo de chat: {e}")

# ============================================================
# Contexto do chatbot
# ============================================================
CONTEXTO_CHAT = """
Você é o "Analista Econômico Virtual", um assistente de IA especializado em economia e mercado financeiro brasileiro.

**Especialidade:**
- Economia brasileira, tendências de mercado, indicadores (IPCA, SELIC, PIB, câmbio),
- Análise de ações (foco em volume e notícias relevantes),
- Interpretação de notícias financeiras.

**Objetivo:**
Ajudar o usuário a entender o cenário econômico, responder perguntas sobre investimentos e finanças de forma clara, objetiva e consultiva.

**Contexto Econômico Atual (base para suas respostas):**
- Inflação (IPCA): tendência de desaceleração nos últimos meses.
- Taxa de Juros (SELIC): 10,75% ao ano.
- Mercado de Ações: PETR4, VALE3 e WEGE3 apresentam maiores volumes recentes.
- Cenário Macroeconômico e Notícias: atenção à alta do petróleo e discussões sobre risco fiscal no país.

**Diretrizes:**
1. Baseie-se principalmente nesse contexto ao responder.
2. Seja claro, direto e educativo.
3. Tenha abordagem consultiva, explicando cenários, riscos e potenciais.
4. Não dê ordens diretas de investimento (não diga "compre X"), foque em análise.
5. Lembre que o cenário é dinâmico e pode mudar.
6. Ao comentar notícias, foque nos impactos econômicos e nos ativos mencionados.
7. Adicione contexto relevante mesmo em perguntas simples.
"""

# ============================================================
# Estado da sessão
# ============================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "historico_acoes" not in st.session_state:
    st.session_state.historico_acoes = []

if "historico_indicadores" not in st.session_state:
    st.session_state.historico_indicadores = []


# ============================================================
# PÁGINAS
# ============================================================

def pagina_home():
    """Página principal - Dashboard com visão geral."""
    st.title("📊 Painel de Análise de Investimentos")
    st.markdown(
        "Visão consolidada do mercado financeiro com análises multiagente, "
        "dados de ações, indicadores econômicos e notícias filtradas."
    )
    st.divider()

    # Métricas rápidas
    st.subheader("Visão Rápida")
    col1, col2, col3, col4 = st.columns(4)

    df_acoes = carregar_csv(ARQUIVO_ACOES)
    df_indicadores = carregar_csv(ARQUIVO_INDICADORES_ECONOMICOS)
    df_noticias = carregar_csv(ARQUIVO_NOTICIAS)

    with col1:
        if isinstance(df_acoes, pd.DataFrame) and "ticker" in df_acoes.columns:
            num_acoes = df_acoes["ticker"].nunique()
            render_metrica_card("Ações", str(num_acoes), "Ativos monitorados")
        else:
            st.metric("Ações", "N/A")

    with col2:
        if isinstance(df_indicadores, pd.DataFrame) and "indicador" in df_indicadores.columns:
            num_indicadores = df_indicadores["indicador"].nunique()
            render_metrica_card("Indicadores", str(num_indicadores), "Métricas econômicas")
        else:
            st.metric("Indicadores", "N/A")

    with col3:
        if isinstance(df_noticias, pd.DataFrame):
            num_noticias = len(df_noticias)
            render_metrica_card("Notícias", str(num_noticias), "Artigos coletados")
        else:
            st.metric("Notícias", "N/A")

    with col4:
        relatorio_existe = ARQUIVO_RELATORIO_AGENTES.exists()
        status_relatorio = "Disponível" if relatorio_existe else "Pendente"
        render_metrica_card("Relatório IA", status_relatorio, "Análise CrewAI")

    st.divider()

    # Preview dos dados
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Últimas Ações")
        if isinstance(df_acoes, pd.DataFrame) and not df_acoes.empty:
            st.dataframe(
                df_acoes.tail(5)[["ticker", "fechamento", "volume"]],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Dados de ações não disponíveis")

    with col2:
        st.subheader("Últimos Indicadores")
        if isinstance(df_indicadores, pd.DataFrame) and not df_indicadores.empty:
            st.dataframe(
                df_indicadores.tail(5)[["indicador", "data", "valor"]],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Indicadores econômicos não disponíveis")

    st.divider()

    # Atalhos de navegação
    st.subheader("Acesso Rápido")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Ver Análise dos Agentes", use_container_width=True):
            st.session_state.navegacao_principal = "Análise Agentes"
            st.rerun()

    with col2:
        if st.button("Analisar Ações", use_container_width=True):
            st.session_state.navegacao_principal = "Ações"
            st.rerun()

    with col3:
        if st.button("Conversar com IA", use_container_width=True):
            st.session_state.navegacao_principal = "Chat"
            st.rerun()


def pagina_analise_agentes():
    """Página de análise dos agentes CrewAI."""
    st.title("🤖 Relatório da Análise dos Agentes")
    st.markdown("Análise multiagente gerada pelo CrewAI")
    st.divider()

    render_secao_contexto("Status do Arquivo")
    if not render_status_arquivo(ARQUIVO_RELATORIO_AGENTES, "Relatório de Análise"):
        st.warning("Execute `python main/main.py` para gerar o relatório.")
        return

    st.divider()

    render_secao_saida("Relatório Completo")
    relatorio_agentes = carregar_relatorio_md(ARQUIVO_RELATORIO_AGENTES)

    with st.container():
        st.markdown(relatorio_agentes, unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns([3, 1])
    with col2:
        if relatorio_agentes and not relatorio_agentes.startswith("Erro"):
            st.download_button(
                label="Download Relatório",
                data=relatorio_agentes,
                file_name="relatorio_analise.md",
                mime="text/markdown",
                use_container_width=True
            )


def pagina_acoes():
    """Página de análise de ações."""
    st.title("📈 Análise de Ações da B3")
    st.markdown("Visualize o desempenho das principais ações do mercado")
    st.divider()

    df_acoes = carregar_csv(ARQUIVO_ACOES)

    if isinstance(df_acoes, str):
        st.error(df_acoes)
        return

    if "ticker" not in df_acoes.columns:
        st.error("Coluna 'ticker' não encontrada no arquivo de ações.")
        return

    # Seção de entrada
    render_secao_entrada("Selecione a Ação")

    col1, col2 = st.columns([2, 1])

    with col1:
        tickers = sorted(df_acoes["ticker"].unique())
        ticker_selecionado = st.selectbox(
            "Ticker:",
            tickers,
            key="ticker_selector"
        )

    with col2:
        st.metric(
            "Total de registros",
            len(df_acoes[df_acoes["ticker"] == ticker_selecionado])
        )

    st.divider()

    # Seção de contexto
    render_secao_contexto("Dados Disponíveis")

    df_ticker_raw = df_acoes[df_acoes["ticker"] == ticker_selecionado]

    with st.expander("Ver tabela de dados brutos", expanded=False):
        st.dataframe(df_ticker_raw, use_container_width=True)

    st.divider()

    # Seção de saída
    render_secao_saida("Análise Visual")

    df_ticker, erro = preparar_dados_acao(df_acoes, ticker_selecionado)

    if erro:
        st.warning(erro)
    elif df_ticker is not None:
        fig = criar_grafico_linha_neon(
            df_ticker,
            x="data_plot",
            y="fechamento",
            titulo=f"Preço de Fechamento — {ticker_selecionado}"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Último Fechamento", f"R$ {df_ticker['fechamento'].iloc[-1]:.2f}")
        with col2:
            st.metric("Média", f"R$ {df_ticker['fechamento'].mean():.2f}")
        with col3:
            st.metric("Máximo", f"R$ {df_ticker['fechamento'].max():.2f}")
        with col4:
            st.metric("Mínimo", f"R$ {df_ticker['fechamento'].min():.2f}")

        # Adicionar ao histórico
        if st.button("Salvar no Histórico", key="salvar_acao"):
            item = {
                "ticker": ticker_selecionado,
                "data_consulta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ultimo_fechamento": float(df_ticker['fechamento'].iloc[-1]),
                "media": float(df_ticker['fechamento'].mean())
            }
            adicionar_ao_historico("historico_acoes", item)
            st.success("Adicionado ao histórico")

    st.divider()

    # Histórico
    render_historico_com_acoes("historico_acoes", "Histórico de Consultas de Ações")


def pagina_indicadores():
    """Página de indicadores econômicos."""
    st.title("📉 Indicadores Econômicos")
    st.markdown("Acompanhe os principais indicadores da economia brasileira")
    st.divider()

    df_indicadores = carregar_csv(ARQUIVO_INDICADORES_ECONOMICOS)

    if isinstance(df_indicadores, str):
        st.error(df_indicadores)
        return

    required_cols = ["data", "valor", "indicador"]
    if not all(col in df_indicadores.columns for col in required_cols):
        st.error(f"O arquivo deve conter as colunas: {', '.join(required_cols)}")
        return

    # Converter datas
    df_indicadores["data"] = pd.to_datetime(df_indicadores["data"], errors="coerce")
    df_indicadores = df_indicadores.dropna(subset=["data"])

    if df_indicadores.empty:
        st.warning("Não há dados válidos de indicadores.")
        return

    # Seção de entrada
    render_secao_entrada("Selecione o Indicador")

    col1, col2 = st.columns([2, 1])

    with col1:
        indicadores_disponiveis = sorted(df_indicadores["indicador"].unique())
        indicador_selecionado = st.selectbox(
            "Indicador:",
            indicadores_disponiveis,
            key="indicador_selector"
        )

    with col2:
        st.metric(
            "Total de registros",
            len(df_indicadores[df_indicadores["indicador"] == indicador_selecionado])
        )

    st.divider()

    # Seção de contexto
    render_secao_contexto("Dados Disponíveis")

    df_indicador_raw = df_indicadores[df_indicadores["indicador"] == indicador_selecionado]

    with st.expander("Ver tabela de dados brutos", expanded=False):
        st.dataframe(df_indicador_raw, use_container_width=True)

    st.divider()

    # Seção de saída
    render_secao_saida("Análise Visual")

    df_plot, erro = preparar_dados_indicador(df_indicadores, indicador_selecionado)

    if erro:
        st.warning(erro)
    elif df_plot is not None:
        fig = criar_grafico_area_neon(
            df_plot,
            x="data",
            y="valor",
            titulo=f"{indicador_selecionado} — Histórico"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Último Valor", f"{df_plot['valor'].iloc[-1]:.2f}")
        with col2:
            st.metric("Média", f"{df_plot['valor'].mean():.2f}")
        with col3:
            st.metric("Máximo", f"{df_plot['valor'].max():.2f}")
        with col4:
            st.metric("Mínimo", f"{df_plot['valor'].min():.2f}")

        # Adicionar ao histórico
        if st.button("Salvar no Histórico", key="salvar_indicador"):
            item = {
                "indicador": indicador_selecionado,
                "data_consulta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ultimo_valor": float(df_plot['valor'].iloc[-1]),
                "media": float(df_plot['valor'].mean())
            }
            adicionar_ao_historico("historico_indicadores", item)
            st.success("Adicionado ao histórico")

    st.divider()

    # Histórico
    render_historico_com_acoes("historico_indicadores", "Histórico de Consultas de Indicadores")


def pagina_noticias():
    """Página de notícias."""
    st.title("📰 Notícias do Mercado Financeiro")
    st.markdown("Últimas notícias sobre economia e investimentos")
    st.divider()

    df_noticias = carregar_csv(ARQUIVO_NOTICIAS)

    if isinstance(df_noticias, str):
        st.error(df_noticias)
        return

    if "titulo" not in df_noticias.columns or "link" not in df_noticias.columns:
        st.warning("Colunas 'titulo' e 'link' não encontradas.")
        st.dataframe(df_noticias.head(10))
        return

    # Filtros
    render_secao_entrada("Filtros")

    col1, col2 = st.columns(2)

    with col1:
        num_noticias = st.slider(
            "Número de notícias:",
            min_value=5,
            max_value=min(50, len(df_noticias)),
            value=10,
            step=5
        )

    with col2:
        if "fonte" in df_noticias.columns:
            fontes = ["Todas"] + sorted(df_noticias["fonte"].dropna().unique().tolist())
            fonte_filtro = st.selectbox("Filtrar por fonte:", fontes)
        else:
            fonte_filtro = "Todas"

    st.divider()

    # Aplicar filtros
    df_filtrado = df_noticias.copy()
    if fonte_filtro != "Todas" and "fonte" in df_noticias.columns:
        df_filtrado = df_filtrado[df_filtrado["fonte"] == fonte_filtro]

    render_secao_saida(f"Notícias ({len(df_filtrado)} encontradas)")

    # Renderizar notícias
    for idx, row in df_filtrado.head(num_noticias).iterrows():
        titulo = str(row["titulo"])
        link = str(row["link"]) if pd.notna(row["link"]) else ""

        with st.container():
            st.markdown(f"### {titulo}")

            col1, col2 = st.columns([3, 1])

            with col1:
                if link and link.strip().lower() not in ["nan", "na", "n/a"]:
                    st.markdown(f"[Ler notícia completa]({link})")
                else:
                    st.caption("Link não disponível")

            with col2:
                if "fonte" in row and pd.notna(row["fonte"]):
                    st.caption(f"Fonte: {row['fonte']}")

            st.divider()


def pagina_chat():
    """Página do chatbot."""
    st.title("💬 Assistente de Investimentos IA")
    st.markdown("Converse com o Analista Econômico Virtual")
    st.divider()

    if not chat_model:
        st.error("Chatbot não disponível. Variável OPENAI_API_KEY não configurada.")
        st.info("Configure a chave de API no arquivo .env ou nas variáveis de ambiente.")
        return

    # Seção de entrada
    render_secao_entrada("Faça sua Pergunta")

    pergunta_cliente = st.text_input(
        "Digite sua pergunta sobre investimentos ou economia:",
        key="chat_input",
        placeholder="Ex: Como a SELIC afeta o mercado de ações?"
    )

    enviar = st.button("Enviar", type="primary", use_container_width=False)

    st.divider()

    # Processar pergunta
    if (pergunta_cliente and enviar) or (pergunta_cliente and len(st.session_state.chat_history) == 0):
        mensagens = [SystemMessage(content=CONTEXTO_CHAT)]

        for troca in st.session_state.chat_history:
            mensagens.append(HumanMessage(content=troca["pergunta"]))
            mensagens.append(AIMessage(content=troca["resposta"]))

        mensagens.append(HumanMessage(content=pergunta_cliente))

        with st.spinner("Analisando sua pergunta..."):
            try:
                resposta_obj = chat_model(mensagens)
                resposta = resposta_obj.content
                st.session_state.chat_history.append(
                    {"pergunta": pergunta_cliente, "resposta": resposta}
                )
            except Exception as e:
                st.error(f"Erro ao obter resposta: {e}")
                return

    # Seção de saída
    if st.session_state.chat_history:
        render_secao_saida("Conversa")

        # Mostrar última interação
        ultima_troca = st.session_state.chat_history[-1]

        with st.container():
            st.markdown("#### Você:")
            st.info(ultima_troca["pergunta"])

            st.markdown("#### Analista:")
            st.success(ultima_troca["resposta"])

        st.divider()

        # Histórico completo
        with st.expander(f"Histórico Completo ({len(st.session_state.chat_history)} mensagens)", expanded=False):
            for i, troca in enumerate(st.session_state.chat_history[:-1]):
                st.markdown(f"**Conversa #{i+1}**")
                st.markdown(f"**Você:** {troca['pergunta']}")
                st.markdown(f"**Analista:** {troca['resposta']}")
                st.markdown("---")

        # Botões de ação
        col1, col2, col3 = st.columns([2, 1, 1])

        with col2:
            if st.button("Limpar Histórico", key="limpar_chat"):
                st.session_state.chat_history = []
                st.rerun()

        with col3:
            import json
            historico_json = json.dumps(st.session_state.chat_history, ensure_ascii=False, indent=2)
            st.download_button(
                label="Download",
                data=historico_json,
                file_name="chat_historico.json",
                mime="application/json"
            )


# ============================================================
# MAIN - Navegação e renderização
# ============================================================

def main():
    """Função principal com navegação."""

    # Renderizar menu de navegação na sidebar
    pagina_atual = render_menu_navegacao()

    # Renderizar informações do sistema na sidebar
    render_info_sidebar(DATA_DIR)

    # Renderizar página selecionada
    if pagina_atual == "Home":
        pagina_home()
    elif pagina_atual == "Análise Agentes":
        pagina_analise_agentes()
    elif pagina_atual == "Ações":
        pagina_acoes()
    elif pagina_atual == "Indicadores":
        pagina_indicadores()
    elif pagina_atual == "Notícias":
        pagina_noticias()
    elif pagina_atual == "Chat":
        pagina_chat()


if __name__ == "__main__":
    main()