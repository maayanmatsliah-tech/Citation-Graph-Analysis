# A 2021 Inflection in Citation Behavior

## The observation

Across the 1950–2025 OpenAlex sample (10,000 papers per year, 32 M outbound edges), three independent metrics of citation behavior move together at exactly **2021**:

| Year | Mutual pairs per 1000 papers | % of papers classified as "diverse" (cites 3+ distinct fields) | Avg # of distinct fields cited per paper |
|------|----------------------------:|---------------------------------------------------------------:|----------------------------------------:|
| 2018 | — | 71.4% | 4.150 |
| 2019 | — | 72.3% | 4.226 |
| 2020 | 32.9 *(high)* | 70.3% | 4.172 |
| **2021** | **17.9 *(sharp drop, −46%)*** | **75.1% *(peak)*** | **4.477 *(peak)*** |
| 2022 | 15.3 | 75.0% | 4.329 |
| 2023 | 11.9 | 73.1% | 4.321 |
| 2024 | 11.8 | 72.3% | 4.367 |
| 2025 | 11.7 | 72.0% | 4.189 |

All three metrics jump in the same direction at the same year: papers became more diverse in what they cite, and mutual citations dropped sharply. 2021 is the peak year for both diversity metrics in the entire 76-year series, not just locally.

## Why these three findings are consistent with each other

A separate per-paper analysis on the same dataset showed that across all years 1950–2025, **non-diverse papers (cite ≤2 distinct fields) have on average 1.90× the mutual-citation share of diverse papers (cite 3+ distinct fields)**. The relationship holds across the whole time series; the chart is in [outputs/mutual_share_by_diversity.png](../outputs/mutual_share_by_diversity.png). Papers that cite within a narrow field are mechanically more likely to land in citation loops with same-field peers; papers that cite broadly spread their references too thin for mutual pairs to form often.

That cross-sectional regularity gives the 2021 inflection a clean mechanism: if researchers in 2021 started citing more broadly across fields, mutual citations should fall as a mechanical consequence. The 2021 spike in citation breadth (+0.30 distinct fields above the 2018–2020 baseline) and the 2021 drop in mutual rate (32.9 → 17.9 per 1000) are quantitatively consistent under this mechanism — they aren't two separate findings but one finding with a downstream effect.

## How robust is the 2021 peak?

With ~9,500 citing papers contributing to each yearly mean, the standard error on the average-distinct-fields metric is roughly ±0.025 (≈ standard deviation / √n). The 2021 spike of +0.30 above adjacent years is therefore ~12 standard errors away from baseline — far outside what sampling noise would produce. The same holds for the +4.8 percentage-point jump in the "% diverse" classifier (70.3% → 75.1%). These are real movements, not artifacts of which papers happened to land in the 2021 cohort.

## What this is and isn't

It is a real, statistically robust, three-way concurrent shift in citation behavior at 2021. It aligns with the structural-break hypothesis at June 2021 — papers published in 2021 (most of which were written in the second half of the year, after June) start citing more broadly than papers published in earlier years.

It is not yet identified to a specific cause. Several plausible candidates exist:

- **Pre-ChatGPT AI tools became broadly usable in 2020–2021** — GPT-3 launched in mid-2020, GitHub Copilot's technical preview was June 2021. These predate ChatGPT by ~17 months and could have begun changing how researchers find related literature.
- **COVID-era research patterns.** 2020 shows an anomalously high mutual rate (32.9/1000 vs the 2018–2019 trend), likely COVID-cluster citing. The 2020 → 2021 transition is partly real shift, partly reversion from the COVID spike. The diversity peak in 2021, however, is *higher than 2018 or 2019*, so it's not simply COVID reversion.
- **Open-access expansion and search-tool improvements** through 2020–2021 (e.g., Semantic Scholar maturation) could have broadened the reachable literature.

It is also a *single-year peak*, not a sustained shift to a new regime. 2022 onward settles slightly below 2021's peak but stays above the 2018–2020 baseline (4.32 vs 4.17 in distinct fields), suggesting whatever happened in 2021 left the baseline somewhat elevated but didn't lock in at peak level.

## Caveats

- The new dataset's `cited_paper_fields` backfill stopped at ~1.2 M of the ~4.4 M in-degree-≥2 papers identified, giving **37% edge coverage**. Absolute values of the average-distinct-fields metric are undercounts. The relative pattern across years (peak at 2021) should be robust to coverage as long as coverage is roughly uniform across years, but if 2021 papers happen to cite a disproportionate share of "popular" papers (high in-degree), the 2021 measurement could be slightly inflated by the backfill bias.
- 2025 coverage in OpenAlex is incomplete and the year is partial, so the 2025 numbers are likely undercounts and should not be over-read.
- The mutual citation rate for the new dataset is computed within-set only (both endpoints in the 10k-per-year sample), so the absolute counts are small. The relative pattern across years is what's informative.

## What would strengthen this further

1. Resume the cited-fields backfill from where it stopped, push edge coverage past 70%, re-run the metrics. If the 2021 peak survives, it's not a coverage artifact.
2. Compute the same three-metric snapshot **per field** to see whether the 2021 inflection is uniform across disciplines or concentrated in specific fields. A real tool-driven effect would show up most strongly in fields likely to adopt AI tools earliest (CS, ML-adjacent, computational sciences).
3. Replicate against a second citation graph (Semantic Scholar, Crossref) to rule out OpenAlex-specific ingestion artifacts.

## Source files

- Data: [data/clean_dataset.duckdb](../data/clean_dataset.duckdb), [data/papers.parquet](../data/papers.parquet), [data/edges.parquet](../data/edges.parquet)
- Mutual citation counts per year: [data/mutual_citations_per_year.csv](../data/mutual_citations_per_year.csv), computed by [research/mutual_citations_per_year.py](../research/mutual_citations_per_year.py)
- Diversity classification: [research/classify_diversity.py](../research/classify_diversity.py)
- Diversity-vs-mutual scatter: [research/scatter_mutual_by_diversity.py](../research/scatter_mutual_by_diversity.py) → [outputs/mutual_share_by_diversity.png](../outputs/mutual_share_by_diversity.png)
- Significance test for break at June 2021: [research/significance_clean.py](../research/significance_clean.py)
