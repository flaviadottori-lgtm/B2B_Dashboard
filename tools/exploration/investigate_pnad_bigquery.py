"""
Investigação do BigQuery para localizar PNAD Contínua (Base dos Dados)
"""

from google.cloud import bigquery
from google.auth.transport.requests import Request
from google.auth import default
import os

# Suppress gcloud warnings
os.environ["GOOGLE_CLOUD_PROJECT"] = "b2b-opportunity-engine"

try:
    # Initialize BigQuery client using Application Default Credentials
    client = bigquery.Client(project="b2b-opportunity-engine")
    print("✓ BigQuery client initialized (using ADC)")
    print(f"  Project: {client.project}")
    print()

    # List all datasets
    print("=" * 70)
    print("STEP 1: Listing all datasets in project")
    print("=" * 70)
    datasets = list(client.list_datasets())
    print(f"Found {len(datasets)} datasets:\n")

    pnad_datasets = []
    for ds in datasets:
        ds_name = ds.dataset_id
        print(f"  - {ds_name}")
        if "pnad" in ds_name.lower() or "household" in ds_name.lower():
            pnad_datasets.append(ds_name)

    print()

    # If PNAD datasets found, list their tables
    if pnad_datasets:
        print("=" * 70)
        print(f"STEP 2: Found {len(pnad_datasets)} potential PNAD dataset(s)")
        print("=" * 70)

        for ds_name in pnad_datasets:
            print(f"\n📊 Dataset: {ds_name}")
            try:
                dataset_ref = client.dataset(ds_name)
                tables = list(client.list_tables(dataset_ref))
                print(f"   Tables: {len(tables)}")
                for table in tables[:10]:  # Show first 10
                    table_id = table.table_id
                    print(f"     - {table_id}")
            except Exception as e:
                print(f"   Error listing tables: {e}")

    # Try Base dos Dados project if available
    print()
    print("=" * 70)
    print("STEP 3: Checking for 'basedosdados' project (public data)")
    print("=" * 70)
    try:
        bdd_client = bigquery.Client(project="basedosdados")
        bdd_datasets = list(bdd_client.list_datasets())
        print(f"Found {len(bdd_datasets)} datasets in basedosdados project")

        pnad_bdd = [ds.dataset_id for ds in bdd_datasets if "pnad" in ds.dataset_id.lower()]
        if pnad_bdd:
            print(f"\n✓ PNAD datasets in basedosdados: {pnad_bdd}")

            for ds_name in pnad_bdd:
                print(f"\n📊 Dataset: basedosdados.{ds_name}")
                dataset_ref = bdd_client.dataset(ds_name)
                tables = list(bdd_client.list_tables(dataset_ref))
                print(f"   Tables: {len(tables)}")
                for table in tables[:15]:
                    table_id = table.table_id
                    print(f"     - {table_id}")
    except Exception as e:
        print(f"Could not access basedosdados project: {e}")

    # Query INFORMATION_SCHEMA
    print()
    print("=" * 70)
    print("STEP 4: Querying INFORMATION_SCHEMA for 'pnad' tables")
    print("=" * 70)

    query = """
    SELECT 
        table_catalog,
        table_schema,
        table_name,
        table_type
    FROM 
        `b2b-opportunity-engine.region-us.INFORMATION_SCHEMA.TABLES`
    WHERE 
        table_name LIKE '%pnad%' 
        OR table_schema LIKE '%pnad%'
        OR table_name LIKE '%household%'
    LIMIT 100
    """

    try:
        results = client.query(query).result()
        if results.total_rows == 0:
            print("No tables found matching 'pnad' or 'household' pattern")
        else:
            print(f"Found {results.total_rows} tables:")
            for row in results:
                print(f"  {row.table_schema}.{row.table_name} ({row.table_type})")
    except Exception as e:
        print(f"INFORMATION_SCHEMA query failed: {e}")
        print("  (This is normal - INFORMATION_SCHEMA might not be available in this region)")

    print()
    print("=" * 70)
    print("Recommendation:")
    print("=" * 70)
    print("""
If you found tables in basedosdados project, you can access them using:
  - Full path: basedosdados.pnad_saude.microdados
  - Query from your project with cross-project access
  
Base dos Dados is a public dataset project - queries may have public data access.
""")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure:")
    print("  1. gcloud auth application-default login was run")
    print("  2. Project b2b-opportunity-engine is set as default")
    print("  3. You have BigQuery permissions")
