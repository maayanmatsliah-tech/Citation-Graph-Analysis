"""
Robustness checks for the monthly trajectory finding in
research/monthly_trajectory.py (significant Chow break at Dec 2022).

Three checks, each printed as a one-liner alongside the baseline:

1. Exclude 2021 — does the break survive without COVID-era pre-period
   data? If 2021 was elevated by COVID research clustering, the apparent
   "steep pre-decline" might just be COVID dissipation.
2. Censoring sensitivity — does the result depend on how many tail
   months we drop for OpenAlex ingestion latency? Re-run with 3, 6, 9,
   12 months.
3. Seasonality — monthly counts have academic-calendar structure
   (conference deadlines, journal issues). Deseasonalize by subtracting
   the month-of-year mean (computed over 2021-2024) and refit.

If the break is real, it should survive all three checks.
"""

import duckdb
import numpy as np
from datetime import date
from scipy.stats import linregress, f as f_dist

con = duckdb.connect("data/citations.duckdb")
BREAK = date(2022, 12, 1)


def fetch_series():
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
            ) AS DATE) AS pm,
            COUNT(*) AS pairs
        FROM mutual_pairs m
        JOIN works w1 ON m.p1 = w1.id
        JOIN works w2 ON m.p2 = w2.id
        WHERE w1.publication_date IS NOT NULL
          AND w2.publication_date IS NOT NULL
          AND w1.year BETWEEN 2020 AND 2024
          AND w2.year BETWEEN 2020 AND 2024
        GROUP BY pm
        ORDER BY pm
    """).fetchall()
    papers = dict(con.execute("""
        SELECT year, COUNT(*) FROM works
        WHERE year BETWEEN 2020 AND 2024
        GROUP BY year
    """).fetchall())
    months, rates = [], []
    for pm, pairs in rows:
        if pm and pm.year in papers:
            months.append(pm)
            rates.append(pairs / (papers[pm.year] / 12) * 1000)
    return months, np.array(rates)


def chow_test(x, y, bp):
    n, k = len(x), 2
    if bp < k + 1 or n - bp < k + 1:
        return None
    f_all = linregress(x, y)
    f1 = linregress(x[:bp], y[:bp])
    f2 = linregress(x[bp:], y[bp:])
    ssr_c = float(np.sum((y - (f_all.slope * x + f_all.intercept)) ** 2))
    ssr1 = float(np.sum(
        (y[:bp] - (f1.slope * x[:bp] + f1.intercept)) ** 2
    ))
    ssr2 = float(np.sum(
        (y[bp:] - (f2.slope * x[bp:] + f2.intercept)) ** 2
    ))
    F = ((ssr_c - (ssr1 + ssr2)) / k) / ((ssr1 + ssr2) / (n - 2 * k))
    p = 1 - f_dist.cdf(F, k, n - 2 * k)
    return F, p, f1, f2


def run(months, rates, label):
    log_r = np.log(rates)
    idx = np.arange(len(months), dtype=float)
    bp = next((i for i, m in enumerate(months) if m >= BREAK), None)
    res = chow_test(idx, log_r, bp) if bp is not None else None
    if res is None:
        print(f"  {label:38s} insufficient data on one side of break")
        return
    F, p, f1, f2 = res
    pre = (np.exp(f1.slope * 12) - 1) * 100
    post = (np.exp(f2.slope * 12) - 1) * 100
    sig = "*** break ***" if p < 0.05 else "no break"
    print(f"  {label:38s} pre {pre:+6.1f}%/yr  post {post:+6.1f}%/yr  "
          f"F={F:5.2f}  p={p:.4f}  {sig}")


def filter_data(months, rates, start_year, censor):
    pairs = [(m, r) for m, r in zip(months, rates) if m.year >= start_year]
    if censor > 0 and len(pairs) > censor:
        pairs = pairs[:-censor]
    fm = [p[0] for p in pairs]
    fr = np.array([p[1] for p in pairs])
    return fm, fr


months_all, rates_all = fetch_series()
print(f"Loaded {len(months_all)} monthly observations "
      f"({months_all[0]} to {months_all[-1]})\n")

print("=== Baseline (matches research/monthly_trajectory.py) ===")
m, r = filter_data(months_all, rates_all, 2021, 6)
run(m, r, f"baseline (2021-, 6mo cens, n={len(m)})")

print("\n=== Check 1: exclude 2021 (no COVID-era pre data) ===")
m, r = filter_data(months_all, rates_all, 2022, 6)
run(m, r, f"start 2022 (6mo cens, n={len(m)})")

print("\n=== Check 2: censoring sensitivity ===")
for c in [3, 6, 9, 12]:
    m, r = filter_data(months_all, rates_all, 2021, c)
    run(m, r, f"censor {c:2d}mo (n={len(m)})")

print("\n=== Check 3: deseasonalize (subtract month-of-year mean) ===")
m, r = filter_data(months_all, rates_all, 2021, 6)
log_r = np.log(r)
moy = np.array([d.month for d in m])
overall_mean = log_r.mean()
seasonal = {}
for month in range(1, 13):
    mask = moy == month
    if mask.any():
        seasonal[month] = log_r[mask].mean() - overall_mean
adjusted = log_r - np.array([seasonal.get(mm, 0) for mm in moy])
run(m, np.exp(adjusted), f"deseasonalized (n={len(m)})")

print(f"\n  Seasonal effect range: "
      f"{max(seasonal.values()) - min(seasonal.values()):.3f} log-units "
      f"({(np.exp(max(seasonal.values()) - min(seasonal.values())) - 1) * 100:.0f}% peak-to-trough)")
heaviest = sorted(seasonal.items(), key=lambda kv: -kv[1])[:3]
lightest = sorted(seasonal.items(), key=lambda kv: kv[1])[:3]
print(f"  Heaviest months: " + ", ".join(f"{m} ({s:+.2f})" for m, s in heaviest))
print(f"  Lightest months: " + ", ".join(f"{m} ({s:+.2f})" for m, s in lightest))
