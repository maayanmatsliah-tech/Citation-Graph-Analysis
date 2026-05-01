# Citation Graph Analysis

Citation data from 7.7 million academic papers (OpenAlex), stored locally and analyzed to investigate what structural patterns in early citation behavior predict how long a paper stays relevant.

## Research Question

Among papers published 1960–1989, do papers that outlive the average citation lifespan for their decade share a pattern in how they were cited in their first 10 years?

## Data

Source: [OpenAlex S3 snapshot](https://developers.openalex.org/download/snapshot-format) — public, no account needed.

Run `citation_parser.py` to stream and store the data locally. Requires `boto3` and `duckdb`.

```bash
pip install boto3 duckdb matplotlib
python3 citation_parser.py
```

## Structure

```
citation-graph-analysis/
├── citation_parser.py        # streams from S3, saves to DuckDB
├── data/                     # local database (not committed)
├── research/                 # analysis scripts for current hypothesis
├── exploration/              # earlier exploratory scripts
└── outputs/                  # saved charts
```