"""
Monthly-resolution trajectory test for mutual citation rate.

Why: research/trajectory.py at yearly resolution has 4 data points and
near-zero power against a pre-existing trend. A structural-break test at
ChatGPT's launch (Nov 30, 2022) needs much more data. This script uses
monthly publication dates (backfilled by data/backfill_dates.py) to
repeat the trajectory test at ~48 monthly points across 2021-2024 and
runs a Chow test for a break at the ChatGPT cutoff.

Denominator: monthly papers ≈ yearly papers / 12 (uniform-within-year
approximation). Cheap; avoids needing dates for all ~1M papers. If you
want real monthly denominators later, set SAMPLE_PER_YEAR > 0 in
data/backfill_dates.py, rerun it, and replace the denominator query
below with a real per-month count.

Pair anchoring: each deduplicated mutual pair is anchored to the later
paper's month (max of the two publication_dates), matching the year-level
convention in research/trajectory.py and research/year_gap_analysis.py.

Right-censoring: the last CENSOR_TAIL_MONTHS months are dropped because
OpenAlex's reference data has ingestion latency — very recent papers'
citation lists aren't fully indexed yet, which would artificially deflate
mutual-pair counts near the present.

2020: dropped entirely as a COVID-era outlier, same as trajectory.py.
"""

import duckdb
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date
from scipy.stats import linregress, f as f_dist

con = duckdb.connect("data/citations.duckdb")

CENSOR_TAIL_MONTHS = 6
BREAK = date(2022, 12, 1)  # first month entirely post-ChatGPT (launched Nov 30, 2022)

# ---------- monthly mutual-pair counts ----------
rows = con.execute("""
    WITH mutual_pairs AS (
        SELECT a.citing_id AS p1, a.cited_id AS p2
        FROM citations a
        JOIN citations b ON a.citing_id = b.cited_id
                        AND a.cited_id = b.citing_id
        WHERE a.citing_id < a.cited_id
    )
    SELECT
        CAST(date_trunc(
            'month',
            GREATEST(w1.publication_date, w2.publication_date)
        ) AS DATE) AS pair_month,
        COUNT(*) AS pairs
    FROM mutual_pairs m
    JOIN works w1 ON m.p1 = w1.id
    JOIN works w2 ON m.p2 = w2.id
    WHERE w1.publication_date IS NOT NULL
      AND w2.publication_date IS NOT NULL
      AND w1.year BETWEEN 2020 AND 2024
      AND w2.year BETWEEN 2020 AND 2024
    GROUP BY pair_month
    ORDER BY pair_month
""").fetchall()

# count pairs we had to drop because of missing dates (backfill gaps)
missing = con.execute("""
    WITH mutual_pairs AS (
        SELECT a.citing_id AS p1, a.cited_id AS p2
        FROM citations a
        JOIN citations b ON a.citing_id = b.cited_id
                        AND a.cited_id = b.citing_id
        WHERE a.citing_id < a.cited_id
    )
    SELECT COUNT(*)
    FROM mutual_pairs m
    JOIN works w1 ON m.p1 = w1.id
    JOIN works w2 ON m.p2 = w2.id
    WHERE w1.year BETWEEN 2020 AND 2024
      AND w2.year BETWEEN 2020 AND 2024
      AND (w1.publication_date IS NULL OR w2.publication_date IS NULL)
""").fetchone()[0]

total_pairs = sum(r[1] for r in rows)
print(f"Mutual pairs with month-level dates: {total_pairs:,}")
print(f"Mutual pairs dropped (date missing on at least one partner): {missing:,}")
print(f"Distinct months covered: {len(rows)}")

# ---------- denominator: papers per year / 12 approximation ----------
papers_by_year = dict(con.execute("""
    SELECT year, COUNT(*) FROM works
    WHERE year BETWEEN 2020 AND 2024
    GROUP BY year
""").fetchall())

# ---------- build (month, rate) series ----------
months_all, rates_all = [], []
for pair_month, pairs in rows:
    if pair_month is None or pair_month.year not in papers_by_year:
        continue
    monthly_papers = papers_by_year[pair_month.year] / 12
    months_all.append(pair_month)
    rates_all.append(pairs / monthly_papers * 1000)

# 2020 out (COVID outlier), tail censored
fit_data = [
    (m, r) for m, r in zip(months_all, rates_all)
    if m.year >= 2021
]
if CENSOR_TAIL_MONTHS > 0:
    fit_data = fit_data[:-CENSOR_TAIL_MONTHS] if len(fit_data) > CENSOR_TAIL_MONTHS else fit_data

fit_months = [d[0] for d in fit_data]
fit_rates = np.array([d[1] for d in fit_data])
fit_idx = np.array([
    (m.year - 2021) * 12 + (m.month - 1) for m in fit_months
], dtype=float)

print(f"\nFitting on {len(fit_rates)} monthly observations "
      f"({fit_months[0]} to {fit_months[-1]})")
print(f"  excluded: 2020 (COVID outlier), "
      f"last {CENSOR_TAIL_MONTHS} months (ingestion latency)")

if len(fit_rates) < 12:
    print("\nNot enough monthly data to fit a trajectory. "
          "Check that data/backfill_dates.py has run.")
    raise SystemExit(0)

log_rates = np.log(fit_rates)

# ---------- aggregate trajectory ----------
fit = linregress(fit_idx, log_rates)
monthly_pct = (np.exp(fit.slope) - 1) * 100
annual_pct = (np.exp(fit.slope * 12) - 1) * 100
print("\n=== Aggregate linear trend on log(rate), monthly ===")
print(f"  Slope (per month):  {fit.slope:+.5f}  ({monthly_pct:+.2f}%/month)")
print(f"  Annualized:         {annual_pct:+.1f}%/year")
print(f"  R²:                 {fit.rvalue**2:.3f}")
print(f"  Slope p-value:      {fit.pvalue:.4g}")

# ---------- Chow test for structural break at ChatGPT ----------
def chow_test(x, y, break_pos):
    """Test whether the regression splits at break_pos (an index into x).
    Returns F-statistic, p-value, and the pre/post linregress results."""
    n = len(x)
    k = 2  # intercept + slope

    f_all = linregress(x, y)
    ssr_c = float(np.sum((y - (f_all.slope * x + f_all.intercept)) ** 2))

    f1 = linregress(x[:break_pos], y[:break_pos])
    ssr1 = float(np.sum(
        (y[:break_pos] - (f1.slope * x[:break_pos] + f1.intercept)) ** 2
    ))

    f2 = linregress(x[break_pos:], y[break_pos:])
    ssr2 = float(np.sum(
        (y[break_pos:] - (f2.slope * x[break_pos:] + f2.intercept)) ** 2
    ))

    F = ((ssr_c - (ssr1 + ssr2)) / k) / ((ssr1 + ssr2) / (n - 2 * k))
    p = 1 - f_dist.cdf(F, k, n - 2 * k)
    return F, p, f1, f2


break_month_idx = (BREAK.year - 2021) * 12 + (BREAK.month - 1)
break_pos = next(
    (i for i, idx in enumerate(fit_idx) if idx >= break_month_idx), None
)

if break_pos is None or break_pos < 6 or len(fit_idx) - break_pos < 6:
    print(f"\nChow test skipped: not enough data on one side of {BREAK}.")
    f1 = f2 = None
else:
    F, p, f1, f2 = chow_test(fit_idx, log_rates, break_pos)
    print(f"\n=== Chow test for structural break at {BREAK} ===")
    print(f"  Pre-period:  {break_pos} months")
    print(f"  Post-period: {len(fit_idx) - break_pos} months")
    print(f"  F-statistic: {F:.3f}")
    print(f"  p-value:     {p:.4g}")
    if p < 0.05:
        print("  *** SIGNIFICANT structural break — reject single-trajectory null ***")
    else:
        print("  No significant structural break detected.")

    pre_annual = (np.exp(f1.slope * 12) - 1) * 100
    post_annual = (np.exp(f2.slope * 12) - 1) * 100
    print(f"\n  Pre  slope:  {f1.slope:+.5f}/month ({pre_annual:+.1f}%/yr)")
    print(f"  Post slope:  {f2.slope:+.5f}/month ({post_annual:+.1f}%/yr)")
    pre_at_break = f1.slope * break_month_idx + f1.intercept
    post_at_break = f2.slope * break_month_idx + f2.intercept
    print(f"  Level shift at break (log): {post_at_break - pre_at_break:+.4f}  "
          f"({(np.exp(post_at_break - pre_at_break) - 1) * 100:+.1f}%)")

# ---------- chart ----------
fig, ax = plt.subplots(figsize=(11, 6))
ax.scatter(fit_months, fit_rates, c="steelblue", s=20, alpha=0.7,
           label=f"Monthly rate (n={len(fit_rates)})")

if f1 is not None and f2 is not None:
    pre_x = fit_idx[:break_pos]
    post_x = fit_idx[break_pos:]
    ax.plot([fit_months[i] for i in range(break_pos)],
            np.exp(f1.slope * pre_x + f1.intercept),
            color="orange", linewidth=2,
            label=f"Pre-ChatGPT trend ({pre_annual:+.1f}%/yr)")
    ax.plot([fit_months[i] for i in range(break_pos, len(fit_months))],
            np.exp(f2.slope * post_x + f2.intercept),
            color="green", linewidth=2,
            label=f"Post-ChatGPT trend ({post_annual:+.1f}%/yr)")
else:
    pred = np.exp(fit.slope * fit_idx + fit.intercept)
    ax.plot(fit_months, pred, color="orange", linewidth=2,
            label=f"Single trend ({annual_pct:+.1f}%/yr)")

ax.axvline(x=BREAK, color="red", linestyle=":", label="ChatGPT launch (Nov 2022)")
ax.set_yscale("log")
ax.set_title("Monthly mutual citation rate trajectory")
ax.set_xlabel("Month")
ax.set_ylabel("Mutual pairs per 1000 papers (log scale)")
ax.legend()
ax.grid(True, alpha=0.3, which="both")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

plt.tight_layout()
plt.savefig("outputs/monthly_trajectory.png", dpi=150)
print("\nSaved chart to outputs/monthly_trajectory.png")
