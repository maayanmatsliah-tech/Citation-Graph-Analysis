import gzip
import json
import duckdb
import boto3
from botocore import UNSIGNED
from botocore.config import Config

con = duckdb.connect("data/citations.duckdb")
con.execute("CREATE TABLE IF NOT EXISTS works (id TEXT, title TEXT, year INT, field TEXT)")
con.execute("CREATE TABLE IF NOT EXISTS citations (citing_id TEXT, cited_id TEXT)")

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))

folders = [
    "data/works/updated_date=2022-10-20/",
    "data/works/updated_date=2022-11-02/",
    "data/works/updated_date=2023-12-11/",
    "data/works/updated_date=2024-07-19/",
    "data/works/updated_date=2024-08-27/",
    "data/works/updated_date=2024-11-08/",
    "data/works/updated_date=2025-07-15/",
    "data/works/updated_date=2025-07-16/",
    "data/works/updated_date=2025-07-22/",
    "data/works/updated_date=2025-07-23/",
    "data/works/updated_date=2025-07-24/",
    "data/works/updated_date=2025-07-25/",
    "data/works/updated_date=2025-07-26/",
    "data/works/updated_date=2025-07-27/",
    "data/works/updated_date=2025-07-28/",
    "data/works/updated_date=2025-07-29/",
    "data/works/updated_date=2025-07-30/",
    "data/works/updated_date=2025-07-31/",
    "data/works/updated_date=2025-08-04/",
    "data/works/updated_date=2025-08-18/",
]

total_kept = 0
total_skipped = 0

for folder in folders:
    # list files inside each folder
    result = s3.list_objects_v2(Bucket="openalex", Prefix=folder)
    files = [obj["Key"] for obj in result.get("Contents", [])]

    for key in files:
        print(f"processing {key}...")
        response = s3.get_object(Bucket="openalex", Key=key)

        with gzip.open(response["Body"], 'rb') as f:
            for line in f:
                work = json.loads(line)
                year = work.get("publication_year")

                if year is None or year < 1925 or year > 2025:
                    total_skipped += 1
                    continue

                work_id = work["id"]
                title = work.get("title", "")
                refs = work.get("referenced_works", [])

                topics = work.get("topics", [])
                field = topics[0]["field"]["display_name"] if topics and "field" in topics[0] else "Unknown"

                con.execute("INSERT INTO works VALUES (?, ?, ?, ?)", [work_id, title, year, field])
                for ref in refs:
                    con.execute("INSERT INTO citations VALUES (?, ?)", [work_id, ref])

                total_kept += 1
                if total_kept % 10000 == 0:
                    print(f"  kept {total_kept} papers so far...")

print(f"done! kept {total_kept} papers, skipped {total_skipped}.")