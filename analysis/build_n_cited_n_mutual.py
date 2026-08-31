"""
14. Reconstructed: per-paper n_cited / n_mutual counts, feeding
    refcount_decile_value_binned.py (step 15/14 in the pipeline ordering).

RECONSTRUCTION NOTICE: no committed version of this script was found anywhere
in git history (full --all pickaxe search on both filenames + the ncited
computation pattern), so this is rebuilt from the exact schema
refcount_decile_value_binned.py expects, not recovered from source. See the
validation step below before trusting this over the existing _n_cited.csv /
_n_mutual.csv already on disk.

Definitions (matching plot_mean_mutual_and_diversity.py's ncited/nmut temp
tables, the closest existing precedent in the repo):
  n_cited   number of DISTINCT papers a source cites, excluding self-citation.
            Targets are deduped via list_distinct before counting.
  n_mutual  number of mutual pairs a paper belongs to (from mutual_pairs.csv;
            each pair contributes +1 to BOTH of its papers; absent = 0).

id format: bare integer, 'W' prefix stripped -- confirmed necessary because
refcount_decile_value_binned.py does a direct CAST(id AS BIGINT) on both
files with no ltrim, unlike every other file in the pipeline.

VALIDATION STATUS: run against the real data/_n_cited.csv and
data/_n_mutual.csv on 2026-08-30. n_cited sum matched exactly
(2,962,157,255) on the first pass with DEDUPE=1; row count was off by
exactly 108,151, which matched the count of n_cited=0 rows in the
reconstructed output -- confirming the original script filtered those
out (now applied below), not that DEDUPE was the wrong choice. Re-run
validate_n_cited_n_mutual.py after any further changes to confirm rows
and sums both match, plus n_mutual.

VALIDATION (do this before relying on this script further):
  1. Run this script -- it writes to *_reconstructed.csv, NOT the real files,
     so nothing existing is overwritten.
  2. Compare against the real data/_n_cited.csv / data/_n_mutual.csv using
     validate_n_cited_n_mutual.py: row counts, sums, and a random spot-check.
  3. If n_cited still diverges, the likely culprit is the dedup choice --
     some other scripts in this repo (e.g.
     plot_mutual_paper_share_by_diversity.py) use RAW (non-deduped)
     target-list length instead. Try DEDUPE=0.

Env:
  EDGES         default data/edges.csv
  PAIRS         default data/mutual_pairs.csv
  OUT_NCITED    default data/_n_cited_reconstructed.csv
  OUT_NMUTUAL   default data/_n_mutual_reconstructed.csv
  MEM           default 10GB
  DEDUPE        default 1 (distinct targets); set 0 to use raw list length instead
"""

import os

import duckdb

EDGES = os.environ.get("EDGES", "data/edges.csv")
PAIRS = os.environ.get("PAIRS", "data/mutual_pairs.csv")
OUT_NCITED = os.environ.get("OUT_NCITED", "data/_n_cited_reconstructed.csv")
OUT_NMUTUAL = os.environ.get("OUT_NMUTUAL", "data/_n_mutual_reconstructed.csv")
MEM = os.environ.get("MEM", "10GB")
DUCKDB_TMP = os.environ.get("DUCKDB_TMP", "data/_duckdb_tmp")
DEDUPE = os.environ.get("DEDUPE", "1") == "1"


def main():
    os.makedirs(DUCKDB_TMP, exist_ok=True)
    os.makedirs(os.path.dirname(OUT_NCITED) or ".", exist_ok=True)

    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false")
    con.execute(f"SET memory_limit='{MEM}'")
    con.execute(f"SET temp_directory='{DUCKDB_TMP}'")
    con.execute("SET preserve_insertion_order=false")

    print(f"1/2 computing n_cited per source (dedupe={DEDUPE}) -> {OUT_NCITED} ...",
          flush=True)
    if DEDUPE:
        n_cited_expr = """
            len(list_distinct(string_split(targets, ';')))
              - CASE WHEN list_contains(list_distinct(string_split(targets, ';')), source)
                     THEN 1 ELSE 0 END
        """
    else:
        n_cited_expr = """
            len(string_split(targets, ';'))
              - CASE WHEN list_contains(string_split(targets, ';'), source)
                     THEN 1 ELSE 0 END
        """
    # CONFIRMED via validation against the real data/_n_cited.csv: the original
    # script excluded n_cited=0 rows (papers whose entire target list was
    # self-citations / exact duplicates, leaving nothing after dedup). Without
    # this filter, sums matched exactly but row count was off by precisely
    # 108,151 -- the count of n_cited=0 rows. Confirms this filter, not a
    # different n_cited definition, was the source of the discrepancy.
    con.execute(f"""
        COPY (
            SELECT id, n_cited FROM (
                SELECT CAST(ltrim(source, 'W') AS BIGINT) AS id,
                       ({n_cited_expr})                    AS n_cited
                FROM read_csv('{EDGES}', header=true, all_varchar=true, ignore_errors=true)
            )
            WHERE n_cited > 0
        ) TO '{OUT_NCITED}' (HEADER, DELIMITER ',')
    """)

    print(f"2/2 computing n_mutual per paper -> {OUT_NMUTUAL} ...", flush=True)
    con.execute(f"""
        COPY (
            SELECT id, count(*) AS n_mutual FROM (
                SELECT CAST(ltrim(paper_a, 'W') AS BIGINT) AS id
                FROM read_csv('{PAIRS}', header=true, all_varchar=true)
                UNION ALL
                SELECT CAST(ltrim(paper_b, 'W') AS BIGINT) AS id
                FROM read_csv('{PAIRS}', header=true, all_varchar=true)
            )
            GROUP BY id
        ) TO '{OUT_NMUTUAL}' (HEADER, DELIMITER ',')
    """)

    n1 = con.execute(f"SELECT count(*) FROM read_csv('{OUT_NCITED}', header=true)").fetchone()[0]
    n2 = con.execute(f"SELECT count(*) FROM read_csv('{OUT_NMUTUAL}', header=true)").fetchone()[0]
    con.close()
    print(f"\nwrote {n1:,} rows to {OUT_NCITED}")
    print(f"wrote {n2:,} rows to {OUT_NMUTUAL}")
    print("\nNEXT STEP: validate against the existing real files before trusting this --")
    print("  see the VALIDATION section in this script's docstring.")


if __name__ == "__main__":
    main()