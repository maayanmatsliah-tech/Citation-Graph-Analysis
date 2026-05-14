import duckdb
import numpy as np
from scipy.stats import chi2_contingency

con = duckdb.connect("data/citations.duckdb")

mutual = con.execute("""
    SELECT 
        GREATEST(w_a.year, w_b.year) AS year,
        COUNT(*) AS pairs
    FROM citations a
    JOIN citations b ON a.citing_id = b.cited_id AND a.cited_id = b.citing_id
    JOIN works w_a ON a.citing_id = w_a.id
    JOIN works w_b ON a.cited_id = w_b.id
    WHERE w_a.year BETWEEN 2018 AND 2024
    AND w_b.year BETWEEN 2018 AND 2024
    GROUP BY GREATEST(w_a.year, w_b.year)
""").fetchall()

papers = con.execute(
    "SELECT year, COUNT(*) FROM works WHERE year BETWEEN 2018 AND 2024 GROUP BY year"
).fetchall()

mutual_dict = {r[0]: r[1] for r in mutual}
paper_dict = {r[0]: r[1] for r in papers}

pre_pairs = mutual_dict.get(2020, 0) + mutual_dict.get(2021, 0)
post_pairs = mutual_dict.get(2023, 0) + mutual_dict.get(2024, 0)
pre_papers = paper_dict.get(2020, 0) + paper_dict.get(2021, 0)
post_papers = paper_dict.get(2023, 0) + paper_dict.get(2024, 0)

pre_non_mutual = pre_papers - pre_pairs
post_non_mutual = post_papers - post_pairs

print(f"Pre-ChatGPT (2020-2021): {pre_pairs:,} mutual / {pre_papers:,} papers")
print(f"Post-ChatGPT (2023-2024): {post_pairs:,} mutual / {post_papers:,} papers")

pre_rate = pre_pairs / pre_papers * 1000
post_rate = post_pairs / post_papers * 1000

print(f"Pre rate: {pre_rate:.4f} per 1000 papers")
print(f"Post rate: {post_rate:.4f} per 1000 papers")

# chi-square test on a 2x2 contingency table
table = np.array([[pre_pairs, pre_non_mutual], [post_pairs, post_non_mutual]])

chi2, pvalue, dof, expected = chi2_contingency(table)

print(f"\nChi-square statistic: {chi2:.4f}")
print(f"P-value: {pvalue:.10f}")

if pvalue < 0.05:
    print("Result: statistically significant (p < 0.05)")
    if post_rate > pre_rate:
        print("Mutual citation rate INCREASED after ChatGPT.")
    else:
        print("Mutual citation rate DECREASED after ChatGPT.")
else:
    print("Result: not statistically significant (p >= 0.05)")
    print("Cannot conclude that ChatGPT changed mutual citation rates.")
