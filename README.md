# Citation Graph Explorer

A Python project for downloading, storing, and analyzing academic citation data from [OpenAlex](https://openalex.org/) — one of the largest open bibliographic datasets in the world.

## What This Project Does

Academic papers cite other papers. Those citations form a **graph** — a massive web of connections between ideas, authors, and fields. This project pulls that data down, stores it efficiently, and lets you run analyses to find patterns and form hypotheses.

Examples of questions you can ask:
- What are the most cited papers of all time?
- Which authors are most influential in a given field?
- Are there clusters of papers that cite each other heavily?

## Data Source

All data comes from the [OpenAlex S3 snapshot](https://developers.openalex.org/download/snapshot-format) — a public, free dataset of 250M+ academic works, no account required.

From each paper, we extract only what we need:
- Paper ID and title
- Authors
- List of papers it cited

This keeps storage to ~10–20 GB instead of the full 1.6 TB snapshot.

## Tech Stack

- **Python** — main scripting language
- **AWS CLI** — streams data from S3 without saving raw files to disk
- **DuckDB** — stores and queries the citation data locally

## Project Structure

```
citation-graph-explorer/
├── README.md
├── ingest.py        # streams data from S3 and saves to DuckDB
├── analyze.py       # queries the database and runs analysis
└── citations.duckdb # the local database file (generated, not committed)
```

## Setup

**1. Install dependencies**
```bash
pip install duckdb
```

**2. Install the AWS CLI**

Follow the instructions at https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html

No AWS account needed — the OpenAlex bucket is public.

**3. Run the ingestion script**
```bash
python ingest.py
```

This streams Works data from OpenAlex, extracts titles, authors, and citations, and saves them to `citations.duckdb`.

**4. Run analysis**
```bash
python analyze.py
```

## Status

Work in progress. Currently building out the ingestion pipeline.

## Author

Rising sophomore CS student exploring large-scale graph analysis on open academic data.