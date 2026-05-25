"""
Scatter plot: percent of each paper's citations that are mutual citations,
by publication year, with markers split by diversity.

For each paper in the attribute table that has at least one outbound edge:
  x = publication year
  y = (number of its outbound edges that are part of a mutual pair)
      / (total number of its outbound edges) * 100

Markers:
  'x' for diverse papers      (cite 3+ distinct fields)
  '.' for non-diverse papers  (cite 2 or fewer distinct fields)

Mutual edge definition: an outbound edge A -> B is mutual if the reverse
edge B -> A is also present in the edge list. Edges to papers outside the
in-set are inherently non-mutual (we have no reverse edge to find).

Yearly means for each group are overlaid as solid lines so the trend is
visible through the dense scatter of ~750k papers.

Inputs:
  data/clean_dataset.duckdb (with papers.diverse populated by
                             research/classify_diversity.py)

Outputs:
  outputs/mutual_share_by_diversity.png
  prints summary stats to stdout
"""

import duckdb
import matplotlib.pyplot as plt
from pathlib import Path

DB = "data/clean_dataset.duckdb"
OUT = "outputs/mutual_share_by_diversity.png"

con = duckdb.connect(DB, read_only=True)

cols = [r[0] for r in con.execute("DESCRIBE papers").fetchall()]
if "diverse" not in cols:
    raise SystemExit(
        "papers.diverse column not found. Run research/classify_diversity.py first."
    )

print("Computing per-paper mutual-edge counts (this can take a couple minutes)...")
rows = con.execute("""
    WITH mutual_edges AS (
        SELECT a.source, a.target FROM edges a
        JOIN edges b ON a.source = b.target AND a.target = b.source
    ),
    out_counts AS (
        SELECT source AS pid, COUNT(*) AS n_out FROM edges GROUP BY source
    ),
    mut_counts AS (
        SELECT source AS pid, COUNT(*) AS n_mut FROM mutual_edges GROUP BY source
    )
    SELECT
        p.year,
        p.diverse,
        o.n_out,
        COALESCE(m.n_mut, 0) AS n_mut
    FROM papers p
    JOIN out_counts o ON o.pid = p.id
    LEFT JOIN mut_counts m ON m.pid = p.id
    WHERE p.year IS NOT NULL AND o.n_out > 0
""").fetchall()

print(f"  {len(rows):,} papers have at least one outbound edge")

# Split by diversity
years_d, pct_d = [], []
years_n, pct_n = [], []
for year, diverse, n_out, n_mut in rows:
    pct = n_mut / n_out * 100
    if diverse:
        years_d.append(year)
        pct_d.append(pct)
    else:
        years_n.append(year)
        pct_n.append(pct)

print(f"  diverse:     {len(years_d):>9,} papers, "
      f"mean pct-mutual = {sum(pct_d) / max(len(pct_d), 1):.3f}%")
print(f"  not diverse: {len(years_n):>9,} papers, "
      f"mean pct-mutual = {sum(pct_n) / max(len(pct_n), 1):.3f}%")


def yearly_means(years, pcts):
    sums, counts = {}, {}
    for y, p in zip(years, pcts):
        sums[y] = sums.get(y, 0) + p
        counts[y] = counts.get(y, 0) + 1
    xs = sorted(sums)
    ys = [sums[y] / counts[y] for y in xs]
    return xs, ys


xs_d, ys_d = yearly_means(years_d, pct_d)
xs_n, ys_n = yearly_means(years_n, pct_n)

# Plot
fig, ax = plt.subplots(figsize=(14, 7))

# Underlying scatter (heavy alpha to make density readable)
ax.scatter(years_n, pct_n, marker=".", s=8, alpha=0.10, color="steelblue",
           label=f"Not diverse: {len(years_n):,} papers")
ax.scatter(years_d, pct_d, marker="x", s=14, alpha=0.20, color="coral",
           label=f"Diverse: {len(years_d):,} papers")

# Yearly-mean trend lines
ax.plot(xs_n, ys_n, color="darkblue", linewidth=2.5, marker="o",
        markersize=4, label="Not diverse: yearly mean", zorder=5)
ax.plot(xs_d, ys_d, color="darkred", linewidth=2.5, marker="x",
        markersize=7, label="Diverse: yearly mean", zorder=5)

ax.set_xlabel("Publication year")
ax.set_ylabel("Percent of citations that are mutual citations (%)")
ax.set_title("Per-paper mutual-citation share by year and diversity\n"
             "(each marker is one paper; lines are yearly means)")
ax.legend(loc="upper right", fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
Path("outputs").mkdir(exist_ok=True)
plt.savefig(OUT, dpi=150)
print(f"\nSaved {OUT}")
