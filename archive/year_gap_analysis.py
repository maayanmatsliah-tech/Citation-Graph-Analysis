"""
Year-gap distribution within mutual pairs.

For each deduped mutual pair, anchor it to the later paper's year
(max(year_A, year_B)) and record gap = |year_A - year_B|. Then compare the
per-year rates of same-year (gap=0) pairs against one-year-apart (gap=1)
pairs, etc.

Why: the original hypothesis specifically predicted ChatGPT would compress
*contemporaneous* peer discovery — same-year mutual pairs should rise. The
aggregate mutual-rate test we ran earlier pooled all gaps together, so a
real shift in same-year pairs could be hidden by lagged-pair dynamics. This
script breaks the trajectory apart by gap to look directly on the axis the
hypothesis cares about, and to see whether same-year decay differs from
lagged decay (a candidate mechanism for the secular decline).

Coverage caveat: both papers in a pair are restricted to 2020-2024 (the
dense region). For pair_year Y, only gaps in [0, Y - 2020] are structurally
possible — older pair_years have fewer gap buckets available, so cells
beyond that range are mechanically zero rather than meaningfully empty.
gap=0 is unaffected (same-year pairs only need that one year to be dense).
gap=1 is clean for pair_years 2021-2024. Higher gaps narrow further.
"""

import duckdb
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

con = duckdb.connect("data/citations.duckdb")

rows = con.execute("""
    WITH mutual_pairs AS (
        SELECT a.citing_id AS p1, a.cited_id AS p2
        FROM citations a
        JOIN citations b ON a.citing_id = b.cited_id AND a.cited_id = b.citing_id
        WHERE a.citing_id < a.cited_id
    )
    SELECT
        GREATEST(w1.year, w2.year) AS pair_year,
        ABS(w1.year - w2.year) AS gap,
        COUNT(*) AS pairs
    FROM mutual_pairs m
    JOIN works w1 ON m.p1 = w1.id
    JOIN works w2 ON m.p2 = w2.id
    WHERE w1.year IS NOT NULL AND w2.year IS NOT NULL
      AND w1.year BETWEEN 2020 AND 2024
      AND w2.year BETWEEN 2020 AND 2024
    GROUP BY pair_year, gap
    ORDER BY pair_year, gap
""").fetchall()

papers_by_year = dict(con.execute("""
    SELECT year, COUNT(*) FROM works
    WHERE year BETWEEN 2020 AND 2024
    GROUP BY year
""").fetchall())

years = sorted(papers_by_year)
gaps = sorted({r[1] for r in rows})
min_year = min(years)

counts = {g: {y: 0 for y in years} for g in gaps}
for y, g, n in rows:
    counts[g][y] = n

totals = {y: sum(counts[g][y] for g in gaps) for y in years}
rates = {g: {y: counts[g][y] / papers_by_year[y] * 1000 for y in years} for g in gaps}


def cell(value, fmt, g, y):
    return f"{'-':>9}" if g > y - min_year else fmt.format(value)


# ---------- raw counts ----------
print("=== Mutual pair counts by (pair_year, gap) ===")
print("(both papers restricted to 2020-2024; '-' = structurally impossible)")
print(f"{'gap':>4}  " + "  ".join(f"{y:>9}" for y in years))
for g in gaps:
    row = [cell(counts[g][y], "{:>9,}", g, y) for y in years]
    print(f"{g:>4}  " + "  ".join(row))
print(f"{'all':>4}  " + "  ".join(f"{totals[y]:>9,}" for y in years))

# ---------- rates per 1000 papers ----------
print("\n=== Mutual pair RATE per 1000 papers, by (pair_year, gap) ===")
print(f"{'gap':>4}  " + "  ".join(f"{y:>9}" for y in years))
for g in gaps:
    row = [cell(rates[g][y], "{:>9.3f}", g, y) for y in years]
    print(f"{g:>4}  " + "  ".join(row))

# ---------- composition (within-year shares) ----------
print("\n=== Composition: share of each year's mutual pairs at each gap (%) ===")
print("(NOTE: share shifts mechanically as more gap buckets become available)")
print(f"{'gap':>4}  " + "  ".join(f"{y:>9}" for y in years))
for g in gaps:
    row = []
    for y in years:
        if g > y - min_year:
            row.append(f"{'-':>9}")
        else:
            pct = counts[g][y] / totals[y] * 100
            row.append(f"{pct:>8.1f}%")
    print(f"{g:>4}  " + "  ".join(row))

# ---------- trajectory tests (the key analysis) ----------
print("\n=== Trajectory fits on log(rate per 1000), 2021-2024 ===")
print("(2020 excluded as COVID-era outlier, consistent with research/trajectory.py)")
fit_years = np.array([2021, 2022, 2023, 2024])


def fit_log(vals, label):
    if not (vals > 0).all():
        print(f"  {label}: zero counts in some year — skipped")
        return None
    log_vals = np.log(vals)
    f = linregress(fit_years, log_vals)
    annual_pct = (np.exp(f.slope) - 1) * 100
    print(f"  {label:32s} slope = {f.slope:+.4f}  "
          f"({annual_pct:+5.1f}%/yr)  R² = {f.rvalue**2:.3f}  p = {f.pvalue:.4f}")
    return f


agg_vals = np.array([totals[y] / papers_by_year[y] * 1000 for y in fit_years])
fit_all = fit_log(agg_vals, "aggregate (all gaps)")
fit_0 = fit_log(np.array([rates[0][y] for y in fit_years]), "gap = 0 (same year)")
fit_1 = fit_log(np.array([rates[1][y] for y in fit_years]), "gap = 1 (one year apart)")

# ---------- pre/post slopes for gap=0 (the most specific ChatGPT test) ----------
print("\n=== Pre vs post-ChatGPT slope on gap=0 (same-year) rate ===")
print("(this is the precise axis the original hypothesis cares about:")
print(" contemporaneous peer discovery should improve post-ChatGPT)")
if all(rates[0][y] > 0 for y in fit_years):
    pre = np.log(rates[0][2022]) - np.log(rates[0][2021])
    post = np.log(rates[0][2024]) - np.log(rates[0][2023])
    print(f"  Pre-ChatGPT  (2021 -> 2022): {pre:+.4f}")
    print(f"  Post-ChatGPT (2023 -> 2024): {post:+.4f}")
    direction = "DECELERATED" if post > pre else "ACCELERATED"
    print(f"  Difference: {post-pre:+.4f}  (same-year decline {direction} after ChatGPT)")

# ---------- residuals for gap=0 (where do post-ChatGPT years sit?) ----------
if fit_0 is not None:
    print("\n=== gap=0 residuals vs fitted trend ===")
    print("(post-ChatGPT residuals well above trend would be evidence FOR the hypothesis)")
    vals = np.array([rates[0][y] for y in fit_years])
    pred = np.exp(fit_0.slope * fit_years + fit_0.intercept)
    resids = np.log(vals) - (fit_0.slope * fit_years + fit_0.intercept)
    for y, obs, p, r in zip(fit_years, vals, pred, resids):
        flag = "  <-- post-ChatGPT" if y >= 2023 else ""
        print(f"  {y}: observed {obs:.3f}  trend {p:.3f}  residual {r:+.4f}{flag}")

# ---------- chart ----------
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Mutual-pair year-gap analysis", fontsize=13)

# left: per-gap rate trajectories (only show gaps with full coverage 2021-2024)
ax = axes[0]
colors = plt.cm.viridis(np.linspace(0.2, 0.85, len(gaps)))
for i, g in enumerate(gaps):
    ys = [y for y in years if g <= y - min_year]
    vals = [rates[g][y] for y in ys]
    ax.plot(ys, vals, marker="o", color=colors[i], label=f"gap = {g}")
ax.axvline(x=2022.92, color="red", linestyle=":", label="ChatGPT launch")
ax.set_title("Mutual-pair rate by year-gap")
ax.set_xlabel("Pair year (later paper)")
ax.set_ylabel("Pairs per 1000 papers")
ax.set_xticks(years)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# right: same-year vs one-year-apart (the cleanest comparison, both 2021-2024)
ax = axes[1]
gap0 = [rates[0][y] for y in fit_years]
gap1 = [rates[1][y] for y in fit_years]
ax.plot(fit_years, gap0, marker="o", color="steelblue", linewidth=2,
        label="gap = 0 (same year)")
ax.plot(fit_years, gap1, marker="s", color="coral", linewidth=2,
        label="gap = 1 (one year apart)")
ax.axvline(x=2022.92, color="red", linestyle=":", label="ChatGPT launch")
ax.set_title("Same-year vs one-year-apart trajectories (2021-2024)")
ax.set_xlabel("Pair year (later paper)")
ax.set_ylabel("Pairs per 1000 papers")
ax.set_xticks(fit_years)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("outputs/year_gap.png", dpi=150)
print("\nSaved chart to outputs/year_gap.png")
