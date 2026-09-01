import duckdb

con = duckdb.connect('data/archive_pre_clean_rebuild/_mutual_clean.duckdb', read_only=True)

count = con.execute("SELECT count(*) FROM all_edges").fetchone()[0]
print(f"all_edges row count: {count:,}")

con.close()

# Write the full mutual pairs directly from all_edges, single pass
con2 = duckdb.connect('data/archive_pre_clean_rebuild/_mutual_clean.duckdb', read_only=True)
con2.execute("SET memory_limit='6GB'")
con2.execute("SET threads=2")
con2.execute("SET temp_directory='data/_duckdb_tmp'")
con2.execute("SET preserve_insertion_order=false")

con2.execute("""
    COPY (
        SELECT 'W' || least(s,t) AS paper_a, 'W' || greatest(s,t) AS paper_b
        FROM all_edges
        GROUP BY least(s,t), greatest(s,t)
        HAVING bool_or(s < t) AND bool_or(s > t)
    ) TO 'data/mutual_pairs.csv' (HEADER, DELIMITER ',')
""")
con2.close()

n = sum(1 for _ in open('data/mutual_pairs.csv')) - 1
print(f"wrote {n:,} mutual pairs to data/mutual_pairs.csv")
