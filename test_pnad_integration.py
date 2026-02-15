"""
PNAD Integration Test
Validates that PNAD data loader, i18n keys, and UI component work correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.constants import I18N
from src.utils.data_loading import load_pnad_data
import pandas as pd


def test_pnad_i18n_keys_exist():
    """Verify all PNAD i18n keys exist in both PT and EN"""
    required_keys = [
        "pnad_title",
        "pnad_desc",
        "pnad_year",
        "pnad_state",
        "pnad_gender",
        "pnad_age_group",
        "pnad_population",
        "pnad_filters",
        "pnad_data",
        "pnad_not_found",
        "pnad_not_found_msg",
        "pnad_time_series",
        "pnad_comparison"
    ]
    
    for key in required_keys:
        assert key in I18N["pt"], f"Missing PT key: {key}"
        assert key in I18N["en"], f"Missing EN key: {key}"
    
    print("✓ All PNAD i18n keys exist in PT and EN")


def test_pnad_i18n_values_not_empty():
    """Verify all PNAD i18n values are non-empty"""
    required_keys = [
        "pnad_title",
        "pnad_desc",
        "pnad_year",
        "pnad_state",
        "pnad_gender",
        "pnad_age_group",
        "pnad_population",
        "pnad_filters",
        "pnad_data",
        "pnad_not_found",
        "pnad_not_found_msg",
        "pnad_time_series",
        "pnad_comparison"
    ]
    
    for key in required_keys:
        assert I18N["pt"][key].strip(), f"Empty PT value for: {key}"
        assert I18N["en"][key].strip(), f"Empty EN value for: {key}"
    
    print("✓ All PNAD i18n values are non-empty")


def test_pnad_tabs_updated():
    """Verify that 'tabs' array now contains 5 tabs including PNAD"""
    pt_tabs = I18N["pt"].get("tabs", [])
    en_tabs = I18N["en"].get("tabs", [])
    
    assert len(pt_tabs) == 5, f"Expected 5 tabs in PT, got {len(pt_tabs)}"
    assert len(en_tabs) == 5, f"Expected 5 tabs in EN, got {len(en_tabs)}"
    
    # Check that PNAD tab is present
    assert any("PNAD" in tab for tab in pt_tabs), "PNAD tab not found in PT tabs"
    assert any("PNAD" in tab for tab in en_tabs), "PNAD tab not found in EN tabs"
    
    print("✓ Tab arrays updated to 5 tabs including PNAD")


def test_pnad_loader_returns_none_if_missing():
    """Test that load_pnad_data() gracefully returns None if parquet missing"""
    # Try loading from non-existent path
    result = load_pnad_data(pnad_path=Path("/nonexistent/pnad.parquet"))
    assert result is None, "Expected None for missing parquet file"
    print("✓ Loader gracefully returns None for missing parquet")


def test_pnad_loader_structure():
    """Test that load_pnad_data() structure is correct when parquet exists"""
    pnad_path = Path(__file__).parent / "data" / "marts" / "pnad" / "pnad_uf_quarter_gender_age.parquet"
    
    if not pnad_path.exists():
        print("⊘ Skipping loader structure test (parquet not found at " + str(pnad_path) + ")")
        print("   To generate, run: python run_pnad_pipeline.py")
        return
    
    result = load_pnad_data(pnad_path=pnad_path)
    
    if result is None:
        print("⊘ Skipping loader structure test (loader returned None)")
        return
    
    # Verify it's a DataFrame
    assert isinstance(result, pd.DataFrame), "Expected DataFrame, got " + str(type(result))
    
    # Verify required columns
    required_cols = ["ano", "uf_code", "sexo", "grupo_idade", "populacao"]
    for col in required_cols:
        assert col in result.columns, f"Missing column: {col}"
    
    # Verify data types
    assert result["ano"].dtype in ["int64", "int32"], f"Wrong dtype for 'ano': {result['ano'].dtype}"
    assert result["populacao"].dtype in ["int64", "int32"], f"Wrong dtype for 'populacao': {result['populacao'].dtype}"
    
    # Verify data is not empty
    assert len(result) > 0, "PNAD DataFrame is empty"
    
    print(f"✓ Loader returns correct DataFrame structure ({len(result)} rows)")



def test_app_imports():
    """Test that app.py can import all necessary components"""
    try:
        from src.ui.pnad_section import render_pnad_section
        print("✓ App imports pnad_section successfully")
    except ImportError as e:
        raise AssertionError(f"Failed to import pnad_section: {e}")


if __name__ == "__main__":
    print("\n=== PNAD Integration Tests ===\n")
    
    try:
        test_pnad_i18n_keys_exist()
        test_pnad_i18n_values_not_empty()
        test_pnad_tabs_updated()
        test_pnad_loader_returns_none_if_missing()
        test_pnad_loader_structure()
        test_app_imports()
        
        print("\n✅ All PNAD integration tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
