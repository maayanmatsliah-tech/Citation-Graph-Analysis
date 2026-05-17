# Citation Graph — Consolidated Findings

This document consolidates the reliable findings from `research_notes.md` — only the results that survived bug fixes, the 2020-anomaly correction, and the trajectory / DiD / volume robustness checks. Superseded numbers, the buggy May 14 results, and the citation-age-increase interpretation (later shown to be a measurement artifact) are excluded.

For the full historical record including discarded analyses, see `research_notes.md`.

## Research Question and Hypothesis

**Question:** Did mutual citations (paper A cites paper B *and* paper B cites paper A) increase after ChatGPT's release (Nov 2022) at a rate that outpaces growth in paper volume alone?

**Hypothesis:** ChatGPT compressed peer discovery — researchers can now find and extract specific claims from recent or in-progress papers without reading them in full — which should produce citation loops that didn't exist before. If true, we should see an increase in mutual citation rate per 1000 papers in 2023–2024 vs. 2020–2021.

## Time Windows

- **Pre-ChatGPT baseline:** 2021 (2020 excluded — see "2020 Anomaly" below)
- **Buffer:** 2022 (ChatGPT launched Nov 30, 2022; papers that year were largely written/submitted pre-launch)
- **Post-ChatGPT:** 2023–2024

## Data

- Source: OpenAlex — S3 snapshot for older papers, API for 2020–2024
- Stored per paper: ID, title, publication year, field
- Stored per citation: citing paper ID → cited paper ID

## Why Mutual Citations Are the Reliable Metric

A paper's citation list is fixed at publication — authors can't add references after the fact. So for any pair of published papers, the mutual citation between them either exists or it doesn't, and waiting longer won't create new ones.

This is why mutual citation counts are trustworthy even for recent years, while raw "citations received" counts are not: a 2024 paper has had ~12 months to accumulate inbound citations, a 2021 paper has had 4+ years. Comparing 2024 to 2021 on inbound citations is unfair to 2024. Comparing them on mutual citations is fair.

## 2020 Anomaly — Why It's Excluded

The per-paper distribution of within-year citations shows 2020 is an outlier:

| Year | Avg within-year refs/paper | Median | p95 | Max |
|------|----------------------------|--------|-----|-----|
| **2020** | **5.46** | 2 | **20** | **244** |
| 2021 | 3.19 | 2 | 10 | 139 |
| 2022 | 3.05 | 2 |  9 |  88 |
| 2023 | 3.20 | 2 | 10 | 127 |
| 2024 | 3.43 | 2 | 11 | 118 |

2020 has roughly 2× the within-year citation density of any other year, but only in the upper tail. This is not a data-ingestion artifact:

1. Ingestion paths are not split by year — both ingesters can contribute to any year, and the S3 ingester has no publication-year filter.
2. Avg refs *out* for 2020 is *lower* (78.64) than other years (~86), not higher.
3. The median is unchanged across years (2 refs/paper); only the tail differs.
4. The 2020 Medicine cohort is 11% larger than 2021's; other top fields are nearly identical.

**Likely cause:** COVID-era research clustering — tight, contemporaneous co-citation among medical/epidemiological papers published in waves. Real signal, but a once-in-a-generation outlier, not a representative pre-ChatGPT year. Using it as the baseline would make any normal year look like a "decline."

## Methodology Notes (Bug Fixes That Apply To All Numbers Below)

The mutual-pair self-join in `research/motif_analysis.py` was originally `a.citing_id = b.cited_id AND a.cited_id = b.citing_id`, which (a) counted every self-cite as a mutual pair, and (b) double-counted every true mutual pair (once as (X→Y, Y→X) and once as (Y→X, X→Y)). All numbers in this document use the fixed query with `WHERE a.citing_id < a.cited_id`, which excludes self-cites and deduplicates each unordered pair to one row.

Statistical testing was also rebuilt on a paper-level Bernoulli table (per period: how many papers participated in at least one mutual pair vs. how many did not), since each paper is one independent trial. The earlier contingency table mixed paper-counts and pair-counts and had no valid interpretation.

## Per-Year Mutual Citation Rates

Deduplicated, self-cites excluded:

| Year | Mutual pairs | Papers | Pairs per 1000 papers |
|------|-------------:|-------:|----------------------:|
| 2020 | 3,010 | 202,323 | 14.88 *(COVID outlier — excluded from comparisons)* |
| 2021 | 2,550 | 201,597 | 12.65 |
| 2022 | 1,989 | 200,102 |  9.94 |
| 2023 | 1,806 | 200,063 |  9.03 |
| 2024 | 1,631 | 200,227 |  8.15 |

## Paper-Level Participation (Pre vs Post, 2020 Excluded)

Per paper: did it participate in at least one mutual pair?

- **Pre-ChatGPT (2021):** 3,786 of 201,597 papers → 18.78 per 1000
- **Post-ChatGPT (2023–2024):** 4,403 of 400,290 papers → 10.99 per 1000
- Chi-square statistic: 604.20, p-value ≈ 0

The drop is ~41%. The p-value is essentially zero, but at n ≈ 400,000 the chi-square test would also call a 0.5% absolute difference "significant" — so the p-value alone is not evidence of a meaningful effect. The effect size and per-year trajectory are what matter, and they require the trajectory test below.

## Trajectory Analysis — The Decline Is Pre-Existing

Fit an exponential-decay model `log(rate) = a + b·year` to the 2021–2024 yearly mutual citation rates (`research/trajectory.py`).

- Annual rate of change: **−13.2% per year**, R² = 0.944, slope p = 0.028.

Residuals (observed minus trend):

| Year | Observed | Trend predicts | Residual (log) |
|------|---------:|---------------:|---------------:|
| 2021 | 12.65 | 12.13 | +0.042 (above trend) |
| 2022 |  9.94 | 10.53 | −0.057 (below — biggest drop, **pre-ChatGPT**) |
| 2023 |  9.03 |  9.14 | −0.012 (on trend) |
| 2024 |  8.15 |  7.93 | +0.027 (slightly above) |

Year-over-year decline:
- 2021 → 2022: **−21.4%** ← the biggest drop, but 2022 papers were written before ChatGPT existed
- 2022 → 2023: −9.2%
- 2023 → 2024: −9.8%

Pre vs post-ChatGPT slope (log-rate):
- Pre-ChatGPT (2021 → 2022): **−0.241** (steepest)
- Post-ChatGPT (2023 → 2024): **−0.103** (about half as steep)
- The decline is **decelerating** after ChatGPT, not accelerating.

**Conclusion.** A single exponential-decay trend fitted to 2021–2024 explains 94% of the variance. Post-ChatGPT years sit on that pre-existing trend line. The earlier chi-square "significant drop" reflects a real pre-existing decline, not a ChatGPT effect. Chart: `outputs/trajectory.png`.

## Difference-in-Differences by Field Exposure

If a real ChatGPT effect exists, it should hit ChatGPT-exposed fields more than ChatGPT-unaffected fields (`research/did_analysis.py`).

**Groups:**
- HIGH exposure: Computer Science (ChatGPT *is* CS research)
- LOW exposure: Chemistry, Materials Science, Agricultural and Biological Sciences, Earth and Planetary Sciences, Immunology and Microbiology — empirical/wet-lab fields where LLMs change workflows less

**Per-year mutual citation rate (papers in mutual pairs per 1000):**

| Year | HIGH (CS) | LOW (5 fields) |
|------|----------:|---------------:|
| 2021 | 32.59 | 10.93 |
| 2022 | 29.98 |  7.32 |
| 2023 | 31.28 |  6.21 |
| 2024 | 19.37 |  3.58 |

**Pre/post DiD:**
- HIGH change (2021–22 → 2023–24): 31.25 → 25.33 per 1000 = **−18.9%**
- LOW  change (2021–22 → 2023–24):  9.09 →  4.86 per 1000 = **−46.5%**
- DiD (log-rate): **+0.416**, SE 0.083, z = +5.02, p < 0.0001

**Direction:** HIGH fell *less* than LOW — the opposite of "ChatGPT-exposed fields show the predicted increase." CS mutual citation rates went **down**, not up, post-ChatGPT. The hypothesis specifically predicted an *increase* in mutual citations from compressed peer discovery — directly falsified at the field level.

**Caveat — pre-trends are not parallel.** From 2021 to 2022 (both pre-ChatGPT), HIGH fell 8% while LOW fell 33%, so the post-period gap is partly continuation of pre-existing field-specific dynamics, not a ChatGPT-induced divergence. With non-parallel pre-trends, the DiD point estimate doesn't cleanly identify a causal effect. What it does establish is that the *direction* predicted by the hypothesis is wrong in the most-exposed field.

## Volume Check — Paper Counts Are Flat

Question: do recent years just have more papers (with more low-quality ones), mechanically deflating per-paper rates? (`research/did_volume_check.py`)

| Period | Papers | Avg citations per paper | Avg mutual citations per paper |
|--------|-------:|------------------------:|-------------------------------:|
| Pre  (2021–2022) | 401,699 | 13.17  | 0.0215 |
| Post (2023–2024) | 400,290 |  3.64  | 0.0157 |
| Change | −0.4% | −72.3% | −27.1% |

Per-year:

| Year | Papers | Total citations received | Avg cit/paper | Mutual pair memberships | Avg mut/paper |
|------|-------:|-------------------------:|--------------:|------------------------:|--------------:|
| 2021 | 201,597 | 3,158,708 | 15.67 | 4,865 | 0.0241 |
| 2022 | 200,102 | 2,129,913 | 10.64 | 3,764 | 0.0188 |
| 2023 | 200,063 | 1,197,181 |  5.98 | 3,504 | 0.0175 |
| 2024 | 200,227 |   261,263 |  1.31 | 2,767 | 0.0138 |

- Paper counts are **basically flat (−0.4%)**. No paper-volume explosion to explain the rate drop.
- The 72% drop in overall citations per paper is a citation-lag clock issue (2024 papers have had ~12 months; 2021 papers have had 4+ years). Steepest at the most recent year, fits lag exactly. Affects all fields roughly equally (CS −69%, the 5 empirical fields −74%), so it does not explain the CS-vs-empirical gap.
- Mutual citations drop only 27%, not 72%, because mutual pairs aren't dragged down by years of accumulation — both papers' citation lists are fixed at publication.
- The field-level DiD result **survives**: volume and citability moved the same way across fields, so the gap between CS (−19%) and the empirical fields (−47%) is not explained by differential paper volume or paper quality.

## Citation Age — The Metric Was an Artifact

The previously reported "3.4× increase in citation age after ChatGPT" does not hold up under inspection (`research/citation_age.py`).

**Per-year avg cited age** (citing 2020–2024, cited 1950–2024):

| Citing year | Avg cited age (years) |
|-------------|----------------------:|
| 2020 | 0.09 |
| 2021 | 0.83 |
| 2022 | 1.39 |
| 2023 | 1.89 |
| 2024 | 2.33 |

The trajectory fit (2021–2024, 2020 excluded) is nearly perfect: slope +0.497 years per year, R² = 0.997, slope p = 0.0014, all residuals under 0.04 years. No break at ChatGPT — same shape as the mutual-citation trajectory.

**But the metric itself is structurally biased.** For every citing year, 99.5–100% of matched citations land on papers in the dense 2020–2024 region of the works table (the S3 snapshot's pre-2020 coverage is too sparse for most pre-2020 citations to find a JOIN match). So "avg cited age" effectively measures *how many years of the dense 2020–2024 region are reachable backward from the citing year*:

- 2020 can match only year 2020 → max possible age 0 → avg 0.09
- 2021 can match 2020–2021 → avg 0.83
- 2022 can match 2020–2022 → avg 1.39
- 2023 can match 2020–2023 → avg 1.89
- 2024 can match 2020–2024 → avg 2.33

This is the exact shape we observe, and it would emerge from any citation behavior — even one in which every paper cites uniformly across all available years. The metric is mechanically constrained by the dense-region width.

**Conclusion.** The "citation age increase" is primarily a measurement artifact of the works table's year-coverage profile, not a behavior change. The previous interpretation ("researchers citing older established work instead of recent peers") cannot be supported from this data.

## Final Verdict on the Hypothesis

**Original hypothesis:** mutual citations increased after ChatGPT because AI tools compressed peer discovery, creating citation loops that wouldn't have existed before.

**Verdict: rejected by this data, with reasonable confidence.** Three independent lines of evidence:

1. **Aggregate trajectory** (`research/trajectory.py`): 2021–2024 mutual rate follows a smooth exponential decline (R² = 0.94). Post-ChatGPT years sit on the pre-existing trend line. No step-change at Nov 2022.
2. **DiD by field exposure** (`research/did_analysis.py`): CS mutual rates *fell* post-ChatGPT (−18.9%), not rose. The most ChatGPT-exposed field did not show the predicted upward divergence.
3. **Volume check** (`research/did_volume_check.py`): paper counts are flat (−0.4%); the field-level pattern is not explained by differential volume or by citation-lag effects.

## What This Does and Doesn't Tell Us

- **Found:** a real secular decline in mutual citation rates (−13.2%/year, R² = 0.94) that started **before** ChatGPT.
- **Found:** the apparent citation-age increase is mostly a measurement artifact of the works table's year coverage, not a behavior signal.
- **Ruled out:** that ChatGPT caused a discrete, yearly-resolution step-change in mutual citation rate or in citation age. Both post-ChatGPT years sit on the pre-existing trend line, and the most-exposed field moved opposite to the hypothesized direction.
- **Did NOT rule out:** a small ChatGPT effect riding on top of the larger trend (4 yearly data points isn't enough power for that); sub-annual effects; effects on dimensions we didn't measure (citation novelty, cross-field reach, semantic similarity); long-run effects that haven't manifested yet (~1.5 years of post-ChatGPT papers).
- **Bottom line:** the *specific* hypothesis ("ChatGPT caused mutual citations to increase via compressed peer discovery") is not supported. The *broader* question ("did ChatGPT change citation behavior at all") is untestable with this dataset.

**Methodological lesson:** at n ≈ 400,000, binary pre/post chi-square gives p ≈ 0 on any pre-existing trend — which is easy to mistake for a causal effect. The trajectory test (per-year trend + residuals + pre/post slope comparison), combined with cross-field DiD, is what distinguished "real signal at the right time" from "real signal that predates the cause."
