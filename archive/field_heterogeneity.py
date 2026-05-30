"""
Field-level analysis of the secular decline.

The pipeline-drift check produced a striking observation: the per-field
decline in mutual citation rate ranges from -5%/yr (Chemistry, Nursing) to
-43%/yr (Agricultural & Biological Sciences). A factor-of-16 spread across
fields. We don't have an explanation yet. This script asks:

  1. Is the field decline correlated with field-level changes in paper
     volume? (If a field is growing fast, per-paper rates can fall just
     because the denominator is exploding.)

  2. Is it correlated with field-level changes in within-field citation
     density (refs per paper that target the same field)?

  3. Is it correlated with baseline mutual rate? (Are high-rate fields
     reverting toward a common floor?)

  4. Within-CS subfield split: do NLP/ML-adjacent areas of CS look
     different from theory/systems? This addresses the "field exposure
     is crude" critique and is the cleanest within-CS analog to the
     cross-field DiD.

  5. Within-field decomposition vs between-field shift: how much of the
     aggregate -13%/yr decline is each field declining individually
     (within-field) vs the composition of papers shifting toward
     lower-rate fields (between-field)?
"""

import duckdb
import numpy as np
from scipy.stats import linregress

con = duckdb.connect("data/citations.duckdb", read_only=True)


# -------- pull per-field, per-year stats --------
rows = con.execute("""
    WITH mutual_pairs AS (
        SELECT a.citing_id AS p1, a.cited_id AS p2
        FROM citations a
        JOIN citations b ON a.citing_id = b.cited_id
                        AND a.cited_id = b.citing_id
        WHERE a.citing_id < a.cited_id
    ),
    pair_papers AS (
        SELECT DISTINCT p FROM (
            SELECT p1 AS p FROM mutual_pairs UNION SELECT p2 FROM mutual_pairs
        )
    ),
    refs_in_field AS (
        -- count of refs from this paper to other papers in same field same year
        SELECT w1.id AS pid, w1.field AS field, w1.year AS year,
               COUNT(*) AS within_refs
        FROM citations c
        JOIN works w1 ON c.citing_id = w1.id
        JOIN works w2 ON c.cited_id  = w2.id
        WHERE w1.year = w2.year
          AND w1.field = w2.field
          AND w1.year BETWEEN 2020 AND 2024
          AND c.citing_id <> c.cited_id
        GROUP BY w1.id, w1.field, w1.year
    )
    SELECT
        w.field, w.year,
        COUNT(*)                              AS papers,
        SUM(CASE WHEN pp.p IS NOT NULL THEN 1 ELSE 0 END) AS in_mutual,
        AVG(COALESCE(r.within_refs, 0))       AS avg_within_field_refs
    FROM works w
    LEFT JOIN pair_papers pp ON pp.p = w.id
    LEFT JOIN refs_in_field r ON r.pid = w.id
    WHERE w.year BETWEEN 2020 AND 2024
    GROUP BY w.field, w.year
""").fetchall()

by_field = {}
for f, y, p, m, ar in rows:
    by_field.setdefault(f, {})[y] = (p, m, ar)


def fit_log_slope(years, vals):
    """Annualized %/yr from log-linear fit. Returns None if can't fit."""
    years = np.array(years, dtype=float)
    vals = np.array(vals, dtype=float)
    if (vals <= 0).any() or len(vals) < 3:
        return None
    f = linregress(years, np.log(vals))
    return (np.exp(f.slope) - 1) * 100


# -------- 1. per-field stats (2021-2024 only) --------
print("=" * 100)
print("FIELD-LEVEL DETAIL (2021-2024, 2020 excluded as COVID outlier)")
print("=" * 100)
print(f"{'field':<46}  {'rate_21':>8} {'rate_24':>8}  {'rate_d':>7}"
      f"  {'papers_d':>9}  {'refs_d':>8}  {'concur_d':>9}")
print(f"{'':46}  {'pairs/k':>8} {'pairs/k':>8}  {'%/yr':>7}"
      f"  {'%/yr':>9}  {'%/yr':>8}  {'%/yr':>9}")
print("-" * 100)

results = []
for field, ydata in by_field.items():
    years_present = [y for y in [2021, 2022, 2023, 2024] if y in ydata]
    if len(years_present) < 3:
        continue
    if ydata[years_present[0]][0] < 1000:  # skip tiny fields
        continue

    rates = []
    papers = []
    refs = []
    for y in years_present:
        p, m, ar = ydata[y]
        if p == 0:
            rates.append(0)
        else:
            rates.append(m / p * 1000)
        papers.append(p)
        refs.append(ar)

    rate_slope = fit_log_slope(years_present, rates)
    papers_slope = fit_log_slope(years_present, papers)
    refs_slope = fit_log_slope(years_present, refs) if all(r > 0 for r in refs) else None

    # rate at 2021 and 2024
    r21 = rates[0]
    r24 = rates[-1]

    if rate_slope is None:
        continue

    results.append({
        "field": field,
        "rate_slope": rate_slope,
        "papers_slope": papers_slope,
        "refs_slope": refs_slope,
        "r21": r21,
        "r24": r24,
        "papers_21": papers[0],
    })

# sort by rate decline (most negative first)
results.sort(key=lambda r: r["rate_slope"])

for r in results:
    refs_s = f"{r['refs_slope']:+8.1f}%" if r["refs_slope"] is not None else "     n/a"
    papers_s = f"{r['papers_slope']:+8.1f}%" if r["papers_slope"] is not None else "     n/a"
    print(f"  {r['field']:<44}  {r['r21']:>8.2f} {r['r24']:>8.2f}"
          f"  {r['rate_slope']:>+6.1f}%  {papers_s}  {refs_s}  "
          f"{(r['refs_slope'] or 0):+8.1f}%")

# -------- 2. correlation: rate decline vs paper volume change and refs change --------
print()
print("=" * 100)
print("WHAT EXPLAINS THE FIELD-LEVEL DECLINE VARIATION?")
print("=" * 100)

rate_slopes = np.array([r["rate_slope"] for r in results])
papers_slopes = np.array([r["papers_slope"] for r in results
                          if r["papers_slope"] is not None])
refs_slopes = np.array([r["refs_slope"] for r in results
                        if r["refs_slope"] is not None])
r21_vals = np.array([r["r21"] for r in results])

# correlation: rate decline vs paper volume change
valid = [(r["rate_slope"], r["papers_slope"]) for r in results
         if r["papers_slope"] is not None]
if len(valid) > 3:
    rs, ps = zip(*valid)
    corr = np.corrcoef(rs, ps)[0, 1]
    print(f"\nCorrelation (rate decline % vs paper-volume change %):  r = {corr:+.3f}")
    print("  If r is strongly negative, fields with growing volume decline faster")
    print("  (volume dilution mechanism). If r is near 0, volume isn't the driver.")

# correlation: rate decline vs within-field refs change
valid = [(r["rate_slope"], r["refs_slope"]) for r in results
         if r["refs_slope"] is not None]
if len(valid) > 3:
    rs, refs = zip(*valid)
    corr = np.corrcoef(rs, refs)[0, 1]
    print(f"\nCorrelation (rate decline % vs within-field-refs change %):  r = {corr:+.3f}")
    print("  If r is strongly POSITIVE, fields whose within-field citation density")
    print("  is falling are also losing mutual pairs — a coherent behavior story.")

# correlation: rate decline vs baseline rate
corr = np.corrcoef(rate_slopes, r21_vals)[0, 1]
print(f"\nCorrelation (rate decline % vs 2021 baseline rate):  r = {corr:+.3f}")
print("  If r is strongly negative, high-baseline fields decline faster")
print("  (reversion to mean). If r is near 0, baseline doesn't predict decline.")


# -------- 3. within-vs-between field decomposition --------
print()
print("=" * 100)
print("WITHIN- vs BETWEEN-FIELD DECOMPOSITION OF AGGREGATE DECLINE")
print("=" * 100)
print("""
The aggregate -13.2%/yr decline could come from:
  (W) each field's own rate falling (within-field decline)
  (B) the mix of papers shifting toward fields with lower mutual rates (composition shift)
This decomposition tells us how much each channel contributes.
""")


def aggregate_for_year(y):
    """Return (total_papers, total_in_mutual, aggregate_rate)."""
    total_p = sum(d[y][0] for d in by_field.values() if y in d)
    total_m = sum(d[y][1] for d in by_field.values() if y in d)
    rate = total_m / total_p * 1000 if total_p else 0
    return total_p, total_m, rate


for y in range(2020, 2025):
    p, m, r = aggregate_for_year(y)
    print(f"  {y}: {m:>6,}/{p:>8,} papers = {r:.2f} per 1000")

# Counterfactual A: 2024 weights with 2021 field rates
# (= "if every field's rate were stuck at 2021, but composition was 2024")
print("\nCounterfactual A: fix every field's rate at its 2021 value;")
print("                  use 2024's field-composition. What rate would we see?")
total_p_24 = 0
weighted_m = 0
for field, ydata in by_field.items():
    if 2021 not in ydata or 2024 not in ydata:
        continue
    p21, m21, _ = ydata[2021]
    if p21 == 0:
        continue
    rate_21 = m21 / p21  # per paper
    p24, _, _ = ydata[2024]
    weighted_m += rate_21 * p24
    total_p_24 += p24
cf_a_rate = weighted_m / total_p_24 * 1000 if total_p_24 else 0
print(f"  -> {cf_a_rate:.2f} per 1000")
print(f"     (vs 2021 actual {aggregate_for_year(2021)[2]:.2f} and 2024 actual {aggregate_for_year(2024)[2]:.2f})")

# Counterfactual B: 2021 weights with 2024 field rates
print("\nCounterfactual B: fix field-composition at 2021;")
print("                  use 2024's per-field rates. What rate would we see?")
total_p_21 = 0
weighted_m = 0
for field, ydata in by_field.items():
    if 2021 not in ydata or 2024 not in ydata:
        continue
    p24, m24, _ = ydata[2024]
    if p24 == 0:
        continue
    rate_24 = m24 / p24
    p21, _, _ = ydata[2021]
    weighted_m += rate_24 * p21
    total_p_21 += p21
cf_b_rate = weighted_m / total_p_21 * 1000 if total_p_21 else 0
print(f"  -> {cf_b_rate:.2f} per 1000")
print(f"     (vs 2021 actual {aggregate_for_year(2021)[2]:.2f} and 2024 actual {aggregate_for_year(2024)[2]:.2f})")

print("""
Interpretation:
  - Counterfactual A isolates COMPOSITION effects: how different would the rate
    be in 2024 if no field's rate had changed, only the mix of papers?
  - Counterfactual B isolates WITHIN-field effects: how different would the rate
    be if the mix were fixed but every field's rate moved to its 2024 value?
  - If A is close to the actual 2021 rate, composition explains little.
  - If B is close to the actual 2024 rate, within-field decline explains most.
""")
