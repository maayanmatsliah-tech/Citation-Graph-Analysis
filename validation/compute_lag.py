#!/usr/bin/env python3
"""
Citation-lag distribution for mutual pairs.

For each mutual pair {A, B}, computes the gap between the two papers'
publication years:

    gap = abs(year_A - year_B)

Reports the cumulative share of mutual pairs whose publication-year gap is:

    - 0 years (same year)
    - <= 1 year
    - <= 2 years
    - <= 3 years

This provides a simple censoring check: mutuality can only be observed once
both papers exist, so pairs involving papers near the corpus's 2023 endpoint
may have had less opportunity to become mutual.

Inputs:
  data/mutual_pairs.csv
  data/attributes.duckdb

Output:
  figures/csvs/citation_lag_distribution.csv

The attributes database and input CSV are read-only. The script does not
modify them.

Environment variables:
  PAIRS  default: data/mutual_pairs.csv
  ATTR   default: data/attributes.duckdb
  OUT    default: figures/csvs/citation_lag_distribution.csv
  MEM    default: 10GB
"""

import os

import duckdb


PAIRS = os.environ.get(
    "PAIRS",
    "data/mutual_pairs.csv",
)

ATTR = os.environ.get(
    "ATTR",
    "data/attributes.duckdb",
)

OUT = os.environ.get(
    "OUT",
    "figures/csvs/citation_lag_distribution.csv",
)

MEM = os.environ.get(
    "MEM",
    "10GB",
)


def compute():
    os.makedirs("data/_duckdb_tmp", exist_ok=True)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)

    con = duckdb.connect()

    try:
        con.execute("SET enable_progress_bar=false")
        con.execute(f"SET memory_limit='{MEM}'")
        con.execute("SET temp_directory='data/_duckdb_tmp'")
        con.execute("SET preserve_insertion_order=false")

        # Read the attributes database in read-only mode.
        con.execute(
            f"ATTACH '{ATTR}' AS a (READ_ONLY)"
        )

        print("Loading mutual pairs and publication years...", flush=True)

        # Join each mutual pair to the publication year of both papers.
        #
        # IDs are normalized to bare BIGINT values on both sides so that
        # W123456 and 123456 are treated as the same paper ID.
        con.execute(
            f"""
            CREATE TEMP TABLE pair_years AS
            SELECT
                ya.year AS year_a,
                yb.year AS year_b,
                abs(ya.year - yb.year) AS gap
            FROM read_csv(
                '{PAIRS}',
                header=true,
                all_varchar=true
            ) p
            JOIN a.attributes ya
              ON CAST(ltrim(p.paper_a, 'W') AS BIGINT)
               = CAST(ltrim(ya.id::VARCHAR, 'W') AS BIGINT)
            JOIN a.attributes yb
              ON CAST(ltrim(p.paper_b, 'W') AS BIGINT)
               = CAST(ltrim(yb.id::VARCHAR, 'W') AS BIGINT)
            """
        )

        # Total number of mutual pairs for the denominator.
        n_total = con.execute(
            """
            SELECT COUNT(*)
            FROM pair_years
            """
        ).fetchone()[0]

        # Cumulative counts at each publication-year-gap threshold.
        row = con.execute(
            """
            SELECT
                SUM(
                    CASE WHEN gap = 0 THEN 1 ELSE 0 END
                ) AS n_within_0,

                SUM(
                    CASE WHEN gap <= 1 THEN 1 ELSE 0 END
                ) AS n_within_1,

                SUM(
                    CASE WHEN gap <= 2 THEN 1 ELSE 0 END
                ) AS n_within_2,

                SUM(
                    CASE WHEN gap <= 3 THEN 1 ELSE 0 END
                ) AS n_within_3

            FROM pair_years
            """
        ).fetchone()

        n0, n1, n2, n3 = row

        return n0, n1, n2, n3, n_total

    finally:
        con.close()


def write_outputs(rows):
    import csv

    n0, n1, n2, n3, n_total = rows

    labels = [
        "same_year",
        "within_1_year",
        "within_2_years",
        "within_3_years",
    ]

    counts = [
        n0,
        n1,
        n2,
        n3,
    ]

    with open(OUT, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(
            [
                "threshold",
                "n_pairs",
                "n_total",
                "cumulative_pct",
            ]
        )

        for label, n in zip(labels, counts):
            pct = (
                100.0 * n / n_total
                if n_total
                else 0.0
            )

            writer.writerow(
                [
                    label,
                    n,
                    n_total,
                    f"{pct:.4f}",
                ]
            )

    print(f"wrote {OUT}")


def main():
    n0, n1, n2, n3, n_total = compute()

    print()
    print(f"total mutual pairs: {n_total:,}")
    print()

    print(
        f"{'threshold':>18} "
        f"{'n_pairs':>12} "
        f"{'cumulative_pct':>16}"
    )

    for label, n in zip(
        [
            "same year",
            "within 1 year",
            "within 2 years",
            "within 3 years",
        ],
        [
            n0,
            n1,
            n2,
            n3,
        ],
    ):
        pct = (
            100.0 * n / n_total
            if n_total
            else 0.0
        )

        print(
            f"{label:>18} "
            f"{n:>12,} "
            f"{pct:>15.1f}%"
        )

    write_outputs(
        (n0, n1, n2, n3, n_total)
    )


if __name__ == "__main__":
    main()
