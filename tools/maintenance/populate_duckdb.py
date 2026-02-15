import duckdb

con = duckdb.connect("data/analytics.duckdb")

con.execute("""
CREATE TABLE IF NOT EXISTS companies_agg_uf AS
SELECT * FROM read_parquet('data/processed/companies_agg_uf.parquet')
""")

con.execute("""
CREATE TABLE IF NOT EXISTS companies_agg AS
SELECT * FROM read_parquet('data/processed/companies_agg.parquet')
""")

print("OK: tables created")
print("Tables in DB:", con.execute("SHOW TABLES").fetchall())

con.close()
