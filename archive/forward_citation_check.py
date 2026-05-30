"""
Forward-citation validity check for the gap=1 mutual-pair finding.

Context: research/year_gap_analysis.py found that one-year-apart (gap=1)
mutual pairs are declining ~24%/year, much faster than same-year (gap=0)
pairs at ~11%/year. A gap=1 mutual pair anchored to pair_year=Y consists
of two citation edges:
  - a normal backward citation: year-Y paper -> year-(Y-1) paper
  - a structurally unusual FORWARD citation: year-(Y-1) paper -> year-Y paper
    (the earlier paper must have cited the later paper, only possible via
     preprint awareness or late editing)

If forward citations across the entire citation graph (not just mutual pairs)
are collapsing on their own, then the gap=1 mutual decline is just inherited
from a broader forward-citation shift — not a mutual-pair-specific story. If
forward citations are roughly stable while gap=1 mutual pairs collapse,
something specific to mutual reciprocity is dropping.

Convention used here: gap = cited_year - citing_year.
  gap > 0  → forward citation (earlier paper citing later paper) — unusual
  gap = 0  → same-year citation
  gap < 0  → backward citation (normal)
"""

import duckdb
import numpy as np
from scipy.stats import linregress

con = duckdb.connect("data/citations.duckdb")

rows = con.execute("""
    SELECT
        w_citing.year AS citing_year,
        w_cited.year  AS cited_year,
        COUNT(*) AS n
    FROM citations c
    JOIN works w_citing ON c.citing_id = w_citing.id
    JOIN works w_cited  ON c.cited_id  = w_cited.id
    WHERE c.citing_id <> c.cited_id
      AND w_citing.year BETWEEN 2020 AND 2024
      AND w_cited.year  BETWEEN 2020 AND 2024
    GROUP BY w_citing.year, w_cited.year
""").fetchall()

papers_by_year = dict(con.execute("""
    SELECT year, COUNT(*) FROM works
    WHERE year BETWEEN 2020 AND 2024
    GROUP BY year
""").fetchall())

years = sorted(papers_by_year)
counts = {y: {} for y in years}
for cy, dy, n in rows:
    counts[cy][dy - cy] = counts[cy].get(dy - cy, 0) + n

all_gaps = sorted({g for y in years for g in counts[y].keys()})

# ---------- raw citation counts by (citing_year, gap) ----------
print("=== Citation counts by (citing_year, gap = cited_year - citing_year) ===")
print("Positive gap = FORWARD citation (the rare half of every gap=1 mutual pair)")
print(f"{'gap':>5}  " + "  ".join(f"{y:>11}" for y in years))
for g in all_gaps:
    row = []
    for y in years:
        v = counts[y].get(g, 0)
        row.append(f"{v:>11,}" if v > 0 else f"{'-':>11}")
    print(f"{g:>+5}  " + "  ".join(row))

# ---------- forward / same / backward aggregate ----------
forward = {y: sum(n for g, n in counts[y].items() if g > 0) for y in years}
same    = {y: counts[y].get(0, 0) for y in years}
backward = {y: sum(n for g, n in counts[y].items() if g < 0) for y in years}
total   = {y: forward[y] + same[y] + backward[y] for y in years}

print("\n=== Forward / same-year / backward citation summary (by citing_year) ===")
print(f"{'citing_year':>11}  {'forward':>12}  {'same':>10}  {'backward':>12}  "
      f"{'total':>12}  {'fwd %':>7}")
for y in years:
    fwd_pct = forward[y] / total[y] * 100 if total[y] else 0
    print(f"{y:>11}  {forward[y]:>12,}  {same[y]:>10,}  "
          f"{backward[y]:>12,}  {total[y]:>12,}  {fwd_pct:>6.2f}%")

# ---------- forward-citation rate per 1000 citing-year papers ----------
print("\n=== Forward-citation rate per 1000 citing-year papers ===")
print("(citations issued by year-cy papers to year-(cy+gap) papers, per 1000 cy papers)")
print(f"{'gap':>5}  " + "  ".join(f"{y:>11}" for y in years))
for g in [1, 2, 3, 4]:
    row = []
    for y in years:
        rate = counts[y].get(g, 0) / papers_by_year[y] * 1000
        row.append(f"{rate:>11.3f}")
    print(f"{g:>+5}  " + "  ".join(row))

# ---------- trajectory fits ----------
print("\n=== Trajectory fits on log(rate per 1000), 2021-2024 ===")
print("(2020 excluded as COVID-era outlier, consistent with other research scripts)")
fit_years = np.array([2021, 2022, 2023, 2024])


def fit_log(vals, label):
    if not (vals > 0).all():
        print(f"  {label}: zero counts in some year — skipped")
        return None
    log_vals = np.log(vals)
    f = linregress(fit_years, log_vals)
    annual_pct = (np.exp(f.slope) - 1) * 100
    print(f"  {label:48s} slope = {f.slope:+.4f}  "
          f"({annual_pct:+6.1f}%/yr)  R² = {f.rvalue**2:.3f}  p = {f.pvalue:.4f}")
    return f


fit_log(np.array([forward[y] / papers_by_year[y] * 1000 for y in fit_years]),
        "all forward citations (any positive gap)")
fit_log(np.array([counts[y].get(1, 0) / papers_by_year[y] * 1000 for y in fit_years]),
        "forward, gap=+1 only (feeds gap=1 mutual pairs)")
fit_log(np.array([counts[y].get(-1, 0) / papers_by_year[y] * 1000 for y in fit_years]),
        "backward, gap=-1 (normal, for comparison)")
fit_log(np.array([same[y] / papers_by_year[y] * 1000 for y in fit_years]),
        "same-year citations")

# share of forward citations among all citations
print("\n=== Forward citation share over time ===")
print("(if this is roughly stable, forward citing isn't collapsing as a behavior)")
fit_log(np.array([forward[y] / total[y] * 1000 for y in fit_years]),
        "forward share (per 1000 of all citations)")

print("\n=== Comparison to mutual-pair findings (from research/year_gap_analysis.py) ===")
print("  gap=0 mutual pair trajectory: -10.9%/yr (R² = 0.916, p = 0.043)")
print("  gap=1 mutual pair trajectory: -23.9%/yr (R² = 0.850, p = 0.078)")
print()
print("Reading the result:")
print("  - If forward gap=+1 rate trajectory matches gap=1 mutual (~ -24%/yr),")
print("    the gap=1 mutual decline is INHERITED from a broader forward-citation")
print("    shift — not a mutual-pair-specific story. Investigate why papers are")
print("    forward-citing less (preprint dating, OpenAlex semantics, etc.).")
print("  - If forward gap=+1 rate is roughly STABLE while gap=1 mutual collapses,")
print("    the decline is mutual-pair-specific: reciprocity is dropping even")
print("    though forward citing still happens. Different mechanism needed.")
