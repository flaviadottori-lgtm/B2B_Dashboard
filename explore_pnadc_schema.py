"""
Explorar schema do br_ibge_pnadc para criar query otimizada
"""

from google.cloud import bigquery

try:
    client = bigquery.Client(project='basedosdados')
    
    # Tabela principal: ano_uf_grupo_idade (agregado por UF, ano, grupo etário)
    table_id = "basedosdados.br_ibge_pnadc.ano_uf_grupo_idade"
    
    print("=" * 80)
    print(f"SCHEMA: {table_id}")
    print("=" * 80)
    
    table = client.get_table(table_id)
    
    print(f"\nTotal rows: {table.num_rows:,}")
    print(f"Table size: {table.num_bytes / (1024**3):.2f} GB")
    print(f"Created: {table.created}")
    
    print("\n" + "=" * 80)
    print("COLUMNS:")
    print("=" * 80)
    
    for field in table.schema:
        field_type = field.field_type
        description = field.description or ""
        print(f"  {field.name:30} | {field_type:15} | {description}")
    
    print("\n" + "=" * 80)
    print("SAMPLE QUERY:")
    print("=" * 80)
    
    query = f"""
    SELECT 
        * 
    FROM `{table_id}`
    LIMIT 5
    """
    
    print("\nExecuting sample query...")
    results = client.query(query).result()
    
    print(f"\nFound columns: {', '.join([field.name for field in results.schema])}")
    print(f"\nFirst few rows:")
    for i, row in enumerate(results):
        if i == 0:
            print(f"\n  Row 1:")
            for key, value in row.items():
                print(f"    {key}: {value}")
        else:
            print(f"\n  Row {i+1}:")
            for key, value in row.items():
                print(f"    {key}: {value}")
    
    # Check ano_uf_raca_cor table too
    print("\n\n" + "=" * 80)
    print("CHECKING: ano_uf_raca_cor (by UF, year, race/color)")
    print("=" * 80)
    
    table2_id = "basedosdados.br_ibge_pnadc.ano_uf_raca_cor"
    table2 = client.get_table(table2_id)
    
    print(f"\nTotal rows: {table2.num_rows:,}")
    print("\nColumns:")
    for field in table2.schema:
        print(f"  {field.name:30} | {field.field_type}")
    
    # Check microdados table
    print("\n\n" + "=" * 80)
    print("CHECKING: microdados (raw individual records)")
    print("=" * 80)
    
    table3_id = "basedosdados.br_ibge_pnadc.microdados"
    table3 = client.get_table(table3_id)
    
    print(f"\nTotal rows: {table3.num_rows:,}")
    print(f"Table size: {table3.num_bytes / (1024**3):.2f} GB")
    print(f"\nColumns (first 20):")
    for i, field in enumerate(table3.schema[:20]):
        print(f"  {field.name:30} | {field.field_type}")
    if len(table3.schema) > 20:
        print(f"  ... and {len(table3.schema) - 20} more columns")
    
except Exception as e:
    print(f"Error: {e}")
