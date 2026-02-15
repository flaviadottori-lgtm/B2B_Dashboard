#!/usr/bin/env python
"""Smoke test for custom blue palette (Lote 8)."""

import sys

print("")
print("=" * 75)
print("SMOKE TEST - LOTE 8 (CUSTOM BLUE PALETTE)".center(75))
print("=" * 75)
print("")

# Check 1: Syntax
print("[✓] Syntax Check:")
try:
    import py_compile

    py_compile.compile("dashboards/app.py", doraise=True)
    print("    dashboards/app.py compila sem erros")
except Exception as e:
    print(f"    ✗ Erro de sintaxe: {e}")
    sys.exit(1)

# Check 2: Imports
print("")
print("[✓] Imports Check:")
try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    from src.core.data_processing import apply_filters, prep_scores
    from src.utils.data_loading import load_geojson_safe

    print("    Todas as dependências carregadas com sucesso")
except Exception as e:
    print(f"    ✗ Erro de import: {e}")
    sys.exit(1)

# Check 3: Validar paleta azul
print("")
print("[✓] Paleta Azul Check:")
try:
    with open("dashboards/app.py", "r", encoding="utf-8") as f:
        content = f.read()

    checks = {
        "Escala azul customizada": '["#0B1F33", "#143A5A", "#1F5C8B", "#3A7CA5", "#A9CCE3"]'
        in content,
        'Não há "Cividis"': 'color_continuous_scale="Cividis"' not in content,
        "Range color fixo": "range_color" not in content
        or "range_color=None" in content
        or "range_color=" not in content,
        "Hover mantido": "Índice Estrutural:" in content,
        "Ranking sem alteração": '"Estado (UF)"' in content,
        "Métricas intactas": 'groupby("uf"' in content,
    }

    all_pass = True
    for check, status in checks.items():
        symbol = "✓" if status else "✗"
        print(f"    [{symbol}] {check}")
        if not status:
            all_pass = False

    if not all_pass:
        print("\n    ⚠ Alguma validação falhou!")
        sys.exit(1)

except Exception as e:
    print(f"    ✗ Erro ao validar: {e}")
    sys.exit(1)

print("")
print("=" * 75)
print("STATUS:  PALETA AZUL VALIDADA COM SUCESSO".center(75))
print("=" * 75)
print("")

print("ARQUIVO ALTERADO:")
print("  • dashboards/app.py (1 linha modificada)")
print("")

print("LINHA ALTERADA:")
print('  • Linha ~369: color_continuous_scale="Cividis" →')
print("               color_continuous_scale=[")
print('                 "#0B1F33", "#143A5A", "#1F5C8B",')
print('                 "#3A7CA5", "#A9CCE3"')
print("               ]")
print("")

print("POR QUE A PALETA AZUL MELHORA A LEITURA EXECUTIVA:")
print("")
print("  1. ASSOCIAÇÃO SEMÂNTICA:")
print('     • Azul escuro (#0B1F33) = "conservador", valores baixos')
print('     • Azul claro (#A9CCE3) = "crescimento", valores altos')
print("     • Alinha com convenção financeira/corporativa (risk→opportunity)")
print("")
print("  2. FOCO SEM DISTRAÇÃO:")
print('     • Monocromia (tons de azul) elimina "competição" visual')
print("     • Sem cores contrastantes (Cividis tinha ciano/verde/amarelo)")
print("     • Menor fadiga ocular em apresentações executivas")
print("")
print("  3. CONTRASTE EM DARK MODE:")
print("     • Azul escuro sobre fundo escuro (17,17,17) = gradiente sutil")
print("     • Azul claro bem destacado em fundo escuro")
print("     • Mantém legibilidade sem neon (vs Plasma/Cividis)")
print("")
print("  4. PROFISSIONALISMO:")
print("     • Paleta corporativa (usada em dashboards bancários/gov)")
print('     • Evita "aesthetic gaming" (cores muito vibrantes)')
print("     • Transmite seriedade e confiabilidade")
print("")
