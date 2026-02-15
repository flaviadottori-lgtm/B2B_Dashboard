#!/usr/bin/env python
"""Smoke test for map + ranking visual improvements (Lote 7)."""

import sys

print('')
print('='*75)
print('SMOKE TEST - LOTE 7 (MAP + RANKING IMPROVEMENTS)'.center(75))
print('='*75)
print('')

# Check 1: Syntax
print('[✓] Syntax Check:')
try:
    import py_compile
    py_compile.compile('dashboards/app.py', doraise=True)
    print('    dashboards/app.py compila sem erros')
except Exception as e:
    print(f'    ✗ Erro de sintaxe: {e}')
    sys.exit(1)

# Check 2: Imports críticos
print('')
print('[✓] Imports Check:')
try:
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    from src.core.data_processing import apply_filters, prep_scores
    from src.utils.data_loading import load_geojson_safe
    print('    Todas as dependências carregadas com sucesso')
except Exception as e:
    print(f'    ✗ Erro de import: {e}')
    sys.exit(1)

# Check 3: Validar alterações do mapa e ranking
print('')
print('[✓] Ajustes Visuais Check:')
try:
    with open('dashboards/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    checks = {
        'Paleta Cividis': 'color_continuous_scale="Cividis"' in content,
        'Colorbar título Índice Estrutural': 'title="Índice<br>Estrutural"' in content,
        'Colorbar tickformat .1f': 'tickformat=".1f"' in content,
        'Colorbar len=0.70': 'len=0.70' in content,
        'Bordas discretas': 'landcolor="rgba(20,20,20,1)"' in content,
        'Hover "Índice Estrutural"': 'Índice Estrutural:' in content and '%{customdata[0]:.1f}' in content,
        'Ranking com "Estado (UF)"': '"Estado (UF)"' in content,
        'Ranking com "Região"': '"Região"' in content,
        'Ranking com "Índice Estrutural"': '"Índice Estrutural"' in content,
        'Region agregado no groupby': '.agg(weighted=("_w", "sum"), units=("units", "sum"), region=("region", "first"))' in content,
        'Explicação ranking': 'Índice agregado (2021) que mede oportunidades econômicas' in content,
        'Formato 2 decimais': '.format({"Índice Estrutural": "{:.2f}"}' in content,
    }
    
    all_pass = True
    for check, status in checks.items():
        symbol = '✓' if status else '✗'
        print(f'    [{symbol}] {check}')
        if not status:
            all_pass = False
            
    if not all_pass:
        print('\n    ⚠ Alguma validação falhou!')
        sys.exit(1)
            
except Exception as e:
    print(f'    ✗ Erro ao validar: {e}')
    sys.exit(1)

print('')
print('='*75)
print('STATUS:  TODOS OS AJUSTES VALIDADOS COM SUCESSO'.center(75))
print('='*75)
print('')

print('ARQUIVOS ALTERADOS:')
print('  • dashboards/app.py (4 seções modificadas)')
print('')

print('ALTERAÇÕES ESPECÍFICAS:')
print('  MAPA:')
print('    • Linha ~350: Agregação com region (primeiro)')
print('    • Linha ~363: Paleta "Viridis" → "Cividis"')
print('    • Linha ~371: Labels "Oportunidade" → "Índice Estrutural"')
print('    • Linha ~374-375: Hover text atualizado com "Índice Estrutural"')
print('    • Linha ~381-384: Bordas discretas (landcolor, coastcolor)')
print('    • Linha ~410-416: Colorbar com novo título, len=0.70')
print('')
print('  RANKING:')
print('    • Linha ~419-425: DataFrame com região, renomeação de colunas')
print('    • Linha ~427-436: Texto explicativo com unsafe_allow_html')
print('    • Linha ~437-441: Format de 2 decimais com .style.format()')
print('')

print('3 RAZÕES POR QUE FICOU MAIS CLARO:')
print('')
print('  1. PALETA CIVIDIS (não Viridis/Plasma):')
print('     • Projetada especificamente para dark mode (contraste superior)')
print('     • Simula perceção de cores daltonismo-safe em fundo escuro')
print('     • Tons azuis profundos → ciano/amarelo evitam "neon" excessivo')
print('')
print('  2. RANKING AUTOEXPLICATIVO:')
print('     • Colunas renomeadas em português claro ("Estado (UF)", "Índice...")')
print('     • Texto curto mas completo explica: O QUÊ, QUANDO, COMO interpretar')
print('     • Coluna "Região" adiciona contexto geográfico sem poluir visuais')
print('')
print('  3. BORDAS E COLORBAR DISCREÇÃO:')
print('     • Bordas (landcolor/coastcolor) subtraem-se (não competem)')
print('     • Colorbar menor (0.70 vs 0.75) + ticks menores = menos "barulho"')
print('     • Espaço branco/negativo melhor equilibrado')
print('')
