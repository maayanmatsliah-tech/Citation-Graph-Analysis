import duckdb

con = duckdb.connect("citations.duckdb")

# for each cited paper, get the year the citation came from
# (approximated by the citing paper's publication year)
print("Building citation timeline...")
con.execute("""
    CREATE TABLE IF NOT EXISTS citation_timeline AS
    SELECT 
        c.cited_id,
        w_citing.year AS citation_year,
        w_cited.year AS published_year
    FROM citations c
    JOIN works w_citing ON c.citing_id = w_citing.id
    JOIN works w_cited ON c.cited_id = w_cited.id
    WHERE w_cited.year BETWEEN 1950 AND 1995
    AND w_citing.year IS NOT NULL
    AND w_cited.year IS NOT NULL
""")

print("Done. Rows:", con.execute("SELECT COUNT(*) FROM citation_timeline").fetchone()[0])

print("Detecting sleeping beauties...")

print("Checking data shape...")
diag = con.execute("""
    WITH citation_counts AS (
        SELECT 
            cited_id,
            citation_year - published_year AS age,
            COUNT(*) AS citations_that_year
        FROM citation_timeline
        GROUP BY cited_id, published_year, citation_year
    )
    SELECT 
        MAX(citations_that_year) AS max_citations_in_one_year,
        AVG(citations_that_year) AS avg_citations_per_year,
        COUNT(DISTINCT cited_id) AS papers_with_post10_citations
    FROM citation_counts
    WHERE age > 10
""").fetchone()
print(f"Max citations in one year (post age 10): {diag[0]}")
print(f"Avg citations per year (post age 10): {round(diag[1], 3)}")
print(f"Papers with any post-10yr citation: {diag[2]}")

results = con.execute("""
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
    sleep_phase AS (
        SELECT 
            cited_id,
            published_year,
            AVG(citations_that_year) AS sleep_rate
        FROM citation_counts
        WHERE age BETWEEN 1 AND 10
        GROUP BY cited_id, published_year
    ),
    peak_phase AS (
        SELECT 
            cited_id,
            MAX(citations_that_year) AS peak_citations
        FROM citation_counts
        WHERE age > 10
        GROUP BY cited_id
    ),
    awakening AS (
        SELECT 
            cc.cited_id,
            MIN(cc.citation_year) AS awakening_year
        FROM citation_counts cc
        JOIN peak_phase p ON cc.cited_id = p.cited_id
        WHERE cc.citations_that_year = p.peak_citations
        AND cc.citation_year - cc.published_year > 10
        GROUP BY cc.cited_id
    )
    SELECT 
        w.title,
        w.year AS published_year,
        ROUND(s.sleep_rate, 2) AS avg_citations_first_10_years,
        p.peak_citations AS peak_citations_in_a_year,
        a.awakening_year
    FROM sleep_phase s
    JOIN peak_phase p ON s.cited_id = p.cited_id
    JOIN awakening a ON s.cited_id = a.cited_id
    JOIN works w ON s.cited_id = w.id
    WHERE s.sleep_rate < 1.0       -- looser sleep threshold
    AND p.peak_citations >= 3      -- looser awakening threshold
    ORDER BY p.peak_citations DESC
    LIMIT 20
""").fetchall()

print("\n=== Top Sleeping Beauties ===")
for row in results:
    print(f"\n'{row[0]}'")
    print(f"  Published: {row[1]}")
    print(f"  Avg citations/year (first 10 yrs): {row[2]}")
    print(f"  Peak citations in a single year: {row[3]}")
    print(f"  Awakening year: {row[4]}")

diag2 = con.execute("""
    WITH citation_counts AS (
        SELECT 
            cited_id,
            citation_year - published_year AS age,
            COUNT(*) AS citations_that_year
        FROM citation_timeline
        GROUP BY cited_id, published_year, citation_year
    )
    SELECT 
        COUNT(DISTINCT cited_id) AS has_early_citations,
    FROM citation_counts
    WHERE age BETWEEN 1 AND 10
""").fetchone()
print(f"Papers with early citations (age 1-10): {diag2[0]}")
