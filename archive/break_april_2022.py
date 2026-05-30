"""
Test whether mutual citation rates show a statistically significant
DECREASE starting April 2022.

Three tests, each at the same April 2022 candidate break date:

  1. Chow test on log(rate) — does a two-line fit beat a single-line fit?
     Same machinery as research/monthly_trajectory.py.
  2. One-sided slope test — is the post-period slope more negative than
     the pre-period slope? This is the directional version of the Chow
     test, specifically for a *decrease*.
  3. Mean comparison (Mann-Whitney U, one-sided) on the monthly rates
     before vs after April 2022. Does not assume any functional form;
     just asks "are post-period rates systematically lower than pre?"

Window: 2021-01 to 2024-06 (last 6 months censored for ingestion latency,
2020 excluded as COVID outlier — same conventions as the paper).

Important context from research/placebo_chow.py: a Chow test on this
series will fire at most candidate break dates by chance (23/30 in the
ChatGPT analysis). A single positive Chow result for April 2022 alone
is NOT strong evidence of a real break at that date — see the
'specificity check' at the bottom.
"""

import duckdb
import numpy as np
from datetime import date
from scipy.stats import linregress, f as f_dist, mannwhitneyu, norm

con = duckdb.connect("data/citations.duckdb", read_only=True)

BREAK = date(2022, 4, 1)
CENSOR_TAIL_MONTHS = 6


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
    months, pairs, rates = [], [], []
    for pm, n in rows:
        if pm and pm.year in papers and pm.year >= 2021:
            months.append(pm)
            pairs.append(n)
            rates.append(n / (papers[pm.year] / 12) * 1000)
    return months, np.array(pairs), np.array(rates)


months_all, pairs_all, rates_all = fetch_series()

# tail-censor for ingestion latency
if CENSOR_TAIL_MONTHS > 0:
    months = months_all[:-CENSOR_TAIL_MONTHS]
    pairs = pairs_all[:-CENSOR_TAIL_MONTHS]
    rates = rates_all[:-CENSOR_TAIL_MONTHS]
else:
    months, pairs, rates = months_all, pairs_all, rates_all

bp = next((i for i, m in enumerate(months) if m >= BREAK), None)
if bp is None or bp < 6 or len(months) - bp < 6:
    raise SystemExit(
        f"Insufficient data on one side of {BREAK}: "
        f"{bp} pre-months, {len(months) - bp if bp is not None else 0} post-months"
    )

print("=" * 78)
print(f"BREAK CANDIDATE: {BREAK} (April 2022)")
print(f"window: {months[0]} to {months[-1]}  (n={len(months)} months)")
print(f"pre:  n={bp:>2}  ({months[0]} to {months[bp-1]})")
print(f"post: n={len(months) - bp:>2}  ({months[bp]} to {months[-1]})")
print("=" * 78)

# raw level comparison
print(f"\nMonthly mutual pair counts (raw):")
print(f"  pre mean   = {pairs[:bp].mean():>6.1f}  median = {np.median(pairs[:bp]):>6.1f}")
print(f"  post mean  = {pairs[bp:].mean():>6.1f}  median = {np.median(pairs[bp:]):>6.1f}")
print(f"  difference = {pairs[bp:].mean() - pairs[:bp].mean():+6.1f}  "
      f"({(pairs[bp:].mean() / pairs[:bp].mean() - 1) * 100:+.1f}%)")

print(f"\nMonthly mutual rate (pairs per 1000 papers):")
print(f"  pre mean   = {rates[:bp].mean():>6.2f}  median = {np.median(rates[:bp]):>6.2f}")
print(f"  post mean  = {rates[bp:].mean():>6.2f}  median = {np.median(rates[bp:]):>6.2f}")
print(f"  difference = {rates[bp:].mean() - rates[:bp].mean():+6.2f}  "
      f"({(rates[bp:].mean() / rates[:bp].mean() - 1) * 100:+.1f}%)")


# ---------- Test 1: Chow test on log(rate) ----------
print("\n" + "=" * 78)
print("TEST 1: Chow test for ANY break (two-line fit vs one-line fit)")
print("=" * 78)

log_r = np.log(rates)
x = np.arange(len(months), dtype=float)
k = 2  # intercept + slope per segment
n = len(x)

f_all = linregress(x, log_r)
ssr_c = float(np.sum((log_r - (f_all.slope * x + f_all.intercept)) ** 2))

f1 = linregress(x[:bp], log_r[:bp])
ssr1 = float(np.sum((log_r[:bp] - (f1.slope * x[:bp] + f1.intercept)) ** 2))

f2 = linregress(x[bp:], log_r[bp:])
ssr2 = float(np.sum((log_r[bp:] - (f2.slope * x[bp:] + f2.intercept)) ** 2))

F = ((ssr_c - (ssr1 + ssr2)) / k) / ((ssr1 + ssr2) / (n - 2 * k))
p_chow = 1 - f_dist.cdf(F, k, n - 2 * k)

pre_ann = (np.exp(f1.slope * 12) - 1) * 100
post_ann = (np.exp(f2.slope * 12) - 1) * 100
single_ann = (np.exp(f_all.slope * 12) - 1) * 100

print(f"  single-line trend:    {single_ann:+6.1f}%/yr")
print(f"  pre-period slope:     {pre_ann:+6.1f}%/yr  (slope={f1.slope:+.5f}/mo)")
print(f"  post-period slope:    {post_ann:+6.1f}%/yr  (slope={f2.slope:+.5f}/mo)")
print(f"  Chow F = {F:.3f}  p = {p_chow:.4f}  "
      f"{'*** break detected ***' if p_chow < 0.05 else 'no significant break'}")


# ---------- Test 2: One-sided slope test (post < pre) ----------
print("\n" + "=" * 78)
print("TEST 2: One-sided slope comparison (is post slope MORE NEGATIVE than pre?)")
print("=" * 78)
print("  H0: post slope >= pre slope")
print("  H1: post slope <  pre slope  (i.e., decrease accelerates after April 2022)")

# delta-method SE on slope difference
diff = f2.slope - f1.slope
se_diff = float(np.sqrt(f1.stderr**2 + f2.stderr**2))
z = diff / se_diff
p_one_sided = norm.cdf(z)  # left tail since we want diff < 0

print(f"  slope difference  = {diff:+.5f}/mo  (post − pre)")
print(f"  SE                = {se_diff:.5f}")
print(f"  z                 = {z:+.3f}")
print(f"  one-sided p-value = {p_one_sided:.4f}")
if p_one_sided < 0.05:
    print(f"  *** REJECT H0: the decline is steeper after April 2022 (p<0.05) ***")
else:
    print(f"  Cannot reject H0: no statistically significant acceleration of decline")


# ---------- Test 3: Mann-Whitney U on monthly rates ----------
print("\n" + "=" * 78)
print("TEST 3: Mann-Whitney U on monthly rates (distribution-free, one-sided)")
print("=" * 78)
print("  H0: post monthly rates >= pre monthly rates")
print("  H1: post monthly rates <  pre monthly rates")

u_stat, u_p = mannwhitneyu(rates[bp:], rates[:bp], alternative="less")
print(f"  U statistic = {u_stat:.1f}")
print(f"  one-sided p = {u_p:.4f}")
if u_p < 0.05:
    print(f"  *** REJECT H0: post-April-2022 rates are systematically lower (p<0.05) ***")
else:
    print(f"  Cannot reject H0: no systematic difference in monthly rates")


# ---------- Specificity check ----------
print("\n" + "=" * 78)
print("SPECIFICITY CHECK (important!)")
print("=" * 78)
print("""
A Chow test on this 42-month series fires at 23/30 candidate break dates
(see research/placebo_chow.py). If TEST 1 above came back 'significant',
that on its own is NOT strong evidence — many random break dates would
look just as significant. The directional one-sided tests (TESTS 2 and 3)
ARE more meaningful because they ask a specific question about direction.

For real attribution to April 2022, you'd want:
  - April 2022 specifically to rank in the top few candidate dates by F
    (run research/placebo_chow.py and check its rank)
  - The one-sided tests (2 and 3) to be significant
  - A plausible mechanism for why April 2022 specifically matters
""")

# Quick rank check vs the placebo sweep
print("Computing F-statistic rank of April 2022 among all candidate breaks...")
all_F = []
for cand_bp in range(6, len(months) - 6):
    f1c = linregress(x[:cand_bp], log_r[:cand_bp])
    f2c = linregress(x[cand_bp:], log_r[cand_bp:])
    ssr1c = float(np.sum((log_r[:cand_bp] - (f1c.slope * x[:cand_bp] + f1c.intercept)) ** 2))
    ssr2c = float(np.sum((log_r[cand_bp:] - (f2c.slope * x[cand_bp:] + f2c.intercept)) ** 2))
    Fc = ((ssr_c - (ssr1c + ssr2c)) / k) / ((ssr1c + ssr2c) / (n - 2 * k))
    all_F.append((months[cand_bp], Fc))

all_F.sort(key=lambda t: -t[1])
rank = next((i + 1 for i, (m, _) in enumerate(all_F) if m == BREAK), None)
print(f"  April 2022 ranks {rank} of {len(all_F)} candidate break dates by F-statistic.")
print(f"  Top 5 candidates by F:")
for m, F_ in all_F[:5]:
    p_ = 1 - f_dist.cdf(F_, k, n - 2 * k)
    print(f"    {m}  F={F_:.2f}  p={p_:.4f}")

if rank and rank <= 3:
    print(f"\n  April 2022 is among the strongest candidates — the Chow result is")
    print(f"  more credible at this date than a generic noisy series would suggest.")
else:
    print(f"\n  April 2022 is NOT among the strongest candidates. The Chow test sees")
    print(f"  many dates that look at least as 'significant' as this one.")
