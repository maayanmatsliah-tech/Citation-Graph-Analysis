import gzip
import json
import duckdb
import boto3
from botocore import UNSIGNED
from botocore.config import Config

con = duckdb.connect("citations.duckdb")
con.execute("CREATE TABLE IF NOT EXISTS works (id TEXT, title TEXT, year INT)")
con.execute("CREATE TABLE IF NOT EXISTS citations (citing_id TEXT, cited_id TEXT)")

s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))

# grab 20 folders to start
folders = [
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
    "data/works/updated_date=2025-08-27/",
    "data/works/updated_date=2025-08-28/",
    "data/works/updated_date=2025-08-29/",
    "data/works/updated_date=2025-09-03/",
    "data/works/updated_date=2025-09-08/",
    "data/works/updated_date=2025-09-09/",
    "data/works/updated_date=2025-09-23/",
    "data/works/updated_date=2025-09-24/",
    "data/works/updated_date=2025-09-25/",
    "data/works/updated_date=2025-09-26/",
    "data/works/updated_date=2025-09-27/",
    "data/works/updated_date=2025-09-28/",
    "data/works/updated_date=2025-09-29/",
    "data/works/updated_date=2025-09-30/",
    "data/works/updated_date=2025-10-01/",
    "data/works/updated_date=2025-10-02/",
    "data/works/updated_date=2025-10-03/",
    "data/works/updated_date=2025-10-04/",
    "data/works/updated_date=2025-10-05/",
    "data/works/updated_date=2025-10-06/",
    "data/works/updated_date=2025-10-07/",
    "data/works/updated_date=2025-10-08/",
    "data/works/updated_date=2025-10-09/",
    "data/works/updated_date=2025-10-10/",
    "data/works/updated_date=2025-10-11/",
    "data/works/updated_date=2025-10-12/",
    "data/works/updated_date=2025-10-13/",
    "data/works/updated_date=2025-10-14/",
    "data/works/updated_date=2025-10-15/",
    "data/works/updated_date=2025-10-16/",
    "data/works/updated_date=2025-10-17/",
    "data/works/updated_date=2025-10-18/",
    "data/works/updated_date=2025-10-19/",
    "data/works/updated_date=2025-10-20/",
    "data/works/updated_date=2025-10-21/",
    "data/works/updated_date=2025-10-22/",
    "data/works/updated_date=2025-10-23/",
    "data/works/updated_date=2025-10-24/",
    "data/works/updated_date=2025-10-25/",
    "data/works/updated_date=2025-10-26/",
    "data/works/updated_date=2025-10-27/",
    "data/works/updated_date=2025-10-28/",
    "data/works/updated_date=2025-10-29/",
    "data/works/updated_date=2025-10-30/",
    "data/works/updated_date=2025-10-31/",
    "data/works/updated_date=2025-11-01/",
    "data/works/updated_date=2025-11-02/",
    "data/works/updated_date=2025-11-03/",
    "data/works/updated_date=2025-11-04/",
    "data/works/updated_date=2025-11-05/",
    "data/works/updated_date=2025-11-06/",
    "data/works/updated_date=2025-11-07/",
    "data/works/updated_date=2025-11-08/",
    "data/works/updated_date=2025-11-09/",
    "data/works/updated_date=2025-11-10/",
    "data/works/updated_date=2025-11-11/",
    "data/works/updated_date=2025-11-12/",
    "data/works/updated_date=2025-11-13/",
    "data/works/updated_date=2025-11-14/",
    "data/works/updated_date=2025-11-15/",
    "data/works/updated_date=2025-11-16/",
    "data/works/updated_date=2025-11-17/",
    "data/works/updated_date=2025-11-18/",
    "data/works/updated_date=2025-11-19/",
    "data/works/updated_date=2025-11-20/",
    "data/works/updated_date=2025-11-23/",
    "data/works/updated_date=2025-11-25/",
    "data/works/updated_date=2025-11-27/",
    "data/works/updated_date=2025-11-28/",
    "data/works/updated_date=2025-11-29/",
    "data/works/updated_date=2025-11-30/",
    "data/works/updated_date=2025-12-01/",
    "data/works/updated_date=2025-12-02/",
    "data/works/updated_date=2025-12-03/",
    "data/works/updated_date=2025-12-04/",
    "data/works/updated_date=2025-12-05/",
    "data/works/updated_date=2025-12-06/",
    "data/works/updated_date=2025-12-07/",
    "data/works/updated_date=2025-12-08/",
    "data/works/updated_date=2025-12-09/",
    "data/works/updated_date=2025-12-10/",
    "data/works/updated_date=2025-12-11/",
    "data/works/updated_date=2025-12-12/",
    "data/works/updated_date=2025-12-13/",
    "data/works/updated_date=2025-12-14/",
    "data/works/updated_date=2025-12-15/",
    "data/works/updated_date=2025-12-16/",
    "data/works/updated_date=2025-12-17/",
    "data/works/updated_date=2025-12-18/",
    "data/works/updated_date=2025-12-19/",
    "data/works/updated_date=2025-12-20/",
    "data/works/updated_date=2025-12-21/",
    "data/works/updated_date=2025-12-22/",
    "data/works/updated_date=2025-12-23/",
    "data/works/updated_date=2025-12-24/",
    "data/works/updated_date=2025-12-25/",
    "data/works/updated_date=2025-12-26/",
    "data/works/updated_date=2025-12-27/",
    "data/works/updated_date=2025-12-28/",
    "data/works/updated_date=2025-12-29/",
    "data/works/updated_date=2025-12-30/",
    "data/works/updated_date=2025-12-31/",
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

                con.execute("INSERT INTO works VALUES (?, ?, ?)", [work_id, title, year])
                for ref in refs:
                    con.execute("INSERT INTO citations VALUES (?, ?)", [work_id, ref])

                total_kept += 1
                if total_kept % 10000 == 0:
                    print(f"  kept {total_kept} papers so far...")

print(f"done! kept {total_kept} papers, skipped {total_skipped}.")