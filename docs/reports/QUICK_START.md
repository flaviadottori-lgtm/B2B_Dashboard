# 🚀 Quick Start Guide

Guia rápido para começar com B2B Dashboard.

## 📥 1. Instalação (5 minutos)

### Windows/Mac/Linux
```bash
# Clone o repositório
git clone <seu-repo>
cd B2B_Dashboard

# Criar ambiente virtual
python -m venv .venv

# Ativar
source .venv/bin/activate  # Mac/Linux
# ou
.venv\Scripts\activate     # Windows

# Instalar
make install-dev
```

## ✅ 2. Validar Setup

```bash
# Verificar que tudo funcionou
make dev

# Você deve ver:
# ✅ All checks passed!
```



## 🏃 3. Inicializar e Rodar o App

Antes de rodar o Streamlit, garanta as views e dimensões padrão no banco oficial DuckDB:

```bash
python scripts/bootstrap_duckdb.py
# O banco oficial é data/marts/b2b.duckdb
```

Depois rode o app normalmente:

```bash
streamlit run dashboards/app.py
```

# Abre em http://localhost:8501

## 🧪 4. Rodar Testes

```bash
# Testes simples
make test

# Com cobertura (gera HTML)
make test-cov

# Ver resultado em htmlcov/index.html
```

## 💻 5. Desenvolver

### Workflow Básico
```bash
# 1. Criar branch
git checkout -b feature/minha-feature

# 2. Fazer mudanças em src/ ou dashboards/

# 3. Verificar qualidade (auto-formata)
make format

# 4. Rodar testes
make test-cov

# 5. Commit (pre-commit hooks rodam automaticamente)
git add .
git commit -m "feat: descrição da feature"

# 6. Push
git push origin feature/minha-feature

# 7. Criar PR no GitHub
```

### Arquitetura do Projeto
```
src/
├── config/        # Configurações centralizadas
├── core/          # Lógica de negócio
├── ui/            # Componentes Streamlit
└── utils/         # Funções utilitárias

dashboards/
└── app.py         # App principal (refatorado)

tests/             # Testes (55+)
```

## 📚 Documentação

- **DEVELOPMENT.md** - Padrões de código e guias
- **CONTRIBUTING.md** - Como contribuir
- **TESTING.md** - Strategy e guidelines
- **DEPLOYMENT.md** - Deploy em produção
- **README.md** - Overview geral

## 🆘 Problemas Comuns

### Módulos não encontrados
```bash
# Reinstalar com setup local
pip install -e .
```

### Testes falhando
```bash
# Verificar Python version
python --version  # Deve ser 3.9+

# Reinstalar deps
make install-dev
make test
```

### Streamlit não roda
```bash
# Verificar instalação
pip list | grep streamlit

# Reinstalar
pip install streamlit==1.28.1

# Rodar com debug
streamlit run dashboards/app.py --logger.level=debug
```

## 🎯 Próximas Etapas

1. **Ler DEVELOPMENT.md** - Entender padrões
2. **Explorar tests/** - Ver exemplos de testes
3. **Fazer uma mudança simples** - Praticar workflow
4. **Abrir PR** - Contribuir com algo

## 📞 Precisa de Ajuda?

- 📖 Leia a documentação relevante
- 🔍 Procure em DEVELOPMENT.md
- 🐛 Abra uma issue no GitHub
- 💬 Use Discussions para perguntas

---

**Status:** ✅ Pronto para usar  
**Versão:** 1.1.0  
**Python:** 3.9+  
**Deps:** ~30 packages
