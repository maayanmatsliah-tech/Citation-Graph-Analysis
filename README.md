# Citation Graph Analysis

Citation data from millions of academic papers (OpenAlex), stored locally and analyzed to investigate whether mutual citations — where two papers cite each other — increased after ChatGPT's release in November 2022.

## Research Question

Did mutual citations increase after ChatGPT's release at a rate that outpaces the growth in paper volume alone — and if so, does this reflect AI tools compressing the research discovery process?

## Hypothesis

Mutual citations increased after ChatGPT because researchers can now find and extract specific information from papers instantly, without reading them in full. This compressed the discovery process enough to create citation loops that wouldn't have existed before.

## Data

Source: [OpenAlex](https://openalex.org/) — S3 snapshot for older papers, API for 2020–2024. Public, no account needed.

```bash
pip install boto3 duckdb matplotlib requests
python3 citation_parser.py   # streams from S3
python3 api_ingest.py        # pulls 2020-2024 from API
```

## Structure

```
citation-graph-analysis/
├── citation_parser.py        # ingestion from S3 snapshot
├── api_ingest.py             # ingestion from OpenAlex API
├── data/                     # local database (not committed)
├── research/                 # analysis scripts for current hypothesis
├── exploration/              # earlier exploratory scripts
├── docs/                     # research notes and hypothesis documents
└── outputs/                  # saved charts
```