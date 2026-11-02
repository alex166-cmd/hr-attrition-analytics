"""
Build a SQLite database from the clean CSV and run the SQL analysis.

Input : data/clean/employees_clean.csv, sql/01_schema.sql, sql/02_analysis_queries.sql
Output: db/hr_analytics.db
        outputs/query_results/<query name>.csv  (one file per query)
"""
import re
import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "hr_analytics.db"
OUT = ROOT / "outputs" / "query_results"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(ROOT / "data" / "clean" / "employees_clean.csv")

con = sqlite3.connect(DB)

# create tables, and then load the cleaned rows into them
con.executescript((ROOT / "sql" / "01_schema.sql").read_text())
df.to_sql("employees", con, if_exists="append", index=False)
n = con.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
print(f"Loaded {n:,} employees into {DB.name}")

# split the query file on the '-- name:' markers and run each query
text = (ROOT / "sql" / "02_analysis_queries.sql").read_text()
blocks = re.split(r"^-- name:\s*", text, flags=re.M)[1:]

for block in blocks:
    name, _, sql = block.partition("\n")
    result = pd.read_sql_query(sql, con)
    result.to_csv(OUT / f"{name.strip()}.csv", index=False)
    print(f"  {name.strip():45s} {len(result):>3} rows")

con.close()
print("Done. Query results are in outputs/query_results/")
