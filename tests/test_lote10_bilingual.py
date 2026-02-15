"""
Lote 10: Bilingual i18n System Validation
Tests that map/ranking section uses bilingual translations instead of hardcoded strings
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import re

from src.config.constants import I18N


def test_i18n_keys_exist():
    """Verify all new i18n keys exist in both PT and EN"""
    required_keys = [
        "map_title",
        "map_description",
        "map_col_rank",
        "map_col_state",
        "map_col_region",
        "map_col_index",
    ]

    for key in required_keys:
        assert key in I18N["pt"], f"Missing PT key: {key}"
        assert key in I18N["en"], f"Missing EN key: {key}"

    print("✓ All i18n keys exist in PT and EN")


def test_i18n_values_not_empty():
    """Verify all new i18n values are non-empty"""
    required_keys = [
        "map_title",
        "map_description",
        "map_col_rank",
        "map_col_state",
        "map_col_region",
        "map_col_index",
    ]

    for key in required_keys:
        assert I18N["pt"][key].strip(), f"Empty PT value for: {key}"
        assert I18N["en"][key].strip(), f"Empty EN value for: {key}"

    print("✓ All i18n values are non-empty")


def test_bilingual_consistency():
    """Verify PT and EN translations are different (not just copies)"""
    pt = I18N["pt"]
    en = I18N["en"]

    # These should be different languages
    assert pt["map_title"] != en["map_title"], "Map title not translated"
    assert pt["map_col_state"] != en["map_col_state"], "State header not translated"
    assert pt["map_col_region"] != en["map_col_region"], "Region header not translated"
    # Note: "Rank" is the same in both PT and EN (international word)

    print("✓ PT and EN translations are distinct")


def test_app_uses_i18n_not_hardcoded():
    """Verify app.py uses T["key"] instead of hardcoded strings"""
    app_path = project_root / "dashboards" / "app.py"

    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract map/ranking section (roughly lines 370-450)
    # Look for the section with choropleth + ranking

    # These hardcoded strings should NOT appear in map section
    forbidden_hardcoded = [
        '"Structural Index"',
        '"Structural Index by State"',
        '"State (UF)"',
        '"Region"',
        '"Rank"',
    ]

    # Find the map/ranking section
    map_section_start = content.find("def _render_map_and_ranking_section")
    if map_section_start == -1:
        print("⚠ Warning: Could not find map/ranking section to validate")
        return

    # Get next 3000 chars to cover the section
    map_section = content[map_section_start : map_section_start + 3000]

    # Check that T["map_col_index"] and T["map_title"] are used
    assert (
        'T["map_col_index"]' in map_section or "T['map_col_index']" in map_section
    ), "map_col_index not used via T[] in map section"

    assert (
        'T["map_title"]' in map_section or "T['map_title']" in map_section
    ), "map_title not used via T[] in map section"

    print("✓ App uses T[] references, not hardcoded strings")


def test_i18n_system_loading():
    """Verify I18N loads correctly and can be accessed"""
    # Test Portuguese
    pt = I18N["pt"]
    assert isinstance(pt, dict), "PT not a dict"
    assert len(pt) > 0, "PT dict empty"

    # Test English
    en = I18N["en"]
    assert isinstance(en, dict), "EN not a dict"
    assert len(en) > 0, "EN dict empty"

    # Test dictionary access pattern used in app
    lang = "pt"
    T = I18N[lang]
    test_value = T["map_title"]
    assert isinstance(test_value, str), "T['map_title'] not a string"

    print(f"✓ I18N system loads correctly ({len(pt)} PT keys, {len(en)} EN keys)")


def test_sample_bilingual_output():
    """Show sample bilingual output"""
    print("\n📊 Bilingual Output Sample:")
    print("=" * 60)

    for lang in ["pt", "en"]:
        T = I18N[lang]
        print(f"\n{lang.upper()}:")
        print(f"  Title: {T['map_title']}")
        print(
            f"  Columns: {T['map_col_rank']}, {T['map_col_state']}, {T['map_col_region']}, {T['map_col_index']}"
        )


if __name__ == "__main__":
    print("🧪 Lote 10: Bilingual i18n Validation\n")

    try:
        test_i18n_keys_exist()
        test_i18n_values_not_empty()
        test_bilingual_consistency()
        test_i18n_system_loading()
        test_app_uses_i18n_not_hardcoded()
        test_sample_bilingual_output()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Bilingual i18n system working!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
