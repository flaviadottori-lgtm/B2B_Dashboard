# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/),
e este projeto segue [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Teste estrutura com pytest (testes unitários e integração)
- GitHub Actions CI/CD pipeline (matrix testing Python 3.9-3.12)
- Pre-commit hooks para code quality
- Makefile com comandos de desenvolvimento
- CONTRIBUTING.md para guidelines de contribuição
- TESTING.md com cobertura e estratégia de testes
- DEPLOYMENT.md com guia de deployment em produção
- Documentação expandida (DEVELOPMENT.md, IMPORTS_GUIDE.md)

### Changed
- Refatored `dashboards/app.py` de 832 para ~350 linhas
- Modularização completa da aplicação
- Configuração centralizada em `src/config/`
- Melhorado tratamento de erros e logging estruturado

### Fixed
- Hardcoded paths removidos
- Duplicação de código eliminada
- Type hints adicionados em 100% do código novo

## [1.0.0] - 2024-01

### Added
- ✅ Arquitetura modular (config, core, ui, utils)
- ✅ Suporte a múltiplas fontes de dados (IBGE, CAGED, Receita)
- ✅ Dashboard executivo com 4 abas
- ✅ Mapa geográfico interativo
- ✅ Filtros e análises customizáveis
- ✅ Sistema de scoring de oportunidades
- ✅ Exportação de dados em CSV/Excel

### Security
- Environment variables para configuração sensível
- Validação de entrada em todos os endpoints
- Sanitização de logs

### Performance
- Caching com @st.cache_resource
- Lazy loading de dados
- Formato Parquet para performance

## [0.9.0] - 2023-12

### Added
- MVP do dashboard Streamlit
- Pipelines de ETL para IBGE e CAGED
- Análise geográfica de empresas
- Sistema de scores básico

### Known Issues
- Monolithic app.py (refactored in 1.1.0)
- Duplicação de código em pipelines
- Falta de testes

---

## Guidelines

### Versioning
- **MAJOR:** Breaking changes na API ou estrutura
- **MINOR:** Novas features compatíveis
- **PATCH:** Bug fixes

### Commit Messages
Usar conventional commits:
```
type(scope): subject

body

footer
```

Tipos:
- `feat:` Nova feature
- `fix:` Bug fix
- `refactor:` Refactoring
- `test:` Testes
- `docs:` Documentação
- `chore:` Manutenção

### Release Process
1. Update version em `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.2.3`
4. Push e criar release no GitHub
5. Deploy to production

---

**Last Updated:** 2024-01
**Maintainer:** Dev Team
