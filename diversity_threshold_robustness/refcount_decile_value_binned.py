#!/usr/bin/env python3
"""
Reference-count decile analysis with configurable diversity threshold.

Tests robustness of diversity threshold (e.g., T=2, T=3, T=4).

Definitions:
  diversity_count 1..(T-1) -> non-diverse
  diversity_count >= T     -> diverse
  diversity_count 0        -> excluded
"""

import os
import sys
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "data" / "attributes.duckdb"
NC_PATH = ROOT / "data" / "_n_cited.csv"
NM_PATH = ROOT / "data" / "_n_mutual.csv"

DUCKDB_TMP = ROOT / "data" / "_duckdb_tmp"

OUT_BASE = Path(__file__).resolve().parent / "results"
OUT_CSV_DIR = OUT_BASE / "csvs"
OUT_GRAPH_DIR = OUT_BASE / "graphs"

MIN_YEAR = int(os.environ.get("MIN_YEAR", "1975"))
MAX_YEAR = int(os.environ.get("MAX_YEAR", "2023"))


def compute_share_and_rate(threshold: int):
    OUT_CSV_DIR.mkdir(parents=True, exist_ok=True)
    OUT_GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    DUCKDB_TMP.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        con.execute("SET enable_progress_bar=false")
        con.execute("SET preserve_insertion_order=false")
        con.execute(f"SET temp_directory='{DUCKDB_TMP}'")

        print(f"\n=======================================================", flush=True)
        print(f"Running Decile Analysis with DIVERSITY_THRESHOLD = {threshold}", flush=True)
        print(f"Diverse: >= {threshold} fields | Non-diverse: 1..{threshold - 1} fields", flush=True)
        print(f"=======================================================", flush=True)

        con.execute(
            """
            CREATE TEMP TABLE in_window AS
            SELECT
                CAST(nc.id AS BIGINT) AS id,
                CAST(nc.n_cited AS BIGINT) AS n_cited,
                COALESCE(CAST(nm.n_mutual AS BIGINT), 0) AS n_mutual,
                a.year,
                CAST(a.diversity_count AS BIGINT) AS diversity_count
            FROM read_csv(
                ?,
                header=true,
                all_varchar=true
            ) nc
            JOIN attributes a
              ON CAST(ltrim(a.id::VARCHAR, 'W') AS BIGINT)
               = CAST(nc.id AS BIGINT)
            LEFT JOIN read_csv(
                ?,
                header=true,
                all_varchar=true
            ) nm
              ON CAST(nm.id AS BIGINT) = CAST(nc.id AS BIGINT)
            WHERE a.year BETWEEN ? AND ?
            """,
            [str(NC_PATH), str(NM_PATH), MIN_YEAR, MAX_YEAR],
        )

        con.execute(
            """
            CREATE TEMP TABLE papers AS
            SELECT * FROM in_window WHERE n_cited >= 3
            """
        )

        con.execute(
            """
            CREATE TEMP TABLE value_counts AS
            SELECT
                n_cited,
                COUNT(*) AS n_papers
            FROM papers
            GROUP BY n_cited
            ORDER BY n_cited
            """
        )

        con.execute(
            """
            CREATE TEMP TABLE value_deciles AS
            WITH positioned AS (
                SELECT
                    n_cited,
                    n_papers,
                    COALESCE(
                        SUM(n_papers) OVER (
                            ORDER BY n_cited
                            ROWS BETWEEN UNBOUNDED PRECEDING
                                 AND 1 PRECEDING
                        ),
                        0
                    ) AS papers_before,
                    SUM(n_papers) OVER () AS total_papers
                FROM value_counts
            ),
            midpoint AS (
                SELECT
                    n_cited,
                    n_papers,
                    total_papers,
                    (
                        papers_before + n_papers / 2.0
                    ) / total_papers AS midpoint_fraction
                FROM positioned
            )
            SELECT
                n_cited,
                n_papers,
                LEAST(
                    10,
                    GREATEST(
                        1,
                        CAST(
                            FLOOR(midpoint_fraction * 10.0)
                            AS INTEGER
                        ) + 1
                    )
                ) AS decile
            FROM midpoint
            """
        )

        con.execute(
            f"""
            CREATE TEMP TABLE grouped AS
            SELECT
                p.id,
                p.n_cited,
                p.n_mutual,
                d.decile,
                CASE
                    WHEN p.diversity_count BETWEEN 1 AND ({threshold} - 1)
                        THEN 'non-diverse'
                    WHEN p.diversity_count >= {threshold}
                        THEN 'diverse'
                    ELSE NULL
                END AS group_name
            FROM papers p
            JOIN value_deciles d
              ON p.n_cited = d.n_cited
            """
        )

        share = con.execute(
            """
            SELECT
                decile,
                group_name AS group,
                COUNT(*) AS n_papers,
                SUM(
                    CASE
                        WHEN n_mutual > 0 THEN 1
                        ELSE 0
                    END
                ) AS n_with_mutual,
                100.0
                * SUM(
                    CASE
                        WHEN n_mutual > 0 THEN 1
                        ELSE 0
                    END
                )
                / COUNT(*) AS share_pct
            FROM grouped
            WHERE group_name IS NOT NULL
            GROUP BY decile, group_name
            ORDER BY decile, group_name
            """
        ).fetch_df()

        rate = con.execute(
            """
            SELECT
                decile,
                group_name AS group,
                COUNT(*) AS n_papers,
                SUM(CAST(n_cited AS BIGINT)) AS sum_cited,
                SUM(CAST(n_mutual AS BIGINT)) AS sum_mutual,
                100.0
                * SUM(CAST(n_mutual AS BIGINT))
                / NULLIF(
                    SUM(CAST(n_cited AS BIGINT)),
                    0
                ) AS rate_pct
            FROM grouped
            WHERE group_name IS NOT NULL
            GROUP BY decile, group_name
            ORDER BY decile, group_name
            """
        ).fetch_df()

        n_total = con.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        n_diverse = con.execute(f"SELECT COUNT(*) FROM grouped WHERE group_name = 'diverse'").fetchone()[0]
        n_nondiverse = con.execute(f"SELECT COUNT(*) FROM grouped WHERE group_name = 'non-diverse'").fetchone()[0]

        print(f"Total Cohort Papers: {n_total:,}")
        print(f"Diverse (>= {threshold} fields):     {n_diverse:,} ({100*n_diverse/n_total:.2f}%)")
        print(f"Non-diverse (1..{threshold-1} fields): {n_nondiverse:,} ({100*n_nondiverse/n_total:.2f}%)")

    finally:
        con.close()

    return share, rate


def write_outputs(share: pd.DataFrame, rate: pd.DataFrame, threshold: int):
    share_csv = OUT_CSV_DIR / f"refcount_decile_dvn_share_t{threshold}.csv"
    share_png = OUT_GRAPH_DIR / f"refcount_decile_dvn_share_t{threshold}.png"

    rate_csv = OUT_CSV_DIR / f"refcount_decile_dvn_rate_t{threshold}.csv"
    rate_png = OUT_GRAPH_DIR / f"refcount_decile_dvn_rate_t{threshold}.png"

    share.to_csv(share_csv, index=False)
    rate.to_csv(rate_csv, index=False)

    # Share plot
    fig, ax = plt.subplots(figsize=(10, 6))
    for group in ["non-diverse", "diverse"]:
        sub = share[share["group"] == group].sort_values("decile")
        label = f"diverse (≥{threshold} fields)" if group == "diverse" else f"non-diverse (1–{threshold-1} fields)"
        ax.plot(
            sub["decile"],
            sub["share_pct"],
            marker="o",
            linewidth=2,
            label=label,
        )
    ax.set_xlim(0.5, 10.5)
    ax.set_xticks(range(1, 11))
    ax.set_xlabel("Reference-count decile")
    ax.set_ylabel("Share of papers with any mutual citation (%)")
    ax.set_title(
        f"Share of papers with any mutual citation by reference-count decile\n"
        f"(Threshold T={threshold}: Diverse ≥{threshold} fields vs Non-diverse 1–{threshold-1} fields)"
    )
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(title="Group")
    fig.tight_layout()
    fig.savefig(share_png, dpi=200)
    plt.close(fig)

    # Rate plot
    fig, ax = plt.subplots(figsize=(10, 6))
    for group in ["non-diverse", "diverse"]:
        sub = rate[rate["group"] == group].sort_values("decile")
        label = f"diverse (≥{threshold} fields)" if group == "diverse" else f"non-diverse (1–{threshold-1} fields)"
        ax.plot(
            sub["decile"],
            sub["rate_pct"],
            marker="o",
            linewidth=2,
            label=label,
        )
    ax.set_xlim(0.5, 10.5)
    ax.set_xticks(range(1, 11))
    ax.set_xlabel("Reference-count decile")
    ax.set_ylabel("Mutual-citation rate (% of references reciprocated)")
    ax.set_title(
        f"Mutual-citation rate by reference-count decile\n"
        f"(Threshold T={threshold}: Diverse ≥{threshold} fields vs Non-diverse 1–{threshold-1} fields)"
    )
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(title="Group")
    fig.tight_layout()
    fig.savefig(rate_png, dpi=200)
    plt.close(fig)

    print(f"Saved: {share_csv}")
    print(f"Saved: {rate_csv}")
    print(f"Saved: {share_png}")
    print(f"Saved: {rate_png}")


def main():
    thresholds = [2, 4]
    if len(sys.argv) > 1:
        thresholds = [int(sys.argv[1])]

    for t in thresholds:
        share, rate = compute_share_and_rate(t)
        write_outputs(share, rate, t)


if __name__ == "__main__":
    main()

