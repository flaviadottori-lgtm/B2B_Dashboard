#!/usr/bin/env python
"""
Script de setup inicial - Execute uma vez após clonar o projeto

Este script:
1. Verifica dependências
2. Valida estrutura de pastas
3. Cria arquivos necessários
4. Pronto para desenvolvimento
"""

import sys
from pathlib import Path


def check_python_version():
    """Verifica se Python 3.9+ está instalado."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ é necessário")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detectado")


def check_project_structure():
    """Valida estrutura de pastas."""
    required_dirs = [
        "src/config",
        "src/core",
        "src/ui",
        "src/utils",
        "dashboards",
        "data",
    ]

    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Diretório faltando: {dir_path}")
            return False
        print(f"✅ {dir_path}")

    return True


def check_critical_files():
    """Verifica arquivos críticos."""
    files = [
        "dashboards/app.py",
        "src/config/settings.py",
        "src/core/data_processing.py",
        "src/ui/components.py",
        "pyproject.toml",
    ]

    for file_path in files:
        if not Path(file_path).exists():
            print(f"⚠️  Arquivo não encontrado: {file_path}")
        else:
            print(f"✅ {file_path}")


def print_next_steps():
    """Mostra próximos passos."""
    print("""
╔════════════════════════════════════════════╗
║   ✅ Estrutura validada com sucesso!      ║
╚════════════════════════════════════════════╝

🚀 PRÓXIMOS PASSOS:

1. Criar ambiente virtual:
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # ou
   .\\venv\\Scripts\\activate   # Windows

2. Instalar dependências:
   pip install -e .
   pip install -e ".[dev]"  # Com ferramentas de dev

3. Configurar variáveis de ambiente:
   cp .env.example .env

4. Executar dashboard:
   cd dashboards
   streamlit run app.py

5. Para desenvolvimento:
   black src/ dashboards/      # Formatar código
   mypy src/                   # Type checking
   pytest tests/               # Rodar testes

📚 DOCUMENTAÇÃO:
   - README.md              → Overview
   - DEVELOPMENT.md         → Padrões
   - IMPORTS_GUIDE.md       → Como importar
   - REFACTORING_CHECKLIST  → Checklist

💡 DICA: Leia DEVELOPMENT.md antes de contribuir!
    """)


if __name__ == "__main__":
    print("🔍 Validando projeto B2B Dashboard...\n")

    check_python_version()
    print()

    print("📁 Verificando estrutura de pastas:")
    if not check_project_structure():
        sys.exit(1)
    print()

    print("📄 Verificando arquivos críticos:")
    check_critical_files()
    print()

    print_next_steps()
