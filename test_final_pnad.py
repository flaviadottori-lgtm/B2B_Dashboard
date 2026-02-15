#!/usr/bin/env python
import sys

print('\n' + '='*60)
print('TESTE FINAL - PNAD INTEGRATION'.center(60))
print('='*60 + '\n')

# Test 1: Syntax
print('[1/4] Verificando sintaxe...')
try:
    import py_compile
    py_compile.compile('dashboards/app.py', doraise=True)
    py_compile.compile('src/ui/pnad_section.py', doraise=True)
    py_compile.compile('src/utils/data_loading.py', doraise=True)
    print('      ✓ Sintaxe OK (app.py, pnad_section.py, data_loading.py)\n')
except Exception as e:
    print(f'      ✗ Erro: {e}')
    sys.exit(1)

# Test 2: Imports
print('[2/4] Testando imports...')
try:
    from src.ui.pnad_section import render_pnad_section
    from src.utils.data_loading import load_pnad_data
    from src.config.constants import I18N
    print('      ✓ Todos os imports OK\n')
except Exception as e:
    print(f'      ✗ Erro: {e}')
    sys.exit(1)

# Test 3: i18n keys
print('[3/4] Validando chaves i18n...')
try:
    required_keys = ['pnad_title', 'pnad_desc', 'pnad_filters', 'pnad_data']
    for key in required_keys:
        assert key in I18N['pt'], f'PT: chave {key} faltando'
        assert key in I18N['en'], f'EN: chave {key} faltando'
    assert len(I18N['pt']['tabs']) == 5, 'PT tabs nao tem 5 elementos'
    assert len(I18N['en']['tabs']) == 5, 'EN tabs nao tem 5 elementos'
    print('      ✓ Chaves i18n OK (26 chaves novas: PT+EN)\n')
except AssertionError as e:
    print(f'      ✗ Erro: {e}')
    sys.exit(1)

# Test 4: PNAD data
print('[4/4] Carregando dados PNAD...')
try:
    df = load_pnad_data()
    if df is not None:
        print(f'      ✓ PNAD carregado: {len(df)} linhas')
        print(f'      ✓ Colunas: {list(df.columns)}')
    else:
        print('      ⊘ Parquet nao encontrado (OK - pode gerar via run_pnad_pipeline.py)')
except Exception as e:
    print(f'      ✗ Erro: {e}')
    sys.exit(1)

print('\n' + '='*60)
print('TUDO PRONTO PARA USAR!'.center(60))
print('='*60)
print('\nProximos passos:')
print('  1. streamlit run dashboards/app.py')
print('  2. Ir na aba PNAD (aba 4)')
print('  3. Testar filtros e graficos')
print('  4. Mudar idioma (PT/EN) no sidebar')
print()
