# scripts/agentes_economicos.py

import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool
from langchain_openai import ChatOpenAI

# ===========
# Carregar variáveis de ambiente
# ===========
load_dotenv()

# Correção: O padrão da biblioteca é OPENAI_API_KEY
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
if not OPENAI_API_KEY:
    raise RuntimeError(
        "ERRO: variavel de ambiente OPENAI_API_KEY não encontrada."
        "Defina no .env (local) ou nos Secrets (Github Actions/Render)"
    )

if not os.getenv("SERPER_API_KEY"):
    print(
        "Aviso: SERPER_API_KEY não encontrada. "
        "O SerperDevTool pode não funcionar corretamente sem essa chave"
    )

# ==============
# Diretórios e arquivos
# =============
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ARQ_TOPO_ACOES = DATA_DIR / "top_10_acoes.csv"
ARQ_NOTICIAS = DATA_DIR / "noticia_investimentos.csv"
ARQ_INDICADORES = DATA_DIR / "indicadores_economicos.csv"
ARQ_RELATORIO_SAIDA = DATA_DIR / "relatorio_indicacao_acoes.md"

# ============
# Leitura dos CSV
# ============
try:
    df_top_10_acoes = pd.read_csv(ARQ_TOPO_ACOES)
    df_noticias_investimento = pd.read_csv(ARQ_NOTICIAS)
    df_indices = pd.read_csv(ARQ_INDICADORES)
except FileNotFoundError as e:
    print("Erro: Arquivo CSV não encontrado")
    print(f"Detalhe: {e}")
    raise SystemExit(1)

# ==================
# Transformar DataFrames em texto de contexto
# ==================
contexto_top_10_acoes = df_top_10_acoes.to_markdown(index=False)
contexto_indices = df_indices.to_markdown(index=False)

# Correção: check de colunas correto
if not df_noticias_investimento.empty and {"titulo", "link"}.issubset(df_noticias_investimento.columns):
    contexto_noticias_investimentos = "\n".join(
        [
            f"Título: {row['titulo']}\nLink: {row['link']}"
            for _, row in df_noticias_investimento.iterrows()
        ]
    )
else:
    contexto_noticias_investimentos = "Nenhuma notícia de investimentos foi encontrada"

contexto_geral_csv = f"""
=========== Dados Históricos de Indicadores Economicos =======================
{contexto_indices}

======== Noticias de Investimentos Recentes (do CSV) =========================
{contexto_noticias_investimentos}

======== Top 10 Ações Monitoradas (do CSV) =========================
{contexto_top_10_acoes}
"""

# =======================================
# Configuração do LLM
# =======================================
# Em vez de passar o objeto llm para cada agente, 
# vamos garantir que a chave de API esteja no ambiente.
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
# Definimos o modelo que queremos usar como padrão
MODEL_NAME = "gpt-4o-mini"
# Definir a ferramenta ANTES dos agentes
web_tool = SerperDevTool()

# ========================
# Definição dos agentes
# ========================

analista_macroeconomico = Agent(
    role="Analista Macroeconômico Sênior",
    goal=(
        "Analisar o cenário macroecônomico brasileiro, com foco nos indicadores econômicos "
        "e nas notícias de investimento..."
    ),
    backstory=(
        "Economista com vasta experiência na análise da conjuntura econômica brasileira..."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[web_tool],
    llm=MODEL_NAME, # ALTERAÇÃO AQUI: Passamos a string do modelo
)

especialista_em_acoes = Agent(
    role="Especialista em Análise de Ações da B3",
    goal=(
        "Avaliar ações da B3, com ênfase nas 'top_10_acoes.csv'..."
    ),
    backstory=(
        "Analista de investimentos (CNPI) focado no mercado de ações brasileiro..."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[web_tool],
    llm=MODEL_NAME, # ALTERAÇÃO AQUI: Passamos a string do modelo
)

redator_de_relatorios_de_investimento = Agent(
    role="Redator de Relatórios de Investimento",
    goal=(
        "Consolidar a análise macroeconômica e as recomendações de ações em um relatório financeiro..."
    ),
    backstory=(
        "Profissional de comunicação com foco no mercado financeiro..."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[],
    llm=MODEL_NAME, # ALTERAÇÃO AQUI: Passamos a string do modelo
)

# =========================
# Tarefas (Tasks) - Suas instruções originais mantidas
# =========================

tarefa_analise_cenario = Task(
    description=(
        "1. Analise os dados dos indicadores econômicos fornecidos no 'contexto_geral_csv' para entender as tendências recentes do mercado.\n"
        "2. Revise as 'Noticias de Investimento Recentes (do CSV)' para capturar o sentimento e os eventos atuais.\n"
        "3. Use a ferramenta de busca na web (SerperDevTool) para buscar as informações atualizadas:\n"
        "   a) Perspectivas para o IPCA, PIB, dólar, IGP-M e taxa Selic no Brasil.\n"
        "   b) Principais fatores macroeconômicos que estão afetando o mercado de ações brasileiro.\n"
        "   c) Notícias relevantes sobre a economia brasileira que possam impactar investimentos.\n"
        "4. Sintetize tudo em um panorama do cenário macroeconômico atual e suas implicações.\n"
        f"Contexto dos CSVs:\n{contexto_geral_csv}"
    ),
    expected_output=(
        "Um relatório conciso sobre o cenário macroeconômico brasileiro, destacando:\n"
        "- Análise da trajetória recente dos indicadores coletados e suas perspectivas.\n"
        "- Principais notícias e eventos de investimento relevantes (CSV + pesquisa online).\n"
        "- Impactos esperados desse cenário no mercado de ações brasileiro."
    ),
    agent=analista_macroeconomico
)

tarefa_indicacao_acoes = Task(
    description=(
        "1. Com base na análise do cenário macroeconômico (tarefa anterior), avalie as ações no arquivo 'top_10_acoes.csv'.\n"
        "2. Para cada tipo de ação do 'top_10_acoes.csv', utilize a ferramenta de busca na web para:\n"
        "   a) Notícias recentes e específicas sobre a empresa e seu setor.\n"
        "   b) Análises e perspectivas de mercado (preço-alvo recomendações, etc.).\n"
        "   c) Informações fundamentais relevantes, quando possível.\n"
        "3. Se julgar pertinente, pesquise também outras ações da B3 que possam representar oportunidades ou riscos no cenário atual.\n"
        "4. Formule recomendações de INVESTIMENTO (COMPRA, VENDA ou MANTER) para pelo menos 5 ações "
        "(priorizando as do 'top_10_acoes.csv', mas podendo incluir outras), cada uma com justificativa.\n"
        f"Contexto principal - Top 10 ações (CSV):\n{contexto_top_10_acoes}"
    ),
    expected_output=(
        "Um relatório de indicações de ações contendo:\n"
        "- Recomendações claras de COMPRA, VENDA ou MANTER para 3 a 5 ações da B3 (com seus tickers).\n"
        "- Justificativa detalhada para cada recomendação, explicando fatores macro, setoriais, específicos da empresa e notícias recentes."
    ),
    agent=especialista_em_acoes,
    context=[tarefa_analise_cenario]
)

tarefa_compilacao_relatorio_final = Task(
    description=(
        "**Sua responsabilidade é GERAR e ESCREVER o conteúdo completo de investimentos em formato markdown. Não descreva o que você faria; produza o relatório AGORA.**\n\n"
        "Você deve:\n"
        "1. Unificar a análise do cenário macroeconômico e as indicações de ações em um relatório final.\n"
        "2. Escrever com linguagem clara, profissional e acessível.\n"
        "3. Destacar como o cenário macroeconômico fundamenta as indicações.\n"
        "4. Apresentar cada indicação com: Ticker, Recomendação (COMPRA/VENDA/MANTER) e justificativa completa.\n"
        "5. Incluir um apêndice mencionando as fontes de dados (CSV + pesquisa online).\n\n"
        "Use as análises das tarefas anteriores, disponíveis no contexto como base principal."
    ),
    expected_output=(
        "Um relatório de investimento completo em markdown (PT-BR), contendo:\n"
        "### Sumário Executivo\n"
        "### Análise do Cenário Macroeconômico\n"
        "### Indicações de Ações Detalhadas\n"
        "### Breves Considerações sobre Riscos e Oportunidades\n"
        "### Apêndice: Fontes de Dados\n"
    ),
    agent=redator_de_relatorios_de_investimento,
    context=[tarefa_analise_cenario, tarefa_indicacao_acoes]
)

# ==================
# Montar o Crew e executar
# ==================

def main():
    crew_recomendacao_de_acoes = Crew(
        agents=[
            analista_macroeconomico,
            especialista_em_acoes,
            redator_de_relatorios_de_investimento,
        ],
        tasks=[
            tarefa_analise_cenario,
            tarefa_indicacao_acoes,
            tarefa_compilacao_relatorio_final,
        ],
        verbose=True
    )

    print("Iniciando a análise de Crew para recomendação de ações...")
    resultado_crew = crew_recomendacao_de_acoes.kickoff()

    # Correção: Extrair texto final com segurança
    texto_para_salvar = str(resultado_crew)
    
    print("\n\n===RELATÓRIO FINAL DE INVESTIMENTO (TEXTO)===\n")
    print(texto_para_salvar)

    # Salvar relatório em markdown
    try:
        ARQ_RELATORIO_SAIDA.write_text(texto_para_salvar, encoding="utf-8")
        print(f"\n\nRelatório salvo com sucesso: {ARQ_RELATORIO_SAIDA}")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

if __name__ == "__main__":
    main()