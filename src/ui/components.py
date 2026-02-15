"""
Componentes e estilos CSS reutilizáveis para Streamlit.
"""

import streamlit as st


def apply_styles() -> None:
    """
    Aplica estilos CSS globais (tema dark executivo).
    Deve ser chamado uma única vez no início do app.
    """
    st.markdown(
        """
<style>
    .block-container { padding-top: 1.3rem; padding-bottom: 2rem; }
    h1, h2, h3 { letter-spacing: 0.8px; }
    .title-up { text-transform: uppercase; font-weight: 800; letter-spacing: 2px; }
    .subtitle { color: #9aa4b2; margin-top: -6px; }

    .kpi {
        background: linear-gradient(180deg, rgba(22,27,34,1) 0%, rgba(14,17,23,1) 100%);
        padding: 18px 18px;
        border-radius: 16px;
        border: 1px solid #21262D;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        min-height: 120px;
    }
    .kpi .label { color: #9aa4b2; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
    .kpi .value { font-size: 30px; font-weight: 800; margin-top: 6px; }
    .kpi .hint  { color: #8B949E; font-size: 12px; margin-top: 6px; }

    .pill {
        display:inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        border: 1px solid #2b313a;
        background: #0E1117;
        color: #c9d1d9;
        font-size: 12px;
        margin-right: 8px;
        margin-top: 6px;
        text-transform: uppercase;
        letter-spacing: .6px;
    }

    .section-card {
        border: 1px solid #21262D;
        border-radius: 16px;
        padding: 14px 14px;
        background: rgba(22,27,34,0.55);
    }

    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""",
        unsafe_allow_html=True,
    )


def render_kpi(label: str, value: str, hint: str = "") -> None:
    """
    Renderiza um KPI em estilo card.
    
    Args:
        label: Texto do rótulo (em cima)
        value: Valor principal (número/texto grande)
        hint: Dica/descrição (embaixo)
    """
    st.markdown(
        f"""
<div class="kpi">
  <div class="label">{label}</div>
  <div class="value">{value}</div>
  <div class="hint">{hint}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_pills(pills_dict: dict) -> None:
    """
    Renderiza pills (tags) de filtros ativos.
    
    Args:
        pills_dict: Dict com {label: valor}
        
    Exemplo:
        render_pills({
            "Ano": "2024",
            "Estado": "SP",
            "Setor": "Tecnologia"
        })
    """
    html = ""
    for label, value in pills_dict.items():
        html += f'<span class="pill">{label}: {value}</span>\n'

    st.markdown(html, unsafe_allow_html=True)


def render_diagnostic_info(
    project_root: str,
    data_files: dict,
) -> None:
    """
    Renderiza box de diagnóstico com informações de caminhos e arquivos.
    
    Args:
        project_root: Caminho raiz do projeto
        data_files: Dict {nome: (caminho, existe?)}
    """
    with st.expander("[OK] Diagnostico (verificar arquivos)", expanded=False):
        st.code(f"PROJECT_ROOT: {project_root}")

        for name, (path, exists) in data_files.items():
            status = "[OK]" if exists else "[ERROR]"
            st.write(f"{status} {name}: {path} | exists: {exists}")
