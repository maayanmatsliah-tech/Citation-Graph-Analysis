"""
Placebo / specificity check for the monthly Chow-test finding.

The baseline monthly_trajectory.py reports a significant Chow break at the
ChatGPT cutoff (Dec 2022, p = 0.027). Two reasons that result might not be
real:

  (a) Dec 2022 is the single lowest-rate month in the entire dataset (4.50
      per 1000), sitting exactly at the break. A break test will fire if a
      single outlier defines the regime boundary, even if there is no real
      regime shift.

  (b) If the time series has enough variance, a Chow test will find some
      "significant" break date *somewhere* by chance. The interesting
      question is whether Dec 2022 is unusual relative to other candidate
      break dates.

This script does two things:

  1. Sweep every candidate break date that leaves at least 6 months on
     each side. Report the F-statistic and p-value at each. If many dates
     fire, the ChatGPT-date result is not specific.

  2. Re-run the ChatGPT Chow test with Dec 2022 *excluded* (we treat it as
     a single-month outlier). If the result vanishes, the break is being
     driven by that one point.
"""

import duckdb
import numpy as np
from datetime import date
from scipy.stats import linregress, f as f_dist

con = duckdb.connect("data/citations.duckdb", read_only=True)


def fetch_series():
    rows = con.execute("""
        WITH mutual_pairs AS (
            SELECT a.citing_id AS p1, a.cited_id AS p2
            FROM citations a
            JOIN citations b ON a.citing_id = b.cited_id
                            AND a.cited_id = b.citing_id
            WHERE a.citing_id < a.cited_id
        )
        SELECT CAST(date_trunc('month',
                       GREATEST(w1.publication_date, w2.publication_date)) AS DATE) AS pm,
               COUNT(*) AS pairs
        FROM mutual_pairs m
        JOIN works w1 ON m.p1 = w1.id
        JOIN works w2 ON m.p2 = w2.id
        WHERE w1.publication_date IS NOT NULL AND w2.publication_date IS NOT NULL
          AND w1.year BETWEEN 2020 AND 2024
          AND w2.year BETWEEN 2020 AND 2024
        GROUP BY pm ORDER BY pm
    """).fetchall()
    papers = dict(con.execute(
        "SELECT year, COUNT(*) FROM works WHERE year BETWEEN 2020 AND 2024 GROUP BY year"
    ).fetchall())
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
    ssr1 = float(np.sum((y[:bp] - (f1.slope * x[:bp] + f1.intercept)) ** 2))
    ssr2 = float(np.sum((y[bp:] - (f2.slope * x[bp:] + f2.intercept)) ** 2))
    F = ((ssr_c - (ssr1 + ssr2)) / k) / ((ssr1 + ssr2) / (n - 2 * k))
    p = 1 - f_dist.cdf(F, k, n - 2 * k)
    return F, p, f1, f2


def filter_data(months, rates, start_year, censor):
    pairs = [(m, r) for m, r in zip(months, rates) if m.year >= start_year]
    if censor > 0 and len(pairs) > censor:
        pairs = pairs[:-censor]
    fm = [p[0] for p in pairs]
    fr = np.array([p[1] for p in pairs])
    return fm, fr


months_all, rates_all = fetch_series()
m, r = filter_data(months_all, rates_all, 2021, 6)
log_r = np.log(r)
x = np.arange(len(m), dtype=float)

CHATGPT_BREAK = date(2022, 12, 1)
chatgpt_bp = next((i for i, mm in enumerate(m) if mm >= CHATGPT_BREAK), None)

# -------- 1. placebo sweep --------
print("=" * 78)
print("PLACEBO CHOW TEST: sweep every candidate break date")
print("=" * 78)
print(f"  series: n={len(m)} months ({m[0]} to {m[-1]})")
print(f"  null:   one straight line through all of log(rate)")
print(f"  for each candidate breakpoint, refit two lines and test")
print()
print(f"{'break date':<12}  {'pre_n':>5}  {'post_n':>6}  {'F':>6}  {'p':>7}  {'sig'}")

results = []
significant = []
for bp in range(6, len(m) - 6):  # need ≥6 on each side for any power
    res = chow_test(x, log_r, bp)
    if res is None:
        continue
    F, p, _, _ = res
    results.append((m[bp], bp, F, p))
    flag = "***" if p < 0.05 else ""
    if p < 0.05:
        significant.append(m[bp])
    marker = "   <-- ChatGPT date" if m[bp] == CHATGPT_BREAK else ""
    print(f"  {str(m[bp]):<10}  {bp:>5}  {len(m)-bp:>6}  {F:>6.2f}  {p:>7.4f}  {flag}{marker}")

print()
print(f"Significant break dates (p < 0.05): {len(significant)} of {len(results)}")
if significant:
    print(f"  {[str(s) for s in significant]}")

# the ChatGPT break date's rank
sorted_by_F = sorted(results, key=lambda t: -t[2])
chatgpt_rank = next(
    (i for i, t in enumerate(sorted_by_F) if t[0] == CHATGPT_BREAK),
    None,
)
print(f"\nChatGPT date's rank by F-statistic: {chatgpt_rank+1} out of {len(results)} candidates")
if chatgpt_rank is not None and chatgpt_rank < 3:
    print("  -> ChatGPT date is among the strongest candidates (suggestive of real signal)")
else:
    print("  -> ChatGPT date is NOT uniquely strong (Chow test result not specific to it)")

# -------- 2. exclude Dec 2022 and re-run ChatGPT Chow --------
print()
print("=" * 78)
print("OUTLIER-DROP CHECK: re-run Chow at ChatGPT date with Dec 2022 excluded")
print("=" * 78)

drop_idx = next((i for i, mm in enumerate(m) if mm == date(2022, 12, 1)), None)
if drop_idx is None:
    print("Dec 2022 not in the fitted window; nothing to drop.")
else:
    m2 = m[:drop_idx] + m[drop_idx+1:]
    log_r2 = np.concatenate([log_r[:drop_idx], log_r[drop_idx+1:]])
    x2 = np.arange(len(m2), dtype=float)
    bp2 = next((i for i, mm in enumerate(m2) if mm >= CHATGPT_BREAK), None)

    print(f"  Dec 2022 value: rate = {float(np.exp(log_r[drop_idx])):.2f}/1000 "
          f"(lowest in dataset; surrounding months ~8-11)")
    print(f"  Re-fitting on n={len(m2)} months, break at first post-Dec-2022 month "
          f"({m2[bp2]})")

    res = chow_test(x2, log_r2, bp2)
    if res is None:
        print("  Chow test returned None (insufficient data on one side)")
    else:
        F, p, f1, f2 = res
        pre_ann = (np.exp(f1.slope * 12) - 1) * 100
        post_ann = (np.exp(f2.slope * 12) - 1) * 100
        sig = "*** SIGNIFICANT ***" if p < 0.05 else "no break"
        print(f"  F = {F:.3f}, p = {p:.4f}  {sig}")
        print(f"  Pre slope:  {f1.slope:+.5f}/mo ({pre_ann:+.1f}%/yr)")
        print(f"  Post slope: {f2.slope:+.5f}/mo ({post_ann:+.1f}%/yr)")
        print()
        print("  Baseline result (with Dec 2022 included): p = 0.0271, post = +16.6%/yr")
        if p > 0.05:
            print("  Removing one month destroyed the result. The 'break' was that single point.")
        else:
            print("  Result survives removing Dec 2022. The break is not driven by the outlier.")
