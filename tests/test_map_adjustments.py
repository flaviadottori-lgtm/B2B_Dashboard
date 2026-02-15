#!/usr/bin/env python
"""Smoke test for map visual adjustments (Lote 6)."""

import sys

print("")
print("=" * 70)
print("SMOKE TEST - LOTE 6 (AJUSTE VISUAL MAPA)".center(70))
print("=" * 70)
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

# Check 2: Imports críticos
print("")
print("[✓] Imports Check:")
try:
    import plotly.express as px
    import plotly.graph_objects as go

    from src.core.data_processing import apply_filters, prep_scores
    from src.utils.data_loading import load_geojson_safe

    print("    Todas as dependências de visualização carregadas")
except Exception as e:
    print(f"    ✗ Erro de import: {e}")
    sys.exit(1)

# Check 3: Validar estrutura do mapa
print("")
print("[✓] Estrutura do Mapa Check:")
try:
    with open("dashboards/app.py", "r", encoding="utf-8") as f:
        content = f.read()

    checks = {
        "Paleta Viridis": 'color_continuous_scale="Viridis"' in content,
        "Colorbar título limpo": 'title="Oportunidade"' in content
        and 'title="Oportunidade<br>' not in content,
        "Colorbar tickformat": 'tickformat=".1f"' in content,
        "Colorbar len=0.75": "len=0.75" in content,
        "Template dark mantido": 'template="plotly_dark"' in content,
        "GeoJSON fitting": 'fitbounds="geojson"' in content,
        "Labels UF preservados": 'mode="text"' in content,
    }

    all_pass = True
    for check, status in checks.items():
        symbol = "✓" if status else "✗"
        print(f"    [{symbol}] {check}")
        if not status:
            all_pass = False

    if not all_pass:
        sys.exit(1)

except Exception as e:
    print(f"    ✗ Erro ao validar: {e}")
    sys.exit(1)

print("")
print("=" * 70)
print("STATUS:  AJUSTES VISUAIS VALIDADOS COM SUCESSO".center(70))
print("=" * 70)
print("")
print("LINHAS ALTERADAS:")
print('  • Linha 370: color_continuous_scale="Plasma" → "Viridis"')
print('  • Linha 416: title="Oportunidade<br>(score)" → "Oportunidade"')
print("  • Linha 418: len=0.7 → len=0.75")
print('  • Linha 419: (NOVO) tickformat=".1f" para ticks com 1 casa decimal')
print("")
print("POR QUE VIRIDIS MELHORA A LEITURA EXECUTIVA:")
print("")
print("  1. Perceptual Linearity: Viridis tem gradiente visual uniforme,")
print("     facilitando identificação de padrões sem distorções.")
print("")
print("  2. Dark Mode Optimization: Cores vívidas (roxo escuro → verde → amarelo)")
print("     mantém excelente contraste em fundo escuro (plotly_dark).")
print("")
print("  3. Accessibility: Viridis é colorblind-safe (protanopia/deuteranopia),")
print("     garantindo legibilidade para ~8% da população com daltonismo.")
print("")
print("  4. Professional Standard: Escala sequencial recomendada para dados")
print("     contínuos em relatórios executivos (vs. Plasma que é perceptual).")
print("")
print('  5. Economic Context: Tom verde inicial representa "oportunidade baixa"')
print('     e amarelo brilhante representa "oportunidade alta", alinhado com')
print("     convenção visual de mercado financeiro/economia.")
print("")
