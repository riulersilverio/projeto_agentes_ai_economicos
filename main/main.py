# main/main.py

"""
Orquestração LOCAL do pipeline de coleta de dados + análise dos agentes + abertura do Streamlit.

IMPORTANTE:
- O Render NÃO usa este arquivo.
- Apenas para desenvolvimento local.
"""

import sys
import subprocess
from pathlib import Path


# ============================================
# Caminhos do projeto
# ============================================
# A pasta main/ é um nível abaixo da raiz
MAIN_DIR = Path(__file__).resolve().parent
ROOT_DIR = MAIN_DIR.parent

SCRIPTS_DIR = ROOT_DIR / "scripts"
STREAMLIT_APP = ROOT_DIR / "streamlit" / "dashboard.py"


# ============================================
# Função utilitária para executar etapas
# ============================================
def run_step(description: str, command: list[str]) -> None:
    print(f"\n🔁 {description}")
    print(f"   Comando: {' '.join(command)}")

    try:
        subprocess.run(command, check=True)
        print(f"✅ {description} concluída com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERRO ao executar: {description}")
        print(f"   Detalhes: {e}")
        sys.exit(1)


# ============================================
# Função principal
# ============================================
def main():
    python_exec = sys.executable  # Garante usar o mesmo Python que chamou o script

    # ----------------------------- #
    # 1. Indicadores Econômicos
    # ----------------------------- #
    run_step(
        "Coleta de indicadores econômicos (BACEN)",
        [python_exec, str(SCRIPTS_DIR / "indicadores_economicos.py")],
    )

    # ----------------------------- #
    # 2. Dados das Ações (Alpha Vantage)
    # ----------------------------- #
    run_step(
        "Coleta das ações da B3 (Alpha Vantage)",
        [python_exec, str(SCRIPTS_DIR / "acoes.py")],
    )

    # ----------------------------- #
    # 3. Notícias Econômicas
    # ----------------------------- #
    run_step(
        "Coleta de notícias econômicas",
        [python_exec, str(SCRIPTS_DIR / "noticias.py")],
    )

    # ----------------------------- #
    # 4. Análise Multiagente (CrewAI)
    # ----------------------------- #
    run_step(
        "Execução da análise multiagente (CrewAI)",
        [python_exec, str(SCRIPTS_DIR / "agentes_economicos.py")],
    )

    # ----------------------------- #
    # 5. Iniciar Streamlit
    # ----------------------------- #
    print("\n🚀 Iniciando painel Streamlit...")
    streamlit_cmd = [
        "streamlit",
        "run",
        str(STREAMLIT_APP),
        "--server.address=0.0.0.0",
        "--server.port=8000",
    ]
    print(f"   Comando: {' '.join(streamlit_cmd)}")

    subprocess.run(streamlit_cmd)


if __name__ == "__main__":
    main()