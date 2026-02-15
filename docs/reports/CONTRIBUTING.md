# Como Contribuir

Obrigado por considerar contribuir com o B2B Dashboard! 🎉

## 📋 Pré-requisitos

- Python 3.9+
- Git
- Conhecimento básico de Python

## 🚀 Começando

### 1. Fork e Clone
```bash
git clone seu-fork
cd B2B_Dashboard
```

### 2. Setup de Desenvolvimento
```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar dependências com ferramentas de dev
make install-dev
```

### 3. Configurar Pre-commit
```bash
pre-commit install
```

## ✍️ Workflow de Contribuição

### 1. Crie uma Branch
```bash
git checkout -b feature/sua-feature
# ou
git checkout -b fix/seu-bug
```

### 2. Faça suas Mudanças
- Siga os padrões em `DEVELOPMENT.md`
- Adicione type hints
- Escreva docstrings
- Adicione testes

### 3. Teste Localmente
```bash
# Formatar código
make format

# Verificar tipos
make type-check

# Rodar testes
make test-cov

# Lint
make lint
```

### 4. Commit com Padrão
```bash
# A formatação será validada automaticamente via pre-commit
git add .
git commit -m "type: descrição breve

Descrição mais detalhada se necessário.

Closes #123"
```

**Tipos de commit:**
- `feat:` - Nova feature
- `fix:` - Correção de bug
- `refactor:` - Refatoração
- `test:` - Testes
- `docs:` - Documentação
- `style:` - Formatação
- `chore:` - Manutenção

### 5. Push e PR
```bash
git push origin feature/sua-feature
```

Depois crie um Pull Request no GitHub.

## 📝 Padrões de Código

### Type Hints
```python
def minha_funcao(param1: int, param2: str) -> dict:
    """Descrição."""
    pass
```

### Docstrings
```python
def calcular(a: int, b: int) -> int:
    """
    Calcula a soma de dois números.

    Args:
        a: Primeiro número
        b: Segundo número

    Returns:
        Soma de a e b

    Example:
        >>> calcular(2, 3)
        5
    """
    return a + b
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Iniciando...")
logger.debug("Debug info")
logger.warning("Atenção!")
logger.error("Erro ocorreu!")
```

## 🧪 Testes

### Estrutura
```python
class TestMinhaFuncao:
    """Testes para minha_funcao"""

    def test_caso_basico(self):
        """Descrição breve do teste"""
        result = minha_funcao(2, 3)
        assert result == 5

    def test_caso_especial(self):
        """Teste para caso especial"""
        pass
```

### Rodar Testes
```bash
# Todos os testes
pytest tests/

# Com cobertura
pytest tests/ --cov=src --cov-report=html

# Um arquivo específico
pytest tests/test_formatters.py -v
```

## 📚 Documentação

Se adicionar uma feature, documente em:
- Docstring na função
- Exemplos em `DEVELOPMENT.md` se aplicável
- README.md se for feature maior

## 🔄 CI/CD

Todos os commits são validados automaticamente via GitHub Actions:
- ✅ Tests (pytest)
- ✅ Lint (pylint)
- ✅ Type check (mypy)
- ✅ Format (black, isort)
- ✅ Coverage

Se uma check falhar, você pode arrumar localmente e fazer push novamente.

## 🐛 Reportar Bugs

Use as **Issues** do GitHub com:
- Descrição clara do bug
- Steps para reproduzir
- Comportamento esperado vs. atual
- Python version e OS

## 💡 Sugerir Features

Use as **Discussions** ou **Issues** com:
- Descrição da feature
- Caso de uso
- Possível implementação

## ❓ Dúvidas?

1. Leia `DEVELOPMENT.md` para padrões
2. Consulte `README.md` para overview
3. Abra uma issue para discussão
4. Entre em contato com os maintainers

---

**Obrigado por contribuir! 🙏**
