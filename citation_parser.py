import gzip, json, sqlite3
import subprocess
import duckdb

# 1. open the database (creates the file if it doesn't exist)
con = duckdb.connect("citations.duckdb")

# 2. create your tables once
con.execute("""
    CREATE TABLE IF NOT EXISTS works (id TEXT, title TEXT);
    CREATE TABLE IF NOT EXISTS citations (citing_id TEXT, cited_id TEXT);
""")

# 3. stream from S3 and save as you go
proc = subprocess.Popen(
    ["aws", "s3", "cp", "s3://openalex/data/works/.../0000_part_00.gz", "-", "--no-sign-request"],
    stdout=subprocess.PIPE
)

with gzip.open(proc.stdout, 'rb') as f:
    for line in f:
        work = json.loads(line)
        
        work_id = work["id"]
        title = work.get("title", "")
        refs = work.get("referenced_works", [])

        # 4. save to database
        con.execute("INSERT INTO works VALUES (?, ?)", [work_id, title])
        
        for ref in refs:
            con.execute("INSERT INTO citations VALUES (?, ?)", [work_id, ref])