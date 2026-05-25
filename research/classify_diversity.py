"""
Add a `diverse` column to the papers attribute table.

For each paper, count the number of DISTINCT fields it cites among the
papers in the attribute table. Classify:

  diverse     = TRUE   if the paper cites work from 3 or more distinct fields
  diverse     = FALSE  if the paper cites work from 2 or fewer distinct fields
                       (also FALSE if the paper has no in-set citations at all)

Note: the edge list contains all outbound edges, including edges to
papers not in our attribute table. We can only count a cited paper's
field if that paper is in our attribute table, so this classification
is computed on the *intersection*: each paper's distinct-field count
is among its references that we happen to have field information for.
Papers whose references are mostly outside the attribute table will
look "not diverse" even if their real reference list is diverse — this
limitation is reported in the coverage stats below.

Inputs:
  data/clean_dataset.duckdb (created by data/build_clean_dataset.py)

Outputs:
  data/clean_dataset.duckdb  -- papers table updated in place with new column
  data/papers.parquet        -- re-exported with the new column
  prints a summary of the diversity distribution
"""

import duckdb
from pathlib import Path

DB = "data/clean_dataset.duckdb"
PAPERS_PARQUET = "data/papers.parquet"

if not Path(DB).exists():
    raise SystemExit(
        f"{DB} does not exist. Run data/build_clean_dataset.py first."
    )

con = duckdb.connect(DB)

n_papers = con.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
n_edges = con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
print(f"Loaded {n_papers:,} papers, {n_edges:,} edges from {DB}")

# Coverage diagnostic: of all outbound edges, what fraction have a
# target that's in our attribute table?
covered = con.execute("""
    SELECT COUNT(*) FROM edges e
    JOIN papers p ON e.target = p.id
""").fetchone()[0]
coverage_pct = covered / n_edges * 100 if n_edges else 0
print(f"\nEdge coverage: {covered:,} of {n_edges:,} outbound edges "
      f"target an in-set paper ({coverage_pct:.1f}%)")
print("Diversity is computed only on in-set citations (the rest are invisible).")

# Rebuild the papers table with the new column derived in one CTE.
# This is cleaner than UPDATE and atomic.
print("\nComputing distinct-field-cited per paper and rebuilding papers table...")
con.execute("""
    CREATE OR REPLACE TABLE papers_new AS
    WITH diversity AS (
        SELECT
            e.source AS pid,
            COUNT(DISTINCT p_cited.field) AS n_fields_cited
        FROM edges e
        JOIN papers p_cited ON e.target = p_cited.id
        WHERE p_cited.field IS NOT NULL
        GROUP BY e.source
    )
    SELECT
        p.id,
        p.year,
        p.field,
        p.title,
        COALESCE(d.n_fields_cited, 0) >= 3 AS diverse
    FROM papers p
    LEFT JOIN diversity d ON p.id = d.pid
""")

con.execute("DROP TABLE papers")
con.execute("ALTER TABLE papers_new RENAME TO papers")
con.execute("CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year)")

# Summary
print("\nOverall diversity distribution:")
totals = con.execute("""
    SELECT diverse, COUNT(*) FROM papers GROUP BY diverse ORDER BY diverse DESC
""").fetchall()
total = sum(c for _, c in totals)
for d, c in totals:
    label = "diverse (cites 3+ fields)" if d else "not diverse (cites <=2 fields or 0 in-set refs)"
    print(f"  {label:<55} {c:>9,}  ({c/total*100:>5.1f}%)")

print("\nDiversity by year (sample of every 10th year):")
rows = con.execute("""
    SELECT year,
           COUNT(*) AS n,
           SUM(CASE WHEN diverse THEN 1 ELSE 0 END) AS n_diverse
    FROM papers
    WHERE year IS NOT NULL
    GROUP BY year ORDER BY year
""").fetchall()
print(f"  {'year':<6}{'n papers':>10}{'diverse':>10}{'pct diverse':>14}")
for y, n, nd in rows:
    if y % 10 == 0 or y >= 2020:
        print(f"  {y:<6}{n:>10,}{nd:>10,}{nd/n*100:>13.1f}%")

# Re-export to parquet
print(f"\nRe-exporting papers table with the new column to {PAPERS_PARQUET}...")
con.execute(
    f"COPY (SELECT * FROM papers ORDER BY year, id) TO '{PAPERS_PARQUET}' "
    "(FORMAT PARQUET, COMPRESSION ZSTD)"
)

size_mb = Path(PAPERS_PARQUET).stat().st_size / 1e6
print(f"  papers.parquet: {size_mb:.1f} MB")
print("Done.")
