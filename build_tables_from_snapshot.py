"""
Build attributes + edges tables directly from the OpenAlex data snapshot.

The OpenAlex snapshot is the full works corpus as gzipped JSON-Lines on the public
S3 bucket `s3://openalex` (no credentials needed). We stream it line by line and
never store the snapshot itself. This avoids the API entirely (and its rate limits).

Per work published in [START_YEAR, END_YEAR] we emit:
  attributes: id, year, field, author
      id     -> OpenAlex short id with the URL prefix stripped (e.g. W123)
      year   -> publication_year
      field  -> primary topic's field display name (topics[0].field.display_name)
      author -> authorships[].author.display_name, joined with "; "
  edges: source, target
      one row per referenced_work (source = this paper, target = cited paper)

Sample mode (default): stop after SAMPLE_N attribute rows so you can eyeball the
columns before committing to a full run. Set SAMPLE_N=0 for no limit.

Env:
  SAMPLE_N    stop after this many attribute rows (default 100; 0 = unlimited)
  START_YEAR  default 1975
  END_YEAR    default 2025
  ATTR_OUT    default data/sample_attributes.csv
  EDGES_OUT   default data/sample_edges.csv

Usage:  ./venv/bin/python build_tables_from_snapshot.py
"""

import csv
import gzip
import json
import os
import sys

import boto3
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = "openalex"
WORKS_PREFIX = "data/works/"

SAMPLE_N = int(os.environ.get("SAMPLE_N", "100"))
START_YEAR = int(os.environ.get("START_YEAR", "1975"))
END_YEAR = int(os.environ.get("END_YEAR", "2025"))
ATTR_OUT = os.environ.get("ATTR_OUT", "data/sample_attributes.csv")
EDGES_OUT = os.environ.get("EDGES_OUT", "data/sample_edges.csv")


def strip_prefix(oa_id: str) -> str:
    """'https://openalex.org/W123' -> 'W123'."""
    return oa_id.rsplit("/", 1)[-1]


def extract(work):
    """Return (attr_row, edge_rows) for one work, or None if it should be skipped."""
    year = work.get("publication_year")
    if year is None or year < START_YEAR or year > END_YEAR:
        return None
    wid = work.get("id")
    if not wid:
        return None
    wid = strip_prefix(wid)

    topics = work.get("topics") or []
    field = "Unknown"
    if topics and isinstance(topics[0], dict):
        field = (topics[0].get("field") or {}).get("display_name", "Unknown")

    authors = "; ".join(
        a["author"]["display_name"]
        for a in (work.get("authorships") or [])
        if a.get("author", {}).get("display_name")
    )

    attr_row = (wid, year, field, authors)
    edge_rows = [
        (wid, strip_prefix(ref)) for ref in (work.get("referenced_works") or [])
    ]
    return attr_row, edge_rows


MAX_FOLDERS = int(os.environ.get("MAX_FOLDERS", "100000"))  # effectively all


def list_part_files(s3, limit_folders=MAX_FOLDERS):
    """Yield .gz part-file keys across the works partitions (folder by folder).
    SAMPLE_N in the caller stops early; for a full run this walks everything."""
    folders = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=WORKS_PREFIX, Delimiter="/"):
        for cp in page.get("CommonPrefixes", []):
            folders.append(cp["Prefix"])
            if len(folders) >= limit_folders:
                break
        if len(folders) >= limit_folders:
            break
    for folder in folders:
        for page in paginator.paginate(Bucket=BUCKET, Prefix=folder):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".gz"):
                    yield obj["Key"]


def main():
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))

    n_attr = 0
    n_edge = 0
    with open(ATTR_OUT, "w", newline="", encoding="utf-8") as af, \
         open(EDGES_OUT, "w", newline="", encoding="utf-8") as ef:
        aw = csv.writer(af)
        ew = csv.writer(ef)
        aw.writerow(["id", "year", "field", "author"])
        ew.writerow(["source", "target"])

        for key in list_part_files(s3):
            print(f"streaming s3://{BUCKET}/{key}", file=sys.stderr)
            body = s3.get_object(Bucket=BUCKET, Key=key)["Body"]
            with gzip.open(body, "rb") as f:
                for line in f:
                    work = json.loads(line)
                    got = extract(work)
                    if not got:
                        continue
                    attr_row, edge_rows = got
                    aw.writerow(attr_row)
                    ew.writerows(edge_rows)
                    n_attr += 1
                    n_edge += len(edge_rows)
                    if SAMPLE_N and n_attr >= SAMPLE_N:
                        print(f"reached SAMPLE_N={SAMPLE_N}", file=sys.stderr)
                        print(f"wrote {n_attr} attribute rows, {n_edge} edge rows")
                        return
    print(f"wrote {n_attr} attribute rows, {n_edge} edge rows")


if __name__ == "__main__":
    main()
