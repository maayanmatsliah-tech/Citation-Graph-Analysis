import duckdb
import matplotlib.pyplot as plt

con = duckdb.connect("citations.duckdb")

# --- get all sleeping beauties (slept 10+ years) ---
data = con.execute("""
    WITH citation_counts AS (
        SELECT
            cited_id,
            published_year,
            citation_year,
            citation_year - published_year AS age,
            COUNT(*) AS citations_that_year
        FROM citation_timeline
        GROUP BY cited_id, published_year, citation_year
    ),
    earliest_citation AS (
        SELECT
            cited_id,
            published_year,
            MIN(age) AS sleep_length,
            MIN(citation_year) AS awakening_year
        FROM citation_counts
        GROUP BY cited_id, published_year
    ),
    peak AS (
        SELECT
            cc.cited_id,
            MAX(cc.citations_that_year) AS peak_citations,
            MIN(cc.citation_year) FILTER (
                WHERE cc.citations_that_year = (
                    SELECT MAX(citations_that_year) 
                    FROM citation_counts cc2 
                    WHERE cc2.cited_id = cc.cited_id
                )
            ) AS peak_year
        FROM citation_counts cc
        GROUP BY cc.cited_id
    )
    SELECT
        e.published_year,
        e.sleep_length,
        e.awakening_year,
        p.peak_citations,
        p.peak_year - e.awakening_year AS time_to_peak
    FROM earliest_citation e
    JOIN peak p ON e.cited_id = p.cited_id
    WHERE e.sleep_length >= 10
""").fetchall()

published_years = [r[0] for r in data]
sleep_lengths   = [r[1] for r in data]
awakening_years = [r[2] for r in data]
peak_citations  = [r[3] for r in data]
time_to_peak    = [r[4] for r in data]

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle("Sleeping Beauty Analysis", fontsize=16)

# 1. sleep length distribution
axes[0,0].hist(sleep_lengths, bins=40, color="steelblue", edgecolor="white")
axes[0,0].set_title("Sleep Length Distribution")
axes[0,0].set_xlabel("Years slept before first citation")
axes[0,0].set_ylabel("Number of papers")

# 2. awakening year distribution
axes[0,1].hist(awakening_years, bins=40, color="coral", edgecolor="white")
axes[0,1].set_title("Awakening Year Distribution")
axes[0,1].set_xlabel("Year of first citation")
axes[0,1].set_ylabel("Number of papers")

# 3. sleep length vs peak citations
axes[0,2].scatter(sleep_lengths, peak_citations, alpha=0.3, color="purple", s=10)
axes[0,2].set_title("Sleep Length vs Peak Citations")
axes[0,2].set_xlabel("Years slept")
axes[0,2].set_ylabel("Peak citations in one year")

# 4. publication decade vs avg sleep length
decades = {}
for pub_year, sleep in zip(published_years, sleep_lengths):
    decade = (pub_year // 10) * 10
    if decade not in decades:
        decades[decade] = []
    decades[decade].append(sleep)
decade_keys = sorted(decades.keys())
decade_avgs = [sum(decades[d]) / len(decades[d]) for d in decade_keys]
axes[1,0].bar(decade_keys, decade_avgs, width=8, color="teal", edgecolor="white")
axes[1,0].set_title("Publication Decade vs Avg Sleep Length")
axes[1,0].set_xlabel("Publication decade")
axes[1,0].set_ylabel("Avg years slept")

# 5. time to peak after awakening
filtered = [t for t in time_to_peak if t is not None and 0 <= t <= 50]
axes[1,1].hist(filtered, bins=30, color="goldenrod", edgecolor="white")
axes[1,1].set_title("Time to Peak After Awakening")
axes[1,1].set_xlabel("Years from awakening to peak citations")
axes[1,1].set_ylabel("Number of papers")

# 6. awakening year vs sleep length
axes[1,2].scatter(awakening_years, sleep_lengths, alpha=0.3, color="green", s=10)
axes[1,2].set_title("Awakening Year vs Sleep Length")
axes[1,2].set_xlabel("Year awakened")
axes[1,2].set_ylabel("Years slept")

plt.tight_layout()
plt.savefig("sleeping_beauty_analysis.png", dpi=150)
plt.show()
print("saved to sleeping_beauty_analysis.png")

# zoom into the stripe pattern
awakening_counts = {}
for year in awakening_years:
    awakening_counts[year] = awakening_counts.get(year, 0) + 1

sorted_years = sorted(awakening_counts.keys())
counts = [awakening_counts[y] for y in sorted_years]

plt.figure(figsize=(14, 5))
plt.bar(sorted_years, counts, color="green", edgecolor="white", width=0.8)
plt.title("Number of Sleeping Beauty Awakenings Per Year")
plt.xlabel("Year")
plt.ylabel("Papers awakened")
plt.tight_layout()
plt.savefig("awakening_spikes.png", dpi=150)
plt.show()