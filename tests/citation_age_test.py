import duckdb
import numpy as np
from scipy.stats import mannwhitneyu

con = duckdb.connect("data/citations.duckdb")

print("Testing whether citation age changed significantly after ChatGPT...")

# get individual citation ages for pre and post periods
pre = con.execute("""
    SELECT w_citing.year - w_cited.year AS citation_age
    FROM citations c
    JOIN works w_citing ON c.citing_id = w_citing.id
    JOIN works w_cited ON c.cited_id = w_cited.id
    WHERE w_citing.year BETWEEN 2020 AND 2021
    AND w_cited.year BETWEEN 1950 AND 2024
    AND w_citing.year >= w_cited.year
""").fetchall()

post = con.execute("""
    SELECT w_citing.year - w_cited.year AS citation_age
    FROM citations c
    JOIN works w_citing ON c.citing_id = w_citing.id
    JOIN works w_cited ON c.cited_id = w_cited.id
    WHERE w_citing.year BETWEEN 2023 AND 2024
    AND w_cited.year BETWEEN 1950 AND 2024
    AND w_citing.year >= w_cited.year
""").fetchall()

pre_ages = [r[0] for r in pre]
post_ages = [r[0] for r in post]

print(f"\nPre-ChatGPT (2020-2021): {len(pre_ages):,} citations")
print(f"Post-ChatGPT (2023-2024): {len(post_ages):,} citations")
print(f"\nPre avg age: {np.mean(pre_ages):.4f} years")
print(f"Post avg age: {np.mean(post_ages):.4f} years")
print(f"\nPre median age: {np.median(pre_ages):.4f} years")
print(f"Post median age: {np.median(post_ages):.4f} years")

# Mann-Whitney U test — compares distributions without assuming normality
stat, pvalue = mannwhitneyu(post_ages, pre_ages, alternative="greater")

print(f"\nMann-Whitney U statistic: {stat:.4f}")
print(f"P-value: {pvalue:.10f}")

if pvalue < 0.05:
    print("Result: statistically significant (p < 0.05)")
    print("Citation age is significantly OLDER after ChatGPT.")
else:
    print("Result: not statistically significant (p >= 0.05)")
    print("Cannot conclude that citation age changed after ChatGPT.")
