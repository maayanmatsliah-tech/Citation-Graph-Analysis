import duckdb
import matplotlib.pyplot as plt

con = duckdb.connect("citations.duckdb")

data = con.execute("""
    SELECT 
        w.id,
        w.year AS pub_year,
        MIN(w_citing.year) AS first_citation,
        MAX(w_citing.year) AS last_citation,
        MAX(w_citing.year) - w.year AS lifespan,
        COUNT(DISTINCT c.citing_id) AS total_citers
    FROM works w
    JOIN citations c ON c.cited_id = w.id
    JOIN works w_citing ON c.citing_id = w_citing.id
    WHERE w.year BETWEEN 1960 AND 1989
    AND w_citing.year >= w.year    GROUP BY w.id, w.year
    HAVING MIN(w_citing.year) - w.year <= 10
""").fetchall()

lifespans = [r[4] for r in data]
pub_years = [r[1] for r in data]

print(f"Total papers: {len(lifespans)}")
print(f"Average lifespan: {sum(lifespans)/len(lifespans):.1f} years")
print(f"Shortest: {min(lifespans)} years")
print(f"Longest: {max(lifespans)} years")

plt.figure(figsize=(12, 5))
plt.hist(lifespans, bins=40, color="steelblue", edgecolor="white")
plt.title("Citation Lifespan Distribution (1960-1989 papers)")
plt.xlabel("Years from publication to last citation")
plt.ylabel("Number of papers")
plt.tight_layout()
plt.savefig("lifespan_distribution.png", dpi=150)
plt.show()
plt.save()