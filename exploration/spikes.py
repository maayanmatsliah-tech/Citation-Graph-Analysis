import duckdb
import matplotlib.pyplot as plt

con = duckdb.connect("citations.duckdb")

rows = con.execute("""
    WITH citation_counts AS (
        SELECT cited_id, published_year, citation_year,
               citation_year - published_year AS age,
               COUNT(*) AS citations_that_year
        FROM citation_timeline
        GROUP BY cited_id, published_year, citation_year
    ),
    earliest AS (
        SELECT cited_id, MIN(age) AS sleep_length, MIN(citation_year) AS awakening_year
        FROM citation_counts
        GROUP BY cited_id
    )
    SELECT awakening_year, COUNT(*) as count
    FROM earliest
    WHERE sleep_length >= 10
    GROUP BY awakening_year
    ORDER BY awakening_year
""").fetchall()

years = [r[0] for r in rows]
counts = [r[1] for r in rows]

plt.figure(figsize=(14, 5))
plt.bar(years, counts, color="green", edgecolor="white", width=0.8)
plt.title("Sleeping Beauty Awakenings Per Year")
plt.xlabel("Year awakened")
plt.ylabel("Number of papers")
plt.tight_layout()
plt.savefig("awakening_spikes.png", dpi=150)
plt.show()