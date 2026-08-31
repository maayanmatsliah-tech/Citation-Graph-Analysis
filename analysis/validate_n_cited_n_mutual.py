"""
Validate build_n_cited_n_mutual.py's reconstruction against the REAL,
already-existing data/_n_cited.csv / data/_n_mutual.csv.

Run build_n_cited_n_mutual.py first, then this. Checks:
  - row counts match
  - sum(n_cited), sum(n_mutual) match
  - a random sample of ids has exactly matching values

If DEDUPE=1 (the default) doesn't match, re-run build_n_cited_n_mutual.py with
DEDUPE=0 and validate again -- that's the most likely source of divergence
given the repo has both conventions in use elsewhere.

Env:
  REAL_NCITED   default data/_n_cited.csv
  REAL_NMUTUAL  default data/_n_mutual.csv
  RECON_NCITED  default data/_n_cited_reconstructed.csv
  RECON_NMUTUAL default data/_n_mutual_reconstructed.csv
  SAMPLE_N      default 50
"""

import os
import random

import duckdb

REAL_NCITED = os.environ.get("REAL_NCITED", "data/_n_cited.csv")
REAL_NMUTUAL = os.environ.get("REAL_NMUTUAL", "data/_n_mutual.csv")
RECON_NCITED = os.environ.get("RECON_NCITED", "data/_n_cited_reconstructed.csv")
RECON_NMUTUAL = os.environ.get("RECON_NMUTUAL", "data/_n_mutual_reconstructed.csv")
SAMPLE_N = int(os.environ.get("SAMPLE_N", "50"))


def compare(name, real_path, recon_path, value_col, con):
    print(f"\n=== {name} ===")
    real_n, real_sum = con.execute(
        f"SELECT count(*), sum(CAST({value_col} AS BIGINT)) "
        f"FROM read_csv('{real_path}', header=true, all_varchar=true)"
    ).fetchone()
    recon_n, recon_sum = con.execute(
        f"SELECT count(*), sum(CAST({value_col} AS BIGINT)) "
        f"FROM read_csv('{recon_path}', header=true, all_varchar=true)"
    ).fetchone()
    print(f"  rows:  real={real_n:,}  reconstructed={recon_n:,}  "
          f"{'MATCH' if real_n == recon_n else 'MISMATCH'}")
    print(f"  sum:   real={real_sum:,}  reconstructed={recon_sum:,}  "
          f"{'MATCH' if real_sum == recon_sum else 'MISMATCH'}")

    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE real AS
        SELECT CAST(id AS BIGINT) AS id, CAST({value_col} AS BIGINT) AS v
        FROM read_csv('{real_path}', header=true, all_varchar=true)
    """)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE recon AS
        SELECT CAST(id AS BIGINT) AS id, CAST({value_col} AS BIGINT) AS v
        FROM read_csv('{recon_path}', header=true, all_varchar=true)
    """)
    diff_n = con.execute("""
        SELECT count(*) FROM real r FULL OUTER JOIN recon c ON c.id = r.id
        WHERE r.v IS DISTINCT FROM c.v
    """).fetchone()[0]
    print(f"  ids with a differing (or missing-on-one-side) value: {diff_n:,}")

    sample = con.execute(f"""
        SELECT r.id, r.v AS real_v, c.v AS recon_v
        FROM real r JOIN recon c ON c.id = r.id
        USING SAMPLE {SAMPLE_N}
    """).fetchall()
    mismatches = [row for row in sample if row[1] != row[2]]
    print(f"  spot-check {len(sample)} random ids: "
          f"{len(sample) - len(mismatches)} match, {len(mismatches)} differ")
    for row in mismatches[:5]:
        print(f"    id={row[0]}  real={row[1]}  reconstructed={row[2]}")


def main():
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    compare("n_cited", REAL_NCITED, RECON_NCITED, "n_cited", con)
    compare("n_mutual", REAL_NMUTUAL, RECON_NMUTUAL, "n_mutual", con)
    con.close()


if __name__ == "__main__":
    main()