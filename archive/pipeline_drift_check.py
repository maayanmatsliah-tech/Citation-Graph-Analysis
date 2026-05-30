"""
Pipeline-drift / dataset-artifact diagnostics.

Hypothesis to test: part of what looks like a "secular decline" in mutual
citation rates is actually OpenAlex pipeline drift — specifically, changing
preprint→journal deduplication semantics that erase what used to look like
distinct preprint→article forward citations.

We don't have multiple snapshots of the same paper, so we can't test
versioning directly. But we can test for fingerprints of pipeline drift:

  1. Type-share by year. If preprints are increasingly being collapsed into
     their journal versions, the type='preprint' share among recent papers
     should fall over time relative to older years.

  2. Type-share by year FOR mutual-pair papers specifically. Mutual pairs
     are sensitive to preprint existence (a gap=1 mutual requires the
     earlier paper to forward-cite the later one, which usually means
     citing a preprint). If preprint-typed papers are vanishing from the
     pair-participant set faster than from the works table overall, the
     pair decline tracks the type-share decline.

  3. Type composition of forward (gap=+1) citations vs other citation
     classes. If forward citations are disproportionately preprint→X edges,
     and preprints are being deduped, the forward collapse has a mechanical
     explanation.

  4. Field heterogeneity of the secular decline. Preprint-heavy fields
     (Computer Science, Mathematics, Physics) should show a stronger
     decline than fields that don't use preprints (most empirical/medical
     fields). If the decline is concentrated in preprint-heavy fields,
     that's strong indirect evidence for the dedup hypothesis. If it's
     uniform across fields, the artifact story is weaker.
"""

import duckdb
import numpy as np

con = duckdb.connect("data/citations.duckdb", read_only=True)

# -------- 1. type-share across years for ALL backfilled papers --------
print("=" * 78)
print("1. TYPE DISTRIBUTION OVER TIME (for papers with backfilled type)")
print("=" * 78)
print("If preprint dedup is increasing, preprint share among recent papers should fall.\n")

rows = con.execute("""
    SELECT year, type, COUNT(*) AS n
    FROM works
    WHERE year BETWEEN 2020 AND 2024
      AND type IS NOT NULL
    GROUP BY year, type
    ORDER BY year, n DESC
""").fetchall()

types_seen = sorted({t for _, t, _ in rows})
year_totals = {}
year_type = {}
for y, t, n in rows:
    year_totals[y] = year_totals.get(y, 0) + n
    year_type[(y, t)] = n

print(f"  Note: type was only backfilled for mutual-pair-participating papers")
print(f"        (~16k papers), so these counts are NOT the full works table.\n")
print(f"{'year':<6}{'total':>8}  " + "  ".join(f"{t[:12]:>12}" for t in types_seen))
for y in sorted(year_totals):
    row = [f"{year_type.get((y, t), 0):>12,}" for t in types_seen]
    print(f"{y:<6}{year_totals[y]:>8,}  " + "  ".join(row))

print(f"\n{'year':<6}{'total':>8}  " + "  ".join(f"{t[:12]:>12}" for t in types_seen) + "  (as %)")
for y in sorted(year_totals):
    row = [
        f"{(year_type.get((y, t), 0) / year_totals[y] * 100 if year_totals[y] else 0):>11.1f}%"
        for t in types_seen
    ]
    print(f"{y:<6}{year_totals[y]:>8,}  " + "  ".join(row))


# -------- 2. type composition of forward (gap=+1) vs same-year vs backward --------
print()
print("=" * 78)
print("2. CITATION-TYPE COMPOSITION: are forward citations dominated by preprints?")
print("=" * 78)
print("Forward (gap=+1) edges should be enriched for preprints if the dedup story is right.\n")

# Get type for both endpoints of every citation in 2020-2024 across years
rows = con.execute("""
    SELECT
        wc.year AS citing_y,
        wd.year AS cited_y,
        wc.type AS citing_type,
        wd.type AS cited_type,
        COUNT(*) AS n
    FROM citations c
    JOIN works wc ON c.citing_id = wc.id
    JOIN works wd ON c.cited_id  = wd.id
    WHERE c.citing_id <> c.cited_id
      AND wc.year BETWEEN 2020 AND 2024
      AND wd.year BETWEEN 2020 AND 2024
      AND wc.type IS NOT NULL
      AND wd.type IS NOT NULL
    GROUP BY wc.year, wd.year, wc.type, wd.type
""").fetchall()

# bucket by gap
fwd_total, fwd_with_preprint = 0, 0
same_total, same_with_preprint = 0, 0
back_total, back_with_preprint = 0, 0

fwd_type_pairs = {}
back_type_pairs = {}
same_type_pairs = {}

for cy, dy, ct, dt, n in rows:
    gap = dy - cy
    pair = (ct, dt)
    has_pre = ct == "preprint" or dt == "preprint"
    if gap > 0:
        fwd_total += n
        if has_pre:
            fwd_with_preprint += n
        fwd_type_pairs[pair] = fwd_type_pairs.get(pair, 0) + n
    elif gap == 0:
        same_total += n
        if has_pre:
            same_with_preprint += n
        same_type_pairs[pair] = same_type_pairs.get(pair, 0) + n
    else:
        back_total += n
        if has_pre:
            back_with_preprint += n
        back_type_pairs[pair] = back_type_pairs.get(pair, 0) + n


def share(part, whole):
    return part / whole * 100 if whole else 0.0


print(f"  Citation class       count       with-preprint   preprint-touch share")
print(f"  forward  (gap>0)  {fwd_total:>10,}   {fwd_with_preprint:>10,}     {share(fwd_with_preprint, fwd_total):>5.1f}%")
print(f"  same-year (gap=0) {same_total:>10,}   {same_with_preprint:>10,}     {share(same_with_preprint, same_total):>5.1f}%")
print(f"  backward (gap<0)  {back_total:>10,}   {back_with_preprint:>10,}     {share(back_with_preprint, back_total):>5.1f}%")

print("\nTop type-pair compositions:")
for label, d, total in [
    ("forward",  fwd_type_pairs,  fwd_total),
    ("same-year", same_type_pairs, same_total),
    ("backward", back_type_pairs, back_total),
]:
    print(f"  {label}:")
    top = sorted(d.items(), key=lambda kv: -kv[1])[:5]
    for (ct, dt), n in top:
        print(f"    {ct:<14} -> {dt:<14}  {n:>9,}  ({share(n, total):>5.1f}%)")


# -------- 3. type-share among mutual-pair-participating papers, by year --------
print()
print("=" * 78)
print("3. TYPE DISTRIBUTION OF MUTUAL-PAIR PARTICIPANTS, BY YEAR")
print("=" * 78)
print("If the pair decline is driven by preprint dedup, the preprint share among")
print("pair-participating papers should fall faster than in the works table at large.\n")

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
    )
    SELECT w.year, w.type, COUNT(*) AS n
    FROM pair_papers pp
    JOIN works w ON pp.p = w.id
    WHERE w.year BETWEEN 2020 AND 2024
      AND w.type IS NOT NULL
    GROUP BY w.year, w.type
    ORDER BY w.year, n DESC
""").fetchall()

year_totals = {}
year_type = {}
types_seen = sorted({t for _, t, _ in rows})
for y, t, n in rows:
    year_totals[y] = year_totals.get(y, 0) + n
    year_type[(y, t)] = n

print(f"{'year':<6}{'total':>8}  " + "  ".join(f"{t[:12]:>12}" for t in types_seen))
for y in sorted(year_totals):
    row = [f"{year_type.get((y, t), 0):>12,}" for t in types_seen]
    print(f"{y:<6}{year_totals[y]:>8,}  " + "  ".join(row))

print(f"\n{'year':<6}{'total':>8}  " + "  ".join(f"{t[:12]:>12}" for t in types_seen) + "  (as %)")
for y in sorted(year_totals):
    row = [
        f"{(year_type.get((y, t), 0) / year_totals[y] * 100):>11.1f}%"
        for t in types_seen
    ]
    print(f"{y:<6}{year_totals[y]:>8,}  " + "  ".join(row))


# -------- 4. field heterogeneity of the secular decline --------
print()
print("=" * 78)
print("4. FIELD HETEROGENEITY OF MUTUAL CITATION DECLINE")
print("=" * 78)
print("Preprint-heavy fields (CS, Math, Physics) should show stronger declines")
print("than empirical fields if pipeline drift is part of the story.\n")

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
    per_field_year AS (
        SELECT w.field, w.year,
               COUNT(*) AS papers,
               SUM(CASE WHEN pp.p IS NOT NULL THEN 1 ELSE 0 END) AS in_mutual
        FROM works w
        LEFT JOIN pair_papers pp ON pp.p = w.id
        WHERE w.year BETWEEN 2020 AND 2024
        GROUP BY w.field, w.year
    )
    SELECT field, year, papers, in_mutual
    FROM per_field_year
    WHERE papers > 1000  -- ignore tiny fields
    ORDER BY field, year
""").fetchall()

by_field = {}
for f, y, p, m in rows:
    by_field.setdefault(f, {})[y] = (p, m)


def fit_trend(field_data, exclude_2020=True):
    """Fit log-rate trend on 2021-2024, return annualized %/yr or None."""
    years = sorted(field_data)
    if exclude_2020:
        years = [y for y in years if y != 2020]
    if len(years) < 3:
        return None
    rates = []
    for y in years:
        p, m = field_data[y]
        if p == 0 or m == 0:
            return None
        rates.append(m / p * 1000)
    log_r = np.log(rates)
    x = np.array(years, dtype=float)
    slope = np.polyfit(x, log_r, 1)[0]
    return (np.exp(slope) - 1) * 100, rates


# Common preprint-heavy fields (heuristic)
PREPRINT_HEAVY = {
    "Computer Science", "Mathematics", "Physics and Astronomy",
    "Biochemistry, Genetics and Molecular Biology",
}

results = []
for field, data in by_field.items():
    fit = fit_trend(data)
    if fit is None:
        continue
    annual_pct, rates = fit
    # 2021 rate vs 2024 rate for absolute change
    if 2021 in data and 2024 in data:
        r21 = data[2021][1] / data[2021][0] * 1000
        r24 = data[2024][1] / data[2024][0] * 1000
        total_change = (r24 / r21 - 1) * 100 if r21 > 0 else None
    else:
        total_change = None
    results.append((field, annual_pct, total_change, data))

# Sort by slope (most negative = steepest decline)
results.sort(key=lambda r: r[1])

print(f"{'field':<48}  {'annual %/yr':>11}  {'2021->2024':>10}  {'preprint-heavy?':>15}")
for field, annual_pct, total_change, _ in results:
    pre_flag = "YES" if field in PREPRINT_HEAVY else ""
    tc_str = f"{total_change:>+9.1f}%" if total_change is not None else "       n/a"
    print(f"  {field:<46}  {annual_pct:>+10.1f}%  {tc_str}  {pre_flag:>15}")

# Summary: average decline rate for preprint-heavy vs not
pre_heavy = [r[1] for r in results if r[0] in PREPRINT_HEAVY]
others = [r[1] for r in results if r[0] not in PREPRINT_HEAVY]
print(f"\nMean annual decline for preprint-heavy fields ({len(pre_heavy)}): {np.mean(pre_heavy):+.1f}%/yr")
print(f"Mean annual decline for other fields ({len(others)}):           {np.mean(others):+.1f}%/yr")
if abs(np.mean(pre_heavy)) > abs(np.mean(others)):
    print("-> preprint-heavy fields decline FASTER. Consistent with pipeline-drift story.")
else:
    print("-> preprint-heavy fields decline SLOWER or comparable. Pipeline-drift story weakened.")
