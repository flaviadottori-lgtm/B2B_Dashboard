"""Debug: Check if PNAD table has data"""

from google.cloud import bigquery

client = bigquery.Client(project="b2b-opportunity-engine")

# Test query
query = """
SELECT 
    COUNT(*) as row_count,
    MIN(ano) as min_year,
    MAX(ano) as max_year,
    COUNT(DISTINCT id_uf) as distinct_ufs
FROM `basedosdados.br_ibge_pnadc.ano_uf_grupo_idade`
"""

print("Testing query...")
try:
    result = client.query(query).to_dataframe()
    print(result)
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying with direct result fetch...")
    result = client.query(query).result()
    for row in result:
        print(f"  Row count: {row[0]}")
        print(f"  Min year: {row[1]}")
        print(f"  Max year: {row[2]}")
        print(f"  Distinct UFs: {row[3]}")
