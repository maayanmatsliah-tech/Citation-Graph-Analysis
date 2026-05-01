import duckdb

con = duckdb.connect("citations.duckdb")

# 1. what years are represented?
print("=== Papers by decade ===")
results = con.execute("""
    SELECT (year / 10) * 10 AS decade, COUNT(*) AS count
    FROM works
    GROUP BY decade
    ORDER BY decade
""").fetchall()
for row in results:
    print(f"{row[0]}s: {row[1]:,}")

# 2. most cited papers
print("\n=== Top 10 most cited papers ===")
results = con.execute("""
    SELECT w.title, w.year, COUNT(*) AS times_cited
    FROM citations c
    JOIN works w ON c.cited_id = w.id
    GROUP BY w.title, w.year
    ORDER BY times_cited DESC
    LIMIT 10
""").fetchall()
for row in results:
    print(f"{row[2]:,}x — ({row[1]}) {row[0]}")

# 3. how many papers have zero citations?
print("\n=== Citation distribution ===")
results = con.execute("""
    SELECT 
        COUNT(*) FILTER (WHERE times_cited = 0) AS uncited,
        COUNT(*) FILTER (WHERE times_cited BETWEEN 1 AND 10) AS low,
        COUNT(*) FILTER (WHERE times_cited BETWEEN 11 AND 100) AS medium,
        COUNT(*) FILTER (WHERE times_cited > 100) AS high
    FROM (
        SELECT w.id, COUNT(c.cited_id) AS times_cited
        FROM works w
        LEFT JOIN citations c ON c.cited_id = w.id
        GROUP BY w.id
    )
""").fetchone()
print(f"uncited:       {results[0]:,}")
print(f"cited 1-10x:   {results[1]:,}")
print(f"cited 11-100x: {results[2]:,}")
print(f"cited 100x+:   {results[3]:,}")