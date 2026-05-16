import duckdb
import numpy as np
from scipy.stats import chi2_contingency

con = duckdb.connect("data/citations.duckdb")

# count distinct papers participating in at least one mutual citation, by year
# - a.citing_id < a.cited_id filters out self-cites and counts each unordered
#   pair {X, Y} exactly once
papers_in_mutual = con.execute("""
    WITH mutual_pairs AS (
        SELECT a.citing_id AS p1, a.cited_id AS p2
        FROM citations a
        JOIN citations b ON a.citing_id = b.cited_id AND a.cited_id = b.citing_id
        WHERE a.citing_id < a.cited_id
    ),
    paper_in_any AS (
        SELECT DISTINCT p1 AS pid FROM mutual_pairs
        UNION
        SELECT DISTINCT p2 FROM mutual_pairs
    )
    SELECT w.year, COUNT(*) AS papers_in_mutual
    FROM paper_in_any pi
    JOIN works w ON pi.pid = w.id
    WHERE w.year BETWEEN 2018 AND 2024
    GROUP BY w.year
""").fetchall()

papers = con.execute(
    "SELECT year, COUNT(*) FROM works WHERE year BETWEEN 2018 AND 2024 GROUP BY year"
).fetchall()

in_mutual = {r[0]: r[1] for r in papers_in_mutual}
paper_dict = {r[0]: r[1] for r in papers}

pre_in_mutual = in_mutual.get(2020, 0) + in_mutual.get(2021, 0)
post_in_mutual = in_mutual.get(2023, 0) + in_mutual.get(2024, 0)
pre_papers = paper_dict.get(2020, 0) + paper_dict.get(2021, 0)
post_papers = paper_dict.get(2023, 0) + paper_dict.get(2024, 0)

pre_not_in = pre_papers - pre_in_mutual
post_not_in = post_papers - post_in_mutual

print(f"Pre-ChatGPT  (2020-2021): {pre_in_mutual:,} of {pre_papers:,} papers in mutual pairs")
print(f"Post-ChatGPT (2023-2024): {post_in_mutual:,} of {post_papers:,} papers in mutual pairs")

pre_rate = pre_in_mutual / pre_papers * 1000
post_rate = post_in_mutual / post_papers * 1000

print(f"Pre rate:  {pre_rate:.4f} papers in mutual pairs per 1000 papers")
print(f"Post rate: {post_rate:.4f} papers in mutual pairs per 1000 papers")

# 2x2 paper-level contingency table — each paper is a Bernoulli trial
# (in a mutual pair or not), grouped by period
table = np.array([[pre_in_mutual, pre_not_in], [post_in_mutual, post_not_in]])

chi2, pvalue, dof, expected = chi2_contingency(table)

print(f"\nChi-square statistic: {chi2:.4f}")
print(f"P-value: {pvalue:.10f}")

if pvalue < 0.05:
    print("Result: statistically significant (p < 0.05)")
    if post_rate > pre_rate:
        print("Mutual citation participation INCREASED after ChatGPT.")
    else:
        print("Mutual citation participation DECREASED after ChatGPT.")
else:
    print("Result: not statistically significant (p >= 0.05)")
    print("Cannot conclude that ChatGPT changed mutual citation rates.")
