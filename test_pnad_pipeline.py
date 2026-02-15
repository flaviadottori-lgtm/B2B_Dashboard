"""
Smoke tests para pipeline PNAD BigQuery
"""

import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.Pipelines.pnad import PNADCExtractor, extract_pnad


def test_extractor_initialization():
    """Test that extractor can be initialized"""
    print("\n[] Test 1: Extractor initialization")
    try:
        extractor = PNADCExtractor(project_id='b2b-opportunity-engine')
        print("   ✓ PNADCExtractor initialized successfully")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


def test_extract_function():
    """Test the convenience function"""
    print("\n[] Test 2: Extract function availability")
    try:
        assert callable(extract_pnad), "extract_pnad is not callable"
        print("   ✓ extract_pnad function is available and callable")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


def test_parquet_output():
    """Test that parquet file was created"""
    print("\n[] Test 3: Parquet file validation")
    try:
        output_file = project_root / 'data' / 'marts' / 'pnad' / 'pnad_uf_quarter_gender_age.parquet'
        
        if not output_file.exists():
            print(f"   ⚠ Output file not found: {output_file}")
            print("   (This is expected if pipeline hasn't been run yet)")
            return True
        
        # Check file properties
        file_size = output_file.stat().st_size
        print(f"   ✓ File exists: {output_file}")
        print(f"     Size: {file_size / 1024:.2f} KB")
        
        # Try to read it
        df = pd.read_parquet(output_file)
        print(f"   ✓ Parquet readable: {len(df):,} rows")
        
        # Check columns
        expected_cols = {'ano', 'uf_code', 'sexo', 'grupo_idade', 'populacao'}
        actual_cols = set(df.columns) - {'extracao_data'}
        
        if expected_cols.issubset(actual_cols):
            print(f"   ✓ All expected columns present")
        else:
            missing = expected_cols - actual_cols
            print(f"   ✗ Missing columns: {missing}")
            return False
        
        # Check data types
        print(f"   ✓ Data types:")
        for col in ['ano', 'uf_code', 'sexo', 'grupo_idade', 'populacao']:
            if col in df.columns:
                print(f"     - {col}: {df[col].dtype}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


def test_module_imports():
    """Test that module can be imported"""
    print("\n[] Test 4: Module imports")
    try:
        from src.Pipelines.pnad import PNADCExtractor
        from src.Pipelines.pnad import extract_pnad
        print("   ✓ All imports successful")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


def main():
    print("=" * 70)
    print("PNAD BIGQUERY PIPELINE - SMOKE TESTS")
    print("=" * 70)
    
    tests = [
        test_module_imports,
        test_extractor_initialization,
        test_extract_function,
        test_parquet_output,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"   ✗ Unexpected error: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)
    
    if all(results):
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
