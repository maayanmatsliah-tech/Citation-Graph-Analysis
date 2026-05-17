# Citation Graph Research Notes

## What We're Studying

We're examining whether mutual citations — where paper A cites paper B and paper B cites paper A — increased after ChatGPT's release in November 2022.

The idea is that before ChatGPT, finding a specific piece of information buried in an unpublished or recently published paper required reading through the whole thing. Researchers had to do extensive literature searches, track down papers that were still in progress, read them in full, and then extract the one claim or finding they actually needed. That process was slow enough that mutual citations were rare — two papers citing each other required both authors to be aware of each other's work at nearly the same time, which didn't happen often.

ChatGPT changed that. Researchers can now ask for a specific paper, find the exact page and line they need, and cite it without reading the whole thing. It also makes it easier to surface recent and in-progress work that would have previously been hard to find. If this meaningfully compressed the research discovery process, we should see it in the citation graph as an increase in mutual citations after November 2022.

## Research Question

Did mutual citations increase after ChatGPT's release at a rate that outpaces the growth in paper volume alone?

## Hypothesis

Mutual citations increased after ChatGPT's release because AI tools made it faster and easier to find and extract specific information from papers — including recently published or in-progress work. Researchers no longer need to read an entire paper to take what they need from it, which compressed the discovery process enough to create citation loops that wouldn't have existed before.

## Time Window

- **Pre-ChatGPT:** 2020–2021
- **Buffer year:** 2022 — excluded from direct comparison to account for the transition period between ChatGPT's launch in November and researchers actually incorporating it into their workflow, plus the time needed for papers to be written and published using it
- **Post-ChatGPT:** 2023–2024

## Data

- Source: OpenAlex — S3 snapshot for older papers, API for 2020–2024
- Fields stored per paper: ID, title, publication year, field
- Citation links stored: citing paper ID → cited paper ID

## What Would Confirm the Hypothesis

A statistically significant increase in mutual citation rate per 1000 papers in 2023–2024 compared to 2020–2021.

## What Would Deny It

If mutual citation rates stayed flat or grew at the same pace as overall paper volume, it would suggest ChatGPT didn't meaningfully change how researchers discover and cite recent work.

## Secondary Observation (to explore later)

If the hypothesis holds, the papers involved in post-2022 mutual citations may also be published closer together in time — suggesting researchers are citing work they discovered very recently rather than work they'd been aware of for a long time. This is not required for the hypothesis to hold but would strengthen it if found.

## Results (May 14, 2026) — superseded, see correction below

Ran research/motif_analysis.py and research/stat_test.py on the cleaned dataset.
Pre-ChatGPT (2020–2021): 19,769 mutual citation pairs across 403,920 papers — 48.94 per 1000 papers.
Post-ChatGPT (2023–2024): 14,055 mutual citation pairs across 400,290 papers — 35.11 per 1000 papers.
Chi-square statistic: 954.21, p-value: ~0.000000000 — statistically significant.

Finding: mutual citation rate decreased by 28% after ChatGPT's release.
This is the opposite of the hypothesis. The decrease is statistically significant and cannot be attributed to random variation.
Next step: investigate why.

## Bug Fix in Motif Analysis (May 15, 2026)

The numbers above were produced by buggy code. The bugs affected absolute magnitudes but not the direction of the finding. Corrected results below.

What was wrong:
1. **Self-citations counted as mutual citations.** The mutual-pair self-join `a.citing_id = b.cited_id AND a.cited_id = b.citing_id` matches any self-citation `(X → X)` against itself, so every self-cite was being counted as a "mutual pair". Self-cites per year were not evenly distributed (3,875 in 2020, 5,178 in 2022, 3,155 in 2024), so they inflated the pre-period baseline more than the post-period.
2. **Every true mutual pair was double-counted.** The symmetric self-join produces two rows per unordered pair `{X, Y}` — once via `(a=X→Y, b=Y→X)` and once via `(a=Y→X, b=X→Y)`. The reported counts were ~2× the actual number of mutual pairs.
3. **`motif_analysis.py` referenced an undefined variable** (`mutual_counts`) in its stat-test block, and imported `proportions_ztest` from `scipy.stats` where it does not exist (it lives in `statsmodels`). The script crashed before printing any stats, so the chart was produced but the in-script stat test never ran.
4. **`stat_test.py` built an incoherent contingency table.** It computed `non_mutual = papers - pairs`, subtracting pair-counts from paper-counts as if they were the same unit. The chi-square test mechanically detected that the two ratios differed, but the table had no meaningful interpretation as counts of independent events.

What was fixed:
1. Added `WHERE a.citing_id < a.cited_id` to the self-join CTE. This filter simultaneously (a) excludes self-cites, since `X < X` is false, and (b) deduplicates each unordered pair `{X, Y}` to exactly one row.
2. Removed the broken in-script stat block from `motif_analysis.py`. Statistical testing now lives only in `tests/stat_test.py`.
3. Replaced the contingency table with a paper-level Bernoulli table: per period, how many papers participated in at least one mutual pair vs. how many did not. This is well-defined — each paper is one independent trial — and is computed from a `UNION` of both sides of the deduped mutual-pair set.

## Corrected Results — Initial Pass (May 15, 2026)

Mutual pairs per year (deduplicated, self-cites excluded):
- 2020: 3,010 pairs / 202,323 papers — 14.88 per 1000
- 2021: 2,550 pairs / 201,597 papers — 12.65 per 1000
- 2022: 1,989 pairs / 200,102 papers —  9.94 per 1000
- 2023: 1,806 pairs / 200,063 papers —  9.03 per 1000
- 2024: 1,631 pairs / 200,227 papers —  8.15 per 1000

Paper-level participation (chi-square on per-paper Bernoulli outcome):
- Pre-ChatGPT  (2020–2021):  8,860 of 403,920 papers in mutual pairs — 21.94 per 1000
- Post-ChatGPT (2023–2024):  4,403 of 400,290 papers in mutual pairs — 11.00 per 1000
- Chi-square statistic: 1,481.60, p-value ≈ 0.

These numbers looked too dramatic — a ~50% drop in two years is implausibly large — so we investigated whether the baseline year (2020) was anomalous.

## 2020 Anomaly Investigation (May 15, 2026)

We compared the per-paper distribution of within-year citations across years (a year's within-year citation density is the strongest determinant of how many mutual pairs can form in that year):

| Year | Avg within-year refs/paper | Median | p95 | Max |
|------|----------------------------|--------|-----|-----|
| **2020** | **5.46** | 2 | **20** | **244** |
| 2021 | 3.19 | 2 | 10 | 139 |
| 2022 | 3.05 | 2 |  9 |  88 |
| 2023 | 3.20 | 2 | 10 | 127 |
| 2024 | 3.43 | 2 | 11 | 118 |

2020 has roughly 2× the within-year citation density of any other year — but only in the upper tail. The median is the same (2 refs/paper) across all years.

**Why this is a real anomaly, not a data error:**
1. **Ingestion paths are not split by year.** Both the API ingester (`data/api_ingest.py`) and the S3 snapshot ingester (`data/citation_parser.py`) can contribute to any year — the S3 ingester has no publication-year filter and runs on `updated_date` partitions from 2022-2025. So 2020 went through the same code paths as 2021-2024; there's no mechanism to selectively inflate 2020.
2. **Average refs OUT for 2020 is *lower* (78.64) than other years (~86).** If extra/duplicate ingestion were adding citation rows to 2020, we'd expect more refs per paper, not fewer.
3. **The median is unchanged.** A uniform ingestion-side inflation would shift the whole distribution. Instead, the anomaly is concentrated in the upper tail (p95 = 20 vs. ~10, max = 244 vs. ~120), which is consistent with a real cluster of papers citing each other heavily.
4. **Field distribution fits a COVID story.** Medicine is the #1 field in both 2020 and 2021, but the 2020 Medicine cohort is 11% larger than 2021's. The other top fields (Engineering, Bio, Environmental Science, Materials Science) are nearly identical between years.

**Likely cause:** COVID-era research clustering. In 2020, large groups of medical/epidemiological/biomedical papers were published within weeks of each other and cited each other heavily — a tight, contemporaneous co-citation cluster that doesn't exist in normal years. The heavy tail of papers with 50-244 within-year references is exactly what you'd expect from COVID review papers and rapid-response studies released in waves.

**Decision for this research:** We exclude 2020 from the pre-ChatGPT baseline. It is a real signal but a once-in-a-generation outlier — not a representative pre-ChatGPT year. Using it as the baseline would falsely make any normal year look like a "decline." The baseline is now 2021 alone; 2022 remains the transition/buffer year; 2023-2024 is the post-ChatGPT period.

## Corrected Results — Final (May 15, 2026, 2020 excluded)

Paper-level participation in mutual citations (chi-square on per-paper Bernoulli outcome):
- Pre-ChatGPT  (2021):      3,786 of 201,597 papers in mutual pairs — 18.78 per 1000
- Post-ChatGPT (2023–2024): 4,403 of 400,290 papers in mutual pairs — 10.99 per 1000
- Chi-square statistic: 604.20, p-value ≈ 0.

Finding: with 2020 removed, the drop is ~41% (down from the ~50% headline that 2020 had inflated). The direction is the same; the magnitude is smaller and more credible.

**Caveats that still need attention before claiming a ChatGPT effect:**

1. **The decline started before ChatGPT.** Per-year mutual rates: 2021 = 12.65, 2022 = 9.94, 2023 = 9.03, 2024 = 8.15 (per 1000 papers). The 21% drop from 2021 to 2022 happened *before* ChatGPT existed (launched Nov 30, 2022; 2022 papers were already written and submitted). A binary pre/post chi-square can't distinguish a step-change at ChatGPT from a pre-existing secular trend, and the data looks much more like a secular trend.
2. **p ≈ 0 is mechanical at this sample size.** With ~200k papers per year, the chi-square test would call a 0.5% absolute difference "significant." The p-value isn't evidence of a meaningful effect; the effect size and the per-year trajectory are what matter.
3. **Citation lag for 2024.** Refs IN per paper drops from 16.14 (2021) to 6.65 (2023) to 2.69 (2024) — recent papers haven't had time to accumulate citations. This may suppress the post-ChatGPT mutual count beyond any real behavior change.

Next step before claiming a ChatGPT effect: replace the binary pre/post test with a per-year trajectory (e.g., linear regression on yearly rate, or a structural break test at Nov 2022) to see whether there is an actual discontinuity at ChatGPT, or just the continuation of a pre-existing decline.

## Trajectory Analysis (May 17, 2026)

Built research/trajectory.py to fit an exponential-decay model `log(rate) = a + b·year` to the 2021-2024 yearly mutual citation rates (2020 excluded as a COVID outlier) and check whether the post-ChatGPT years fall below the pre-existing trend.

Fitted trend (2021-2024):
- Annual rate of change: **-13.2% per year**, R² = 0.944, slope p-value = 0.028.

Residuals (observed minus trend):
| Year | Observed | Trend predicts | Residual (log) | Interpretation |
|------|----------|----------------|----------------|----------------|
| 2021 | 12.65 | 12.13 | **+0.042** | above trend |
| 2022 |  9.94 | 10.53 | **-0.057** | below trend (biggest drop, pre-ChatGPT) |
| 2023 |  9.03 |  9.14 | **-0.012** | essentially on trend |
| 2024 |  8.15 |  7.93 | **+0.027** | slightly above trend |

Year-over-year decline:
- 2021 → 2022: **-21.4%** ← biggest drop, but 2022 papers were written before ChatGPT existed
- 2022 → 2023: -9.2%
- 2023 → 2024: -9.8%

Pre vs post-ChatGPT slope (log-rate):
- Pre-ChatGPT (2021 → 2022):  **-0.241** (steepest)
- Post-ChatGPT (2023 → 2024): **-0.103** (about half as steep)
- Decline is **decelerating** after ChatGPT, not accelerating.

**Interpretation.** A single exponential-decay trend fitted to 2021-2024 explains 94% of the variance in yearly mutual citation rates. The post-ChatGPT years (2023, 2024) sit essentially on that trend line — 2023 is 0.012 below it, 2024 is 0.027 above it. If ChatGPT had caused a meaningful break in citation behavior, we would expect the post-ChatGPT years to fall noticeably below the pre-existing trend. They do not. The largest single-year drop in the entire window is 2021 → 2022, which occurred entirely before ChatGPT existed (launched Nov 30, 2022; 2022 papers were written and submitted well before).

**Conclusion.** The earlier chi-square "significant drop" reflected a real pre-existing decline in mutual citation rates, not a ChatGPT effect. We cannot attribute the observed change to ChatGPT with this data. The hypothesis as originally stated — that ChatGPT compressed peer discovery and changed mutual citation behavior — is **not supported**. The previously-reported secondary finding on citation age increase needs to be re-examined the same way (with a trajectory test) before attributing it to ChatGPT.

**Caveat on statistical power.** With only 4 yearly data points (2021-2024), formal structural-break tests (Chow test, etc.) have very low power. What we can say is that the data is *consistent* with a continuous secular decline and *inconsistent* with the hypothesized step-change at ChatGPT — not that a small ChatGPT effect has been formally ruled out. Distinguishing those would require finer temporal resolution (monthly publication dates) or a longer post-ChatGPT window.

**Restated finding (one line):** Decline in mutual citation rate is real and statistically significant (−13.2%/year, p = 0.028, R² = 0.94), but ChatGPT attribution is not supported by the trajectory.

Chart: outputs/trajectory.png.

Validity Checks (May 14, 2026)
Before accepting the finding, we tested two potential sources of bias:
1. Field composition bias
Checked whether the two periods had different field distributions that could explain the rate drop. The top fields were nearly identical — Medicine, Engineering, Computer Science, Environmental Science all present in both periods at similar proportions. A modest shift (Medicine dropped from #1 to #2, Engineering rose to #1) could account for a small portion of the decrease but not a 28% drop.
2. Citation completeness bias
The pre-2022 data came from the S3 snapshot and the post-2022 data came from the OpenAlex API — two different sources. If the API had incomplete citation indexing for recent papers, mutual citation counts would be artificially low for 2023-2024. We tested this by checking average references per paper across years:

2020: 78.64 avg refs
2021: 86.65 avg refs
2022: 85.26 avg refs
2023: 85.98 avg refs
2024: 86.33 avg refs

Reference counts are consistent across all years. No evidence of incomplete indexing for recent papers.
Conclusion: Neither field composition nor data source bias appears to explain the finding. The 28% decrease in mutual citation rate appears to be real.

## Secondary Finding: Citation Age Increased After ChatGPT (May 14, 2026)
Ran research/citation_age.py and research/citation_age_test.py to test whether the average age of cited papers changed after ChatGPT.
Results:

Pre-ChatGPT (2020–2021): 1,855,318 citations, avg age 0.63 years
Post-ChatGPT (2023–2024): 7,188,198 citations, avg age 2.14 years
Mann-Whitney U statistic: 11,583,023,273,591.5, p-value: ~0.000000000

Finding: citation age increased 3.4x after ChatGPT — statistically significant.
Interpretation: After ChatGPT, researchers cite older established work rather than recent contemporaneous papers. This supports the primary finding — if citations are drifting toward older literature, two papers being written simultaneously are less likely to discover and cite each other, which explains the 28% drop in mutual citation rate.
Revised narrative: ChatGPT did not accelerate peer discovery as hypothesized. Instead, it appears to have shifted citation behavior away from real-time peer discovery toward canonical older literature — possibly because AI tools surface well-known established papers more readily than recent unpublished work.