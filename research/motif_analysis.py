import duckdb
import matplotlib.pyplot as plt

con = duckdb.connect("data/citations.duckdb")

print("Analyzing mutual citation motifs before and after ChatGPT...")

# count mutual citation pairs per year
mutual_by_year = con.execute("""
    SELECT 
        GREATEST(w_a.year, w_b.year) AS year,
        COUNT(*) AS mutual_pairs
    FROM citations a
    JOIN citations b 
        ON a.citing_id = b.cited_id 
        AND a.cited_id = b.citing_id
    JOIN works w_a ON a.citing_id = w_a.id
    JOIN works w_b ON a.cited_id = w_b.id
    WHERE w_a.year IS NOT NULL
    AND w_b.year IS NOT NULL
    AND w_a.year BETWEEN 2018 AND 2024
    AND w_b.year BETWEEN 2018 AND 2024
    GROUP BY GREATEST(w_a.year, w_b.year)
    ORDER BY year
""").fetchall()

# total papers per year for normalization
papers_by_year = con.execute("""
    SELECT year, COUNT(*) as total
    FROM works
    WHERE year BETWEEN 2018 AND 2024
    GROUP BY year
    ORDER BY year
""").fetchall()

paper_counts = {r[0]: r[1] for r in papers_by_year}
years = [r[0] for r in mutual_by_year]
pairs = [r[1] for r in mutual_by_year]
rates = [p / paper_counts.get(y, 1) * 1000 for p, y in zip(pairs, years)]

# print results
print("\n=== Mutual Citations Per Year ===")
for y, p, r in zip(years, pairs, rates):
    print(f"{y}: {p:,} pairs | {r:.2f} per 1000 papers")

# plot
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Mutual Citation Patterns Before and After ChatGPT (Nov 2022)", fontsize=13)

axes[0].bar(years, pairs, color="steelblue", edgecolor="white")
axes[0].axvline(x=2022.9, color="red", linestyle="--", label="ChatGPT launch")
axes[0].set_title("Mutual Citation Pairs Per Year")
axes[0].set_xlabel("Year")
axes[0].set_ylabel("Number of mutual pairs")
axes[0].legend()

axes[1].bar(years, rates, color="coral", edgecolor="white")
axes[1].axvline(x=2022.9, color="red", linestyle="--", label="ChatGPT launch")
axes[1].set_title("Mutual Citations per 1000 Papers")
axes[1].set_xlabel("Year")
axes[1].set_ylabel("Rate per 1000 papers")
axes[1].legend()

plt.tight_layout()
plt.savefig("outputs/motif_analysis.png", dpi=150)
plt.show()

from scipy.stats import proportions_ztest
import numpy as np

print("\n=== Statistical Significance Test ===")

# pre-ChatGPT: 2020-2021 combined
pre_years = [y for y in years if y <= 2021]
post_years = [y for y in years if y >= 2023]

pre_pairs = sum(mutual_counts.get(y, 0) for y in pre_years)
post_pairs = sum(mutual_counts.get(y, 0) for y in post_years)

pre_papers = sum(paper_counts.get(y, 0) for y in pre_years)
post_papers = sum(paper_counts.get(y, 0) for y in post_years)

print(f"Pre-ChatGPT (2020-2021): {pre_pairs:,} mutual pairs out of {pre_papers:,} papers")
print(f"Post-ChatGPT (2023-2024): {post_pairs:,} mutual pairs out of {post_papers:,} papers")

pre_rate = pre_pairs / pre_papers * 1000
post_rate = post_pairs / post_papers * 1000

print(f"Pre rate: {pre_rate:.4f} per 1000 papers")
print(f"Post rate: {post_rate:.4f} per 1000 papers")

# run the test
counts = np.array([post_pairs, pre_pairs])
nobs = np.array([post_papers, pre_papers])

stat, pvalue = proportions_ztest(counts, nobs)

print(f"\nZ-statistic: {stat:.4f}")
print(f"P-value: {pvalue:.6f}")

if pvalue < 0.05:
    print("Result: statistically significant (p < 0.05)")
    if post_rate > pre_rate:
        print("Mutual citation rate INCREASED after ChatGPT.")
    else:
        print("Mutual citation rate DECREASED after ChatGPT.")
else:
    print("Result: not statistically significant (p >= 0.05)")
    print("Cannot conclude that ChatGPT changed mutual citation rates.")


print("\ndone.")
