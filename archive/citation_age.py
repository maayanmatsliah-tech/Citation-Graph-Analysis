import duckdb
import matplotlib.pyplot as plt

con = duckdb.connect("data/citations.duckdb")

print("Analyzing average age of cited papers by year...")

results = con.execute("""
    SELECT 
        w_citing.year AS citing_year,
        AVG(w_citing.year - w_cited.year) AS avg_citation_age
    FROM citations c
    JOIN works w_citing ON c.citing_id = w_citing.id
    JOIN works w_cited ON c.cited_id = w_cited.id
    WHERE w_citing.year BETWEEN 2018 AND 2024
    AND w_cited.year BETWEEN 1950 AND 2024
    AND w_citing.year >= w_cited.year
    GROUP BY w_citing.year
    ORDER BY w_citing.year
""").fetchall()

print("\n=== Average Age of Cited Papers ===")
for r in results:
    print(f"{r[0]}: {r[1]:.2f} years")

years = [r[0] for r in results]
ages = [r[1] for r in results]

plt.figure(figsize=(10, 5))
plt.bar(years, ages, color="steelblue", edgecolor="white")
plt.axvline(x=2022.9, color="red", linestyle="--", label="ChatGPT launch")
plt.title("Average Age of Cited Papers Per Year")
plt.xlabel("Year of citing paper")
plt.ylabel("Average age of cited paper (years)")
plt.legend()
plt.tight_layout()
plt.savefig("outputs/citation_age.png", dpi=150)
plt.show()

print("\ndone.")