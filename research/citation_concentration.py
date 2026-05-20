"""
Citation-concentration analysis.

Hypothesis: the secular decline in mutual citation rates is partly driven by
citations becoming more concentrated on a smaller set of "winner" papers
over time. If the top 1% of papers absorbs an ever-larger share of inbound
citations, the average paper is less and less likely to be in a citation
loop with any other average paper — mutual pair formation drops
mechanically without anyone's behavior changing.

We measure concentration two ways:

  1. Gini coefficient of inbound citation counts within each publication
     cohort. Gini ranges from 0 (perfectly uniform) to 1 (one paper has
     all citations). Higher = more concentrated.

  2. Top-N% share: what fraction of total inbound citations is captured by
     the top 1%, 5%, 10% of papers in the cohort? Cleaner to read than
     Gini.

To control for citation-lag (recent papers have had less time to
accumulate citations), we restrict the comparison to *within-year*
citations: papers from year Y receive citations from papers also in
year Y. This puts every year on the same lag clock and is the same
restriction we used to identify the 2020 COVID anomaly.
"""

import duckdb
import numpy as np

con = duckdb.connect("data/citations.duckdb", read_only=True)


def gini(values):
    """Standard Gini coefficient. Expects an array of non-negative numbers,
    including zeros. Returns 0 (perfectly equal) to 1 (one element has it all)."""
    values = np.array(values, dtype=float)
    if values.size == 0 or values.sum() == 0:
        return 0.0
    v = np.sort(values)
    n = v.size
    # standard formula
    cum = np.cumsum(v)
    return (n + 1 - 2 * (cum.sum() / cum[-1])) / n


# -------- 1. within-year citation concentration --------
# for each year Y, compute the distribution of "how many citations from
# year Y did each year-Y paper receive"
print("=" * 78)
print("1. WITHIN-YEAR CITATION CONCENTRATION (lag-controlled)")
print("=" * 78)
print("For each year Y: among papers published in Y, distribution of inbound")
print("citations received from other year-Y papers.\n")

print(f"{'year':<6}{'papers':>9}{'with_cite':>10}{'%':>6}{'mean':>7}"
      f"{'median':>7}{'p95':>6}{'p99':>6}{'max':>6}{'gini':>7}"
      f"{'top1%':>7}{'top5%':>7}{'top10%':>8}")

for y in range(2020, 2025):
    rows = con.execute(f"""
        WITH targets AS (
            SELECT id FROM works WHERE year = {y}
        ),
        counts AS (
            SELECT t.id, COUNT(c.citing_id) AS n
            FROM targets t
            LEFT JOIN citations c ON c.cited_id = t.id
            LEFT JOIN works wc ON c.citing_id = wc.id AND wc.year = {y}
            WHERE wc.year = {y} OR c.citing_id IS NULL
            GROUP BY t.id
        )
        SELECT n FROM counts
    """).fetchall()
    counts = np.array([r[0] for r in rows], dtype=int)

    if counts.size == 0:
        continue

    nonzero = counts[counts > 0]
    g = gini(counts)
    total = counts.sum()
    sorted_desc = np.sort(counts)[::-1]
    n = counts.size

    def top_share(pct):
        k = max(1, int(n * pct / 100))
        return sorted_desc[:k].sum() / total * 100 if total else 0.0

    print(f"{y:<6}{n:>9,}{nonzero.size:>10,}{nonzero.size/n*100:>5.1f}%"
          f"{counts.mean():>7.2f}{np.median(counts):>7.0f}"
          f"{np.percentile(counts, 95):>6.0f}{np.percentile(counts, 99):>6.0f}"
          f"{counts.max():>6,}{g:>7.4f}"
          f"{top_share(1):>6.1f}%{top_share(5):>6.1f}%{top_share(10):>7.1f}%")


# -------- 2. total inbound citation concentration (all citing years) --------
# this includes accumulation across years, so 2024 will look less
# concentrated just because less time has passed. Mostly diagnostic.
print()
print("=" * 78)
print("2. ALL-INBOUND CITATION CONCENTRATION (cumulative, NOT lag-controlled)")
print("=" * 78)
print("Includes all years of citation accumulation. Useful for cross-check but")
print("can't be compared across years without caveats.\n")

print(f"{'year':<6}{'papers':>9}{'with_cite':>10}{'%':>6}{'mean':>7}"
      f"{'median':>7}{'p95':>6}{'p99':>6}{'max':>6}{'gini':>7}"
      f"{'top1%':>7}{'top5%':>7}{'top10%':>8}")

for y in range(2020, 2025):
    rows = con.execute(f"""
        WITH targets AS (
            SELECT id FROM works WHERE year = {y}
        ),
        counts AS (
            SELECT t.id, COUNT(c.citing_id) AS n
            FROM targets t
            LEFT JOIN citations c ON c.cited_id = t.id
            GROUP BY t.id
        )
        SELECT n FROM counts
    """).fetchall()
    counts = np.array([r[0] for r in rows], dtype=int)

    nonzero = counts[counts > 0]
    g = gini(counts)
    total = counts.sum()
    sorted_desc = np.sort(counts)[::-1]
    n = counts.size

    def top_share(pct):
        k = max(1, int(n * pct / 100))
        return sorted_desc[:k].sum() / total * 100 if total else 0.0

    print(f"{y:<6}{n:>9,}{nonzero.size:>10,}{nonzero.size/n*100:>5.1f}%"
          f"{counts.mean():>7.2f}{np.median(counts):>7.0f}"
          f"{np.percentile(counts, 95):>6.0f}{np.percentile(counts, 99):>6.0f}"
          f"{counts.max():>6,}{g:>7.4f}"
          f"{top_share(1):>6.1f}%{top_share(5):>6.1f}%{top_share(10):>7.1f}%")


# -------- 3. interpretation --------
print()
print("=" * 78)
print("INTERPRETATION GUIDE")
print("=" * 78)
print("""
If Gini and top-1% share are RISING from 2021 -> 2024 (in within-year, the
lag-controlled view), that's evidence citations are becoming more
concentrated. A mechanical implication: if a fixed budget of citations is
flowing to fewer winners, the average paper-pair has lower probability of
being a mutual pair, even with no behavior change. This would partially
explain the -13.2%/yr secular decline.

If Gini is roughly flat from 2021 -> 2024, then the average citation
'spread' isn't changing and concentration cannot be the mechanism.
""")
