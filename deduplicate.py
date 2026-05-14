import duckdb

con = duckdb.connect("data/citations.duckdb")

print("Checking for duplicates...")

works_total = con.execute("SELECT COUNT(*) FROM works").fetchone()[0]
works_unique = con.execute("SELECT COUNT(DISTINCT id) FROM works").fetchone()[0]
citations_total = con.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
citations_unique = con.execute("SELECT COUNT(DISTINCT (citing_id, cited_id)) FROM citations").fetchone()[0]

print(f"Works — total: {works_total:,}, unique: {works_unique:,}, duplicates: {works_total - works_unique:,}")
print(f"Citations — total: {citations_total:,}, unique: {citations_unique:,}, duplicates: {citations_total - citations_unique:,}")

if works_total == works_unique and citations_total == citations_unique:
    print("\nNo duplicates found. Nothing to do.")
else:
    print("\nRemoving duplicates...")

    con.execute("""
        CREATE TABLE works_clean AS
        SELECT DISTINCT ON (id) id, title, year, field
        FROM works
    """)

    con.execute("""
        CREATE TABLE citations_clean AS
        SELECT DISTINCT citing_id, cited_id
        FROM citations
    """)

    con.execute("DROP TABLE works")
    con.execute("DROP TABLE citations")
    con.execute("ALTER TABLE works_clean RENAME TO works")
    con.execute("ALTER TABLE citations_clean RENAME TO citations")

    works_final = con.execute("SELECT COUNT(*) FROM works").fetchone()[0]
    citations_final = con.execute("SELECT COUNT(*) FROM citations").fetchone()[0]

    print(f"\nDone.")
    print(f"Works: {works_total:,} → {works_final:,}")
    print(f"Citations: {citations_total:,} → {citations_final:,}")
    