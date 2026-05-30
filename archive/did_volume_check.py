"""Robustness check on did_analysis.py.

Concern: post-ChatGPT years may simply contain a higher share of low-quality
papers that nobody cites. The mutual-pair-membership rate would then drop
even with unchanged citing-author behavior. If that is what's driving the
DiD result, we should also see:
  - avg incoming citations per paper falling MORE in HIGH than in LOW, and
  - the ratio (avg mutual / avg total citations) staying roughly flat.
If instead the mutual-pair share of total citations also drops in HIGH, the
original finding survives the volume/composition confound.
"""

import duckdb
import numpy as np

con = duckdb.connect("data/citations.duckdb", read_only=True)

HIGH_EXPOSURE = ["Computer Science"]
LOW_EXPOSURE = [
    "Chemistry",
    "Materials Science",
    "Agricultural and Biological Sciences",
    "Earth and Planetary Sciences",
    "Immunology and Microbiology",
]


def per_year_stats(fields):
    """For each year 2021-2024 return:
        papers       -- paper count in field set
        total_cites  -- sum of incoming citations to those papers (in-dataset)
        mutual_edges -- sum of mutual-pair memberships for those papers
                        (a paper in k mutual pairs contributes k)
    """
    placeholders = ",".join(["?"] * len(fields))
    rows = con.execute(f"""
        WITH target AS (
            SELECT id, year
            FROM works
            WHERE field IN ({placeholders})
              AND year BETWEEN 2021 AND 2024
        ),
        incoming AS (
            SELECT t.id, t.year, COUNT(c.citing_id) AS n_cites
            FROM target t
            LEFT JOIN citations c ON c.cited_id = t.id
            GROUP BY t.id, t.year
        ),
        mutual_pairs AS (
            SELECT a.citing_id AS p1, a.cited_id AS p2
            FROM citations a
            JOIN citations b ON a.citing_id = b.cited_id
                            AND a.cited_id = b.citing_id
            WHERE a.citing_id < a.cited_id
        ),
        mutual_memberships AS (
            -- one row per (paper, mutual-pair) it participates in
            SELECT p1 AS pid FROM mutual_pairs
            UNION ALL
            SELECT p2 AS pid FROM mutual_pairs
        ),
        mutual_per_paper AS (
            SELECT t.id, t.year, COUNT(m.pid) AS n_mutual
            FROM target t
            LEFT JOIN mutual_memberships m ON m.pid = t.id
            GROUP BY t.id, t.year
        )
        SELECT i.year,
               COUNT(*)              AS papers,
               SUM(i.n_cites)        AS total_cites,
               SUM(mp.n_mutual)      AS mutual_edges
        FROM incoming i
        JOIN mutual_per_paper mp USING (id, year)
        GROUP BY i.year
        ORDER BY i.year
    """, fields).fetchall()
    return {y: dict(papers=p, total=t, mutual=m) for y, p, t, m in rows}


def summarize(label, data):
    print(f"=== {label} ===")
    print(f"  {'year':>4}  {'papers':>8}  {'tot_cites':>10}  "
          f"{'avg_cit/p':>10}  {'mut_edges':>10}  {'avg_mut/p':>10}  "
          f"{'mut/cit %':>10}")
    for y in sorted(data):
        d = data[y]
        avg_cit = d["total"] / d["papers"]
        avg_mut = d["mutual"] / d["papers"]
        share = d["mutual"] / d["total"] * 100 if d["total"] else float("nan")
        print(f"  {y:>4}  {d['papers']:>8,}  {d['total']:>10,}  "
              f"{avg_cit:>10.3f}  {d['mutual']:>10,}  {avg_mut:>10.4f}  "
              f"{share:>9.2f}%")


def pool(data, years):
    papers = sum(data[y]["papers"] for y in years)
    total  = sum(data[y]["total"]  for y in years)
    mutual = sum(data[y]["mutual"] for y in years)
    return papers, total, mutual


high = per_year_stats(HIGH_EXPOSURE)
low  = per_year_stats(LOW_EXPOSURE)

print(f"HIGH exposure fields: {HIGH_EXPOSURE}")
print(f"LOW  exposure fields: {LOW_EXPOSURE}\n")
summarize("HIGH (Computer Science)", high)
print()
summarize("LOW (5 empirical fields)", low)

PRE  = [2021, 2022]
POST = [2023, 2024]

print("\n=== Pre (2021-2022) vs Post (2023-2024), pooled ===")
print(f"  {'group':<6}  {'period':<5}  {'papers':>8}  "
      f"{'avg_cit/p':>10}  {'avg_mut/p':>10}  {'mut/cit %':>10}")

results = {}
for label, data in [("HIGH", high), ("LOW", low)]:
    for period_name, years in [("pre", PRE), ("post", POST)]:
        p, t, m = pool(data, years)
        avg_cit = t / p
        avg_mut = m / p
        share   = m / t * 100
        results[(label, period_name)] = dict(avg_cit=avg_cit, avg_mut=avg_mut, share=share,
                                             papers=p, total=t, mutual=m)
        print(f"  {label:<6}  {period_name:<5}  {p:>8,}  "
              f"{avg_cit:>10.3f}  {avg_mut:>10.4f}  {share:>9.2f}%")

def pct_change(a, b):
    return (b / a - 1) * 100

print("\n=== Pre -> Post change, by group ===")
for label in ["HIGH", "LOW"]:
    pre, post = results[(label, "pre")], results[(label, "post")]
    print(f"  {label}:  avg_cit/paper  {pre['avg_cit']:7.3f} -> {post['avg_cit']:7.3f}  "
          f"({pct_change(pre['avg_cit'],  post['avg_cit']):+6.1f}%)")
    print(f"  {label}:  avg_mut/paper  {pre['avg_mut']:7.4f} -> {post['avg_mut']:7.4f}  "
          f"({pct_change(pre['avg_mut'],  post['avg_mut']):+6.1f}%)")
    print(f"  {label}:  mutual/total   {pre['share']:7.2f}% -> {post['share']:7.2f}%  "
          f"({pct_change(pre['share'],   post['share']):+6.1f}%)")
    print()

print("=== Difference-in-differences (log-ratio) ===")
def did_log(metric_key):
    hp = np.log(results[("HIGH","post")][metric_key])  - np.log(results[("HIGH","pre")][metric_key])
    lp = np.log(results[("LOW", "post")][metric_key])  - np.log(results[("LOW", "pre")][metric_key])
    return hp - lp, hp, lp

for label, key in [("avg citations / paper", "avg_cit"),
                   ("avg mutual edges / paper", "avg_mut"),
                   ("mutual share of citations", "share")]:
    did, hp, lp = did_log(key)
    print(f"  {label:<28}  HIGH: {hp:+.4f}  LOW: {lp:+.4f}  DiD: {did:+.4f}")

print("""
Interpretation guide:
  - If HIGH's avg_cit/paper drops much more than LOW's, the 2023-2024 CS
    cohort is genuinely less citable on average (the volume/garbage story).
  - If 'mutual share of citations' ALSO drops in HIGH more than LOW, then
    even controlling for overall citedness, mutual pairs are a smaller slice
    of the citation pie in CS post-ChatGPT, supporting the original finding.
  - If the share is flat or moves the same in both groups, the original DiD
    on mutual-pair membership rate is mostly a composition artifact.
""")
