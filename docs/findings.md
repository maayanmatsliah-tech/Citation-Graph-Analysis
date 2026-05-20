# Citation Graph — Consolidated Findings

This document is the paper-ready summary of the project. It contains only the results that survived bug fixes, the 2020-anomaly correction, the trajectory test, the field-level DiD, the volume/quality check, the year-gap stratification, and the forward-citation validity check. Superseded numbers, the buggy May 14 results, and the "citation age increase" interpretation (later shown to be a measurement artifact) are excluded. For the full historical record including discarded analyses, see [research_notes.md](research_notes.md).

## Research Question and Hypothesis

**Question.** Did mutual citations (paper A cites paper B *and* paper B cites paper A) increase after ChatGPT's release (Nov 30, 2022) at a rate that outpaces growth in paper volume alone?

**Hypothesis.** ChatGPT compressed peer discovery — researchers can now find and extract specific claims from recent or in-progress papers without reading them in full — which should produce citation loops that didn't exist before. If true, we should see an increase in mutual citation rate per 1000 papers in 2023–2024 vs. 2020–2021.

## Time Windows

- **Pre-ChatGPT baseline:** 2021 (2020 excluded — see "2020 Anomaly" below).
- **Buffer:** 2022 — ChatGPT launched Nov 30, 2022; papers that year were largely written/submitted pre-launch.
- **Post-ChatGPT:** 2023–2024.

## Data

- Source: OpenAlex — S3 snapshot ([data/citation_parser.py](../data/citation_parser.py)) for older papers, API ([data/api_ingest.py](../data/api_ingest.py)) for 2020–2024. Both ingesters write to the same `works` and `citations` tables in [data/citations.duckdb](../data/citations.duckdb); neither path is split by publication year.
- Stored per paper (`works`): `id`, `title`, `year`, `field`. As of May 18, [data/backfill_dates.py](../data/backfill_dates.py) added `publication_date` (DATE) and `type` (TEXT) to the ~16k papers participating in mutual pairs (100% coverage 2020–2024).
- Stored per citation (`citations`): `citing_id` → `cited_id`.
- Deduplication done by [data/deduplicate.py](../data/deduplicate.py).
- ~200k papers/year for each of 2020–2024 (basically flat: −0.4% pre vs. post).
- Pre-2020 coverage is sparse — most pre-2020 cited papers fail to JOIN.

## Why Mutual Citations Are the Reliable Metric

A paper's citation list is fixed at publication — authors can't add references after the fact. So for any pair of published papers, the mutual citation between them either exists or it doesn't, and waiting longer won't create new ones.

This is why mutual citation counts are trustworthy even for recent years, while raw "citations received" counts are not. A 2024 paper has had ~12 months to accumulate inbound citations; a 2021 paper has had 4+ years. Comparing them on inbound citations is unfair to 2024; comparing them on mutual citations is fair.

## Methodology Note — Bug Fixes That Apply To All Numbers

The original mutual-pair self-join in [research/motif_analysis.py](../research/motif_analysis.py) was `a.citing_id = b.cited_id AND a.cited_id = b.citing_id` with no further filter. This (a) counted every self-cite as a mutual pair, since the join matches any `(X → X)` against itself, and (b) double-counted every true mutual pair (once as `(X→Y, Y→X)` and once as `(Y→X, X→Y)`).

All numbers in this document use the fixed query with `WHERE a.citing_id < a.cited_id`, which simultaneously excludes self-cites and deduplicates each unordered pair to one row.

Statistical testing was also rebuilt on a paper-level Bernoulli table in [tests/stat_test.py](../tests/stat_test.py) — per period, how many papers participated in at least one mutual pair vs. how many did not. The earlier contingency table mixed paper-counts and pair-counts and had no valid interpretation.

## 2020 Anomaly — Why It's Excluded

The per-paper distribution of within-year citations shows 2020 is an outlier:

| Year | Avg within-year refs/paper | Median | p95 | Max |
|------|---------------------------:|-------:|----:|----:|
| **2020** | **5.46** | 2 | **20** | **244** |
| 2021 | 3.19 | 2 | 10 | 139 |
| 2022 | 3.05 | 2 |  9 |  88 |
| 2023 | 3.20 | 2 | 10 | 127 |
| 2024 | 3.43 | 2 | 11 | 118 |

2020 has roughly 2× the within-year citation density of any other year, but only in the upper tail. This is not a data-ingestion artifact:

1. Ingestion paths are not split by year — both ingesters can contribute to any year, and the S3 ingester has no publication-year filter.
2. Avg refs *out* for 2020 is *lower* (78.64) than for other years (~86), not higher — opposite of what duplicate ingestion would produce.
3. The median is unchanged across years (2 refs/paper); only the tail differs.
4. The 2020 Medicine cohort is 11% larger than 2021's; other top fields are nearly identical.

**Likely cause:** COVID-era research clustering — tight, contemporaneous co-citation among medical/epidemiological papers published in waves. Real signal, but a once-in-a-generation outlier, not a representative pre-ChatGPT year. Using it as the baseline would falsely make any normal year look like a "decline."

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

Per paper: did it participate in at least one mutual pair? ([tests/stat_test.py](../tests/stat_test.py))

- **Pre-ChatGPT (2021):** 3,786 of 201,597 papers → 18.78 per 1000
- **Post-ChatGPT (2023–2024):** 4,403 of 400,290 papers → 10.99 per 1000
- Chi-square statistic: 604.20, p-value ≈ 0.

The drop is ~41%. The p-value is essentially zero, but at n ≈ 400,000 the chi-square test would also call a 0.5% absolute difference "significant" — so the p-value alone is not evidence of a meaningful effect. The effect size and the per-year trajectory are what matter, and they require the trajectory test below.

## Trajectory Analysis — The Decline Is Pre-Existing

Fit an exponential-decay model `log(rate) = a + b·year` to the 2021–2024 yearly mutual citation rates ([research/trajectory.py](../research/trajectory.py)).

- Annual rate of change: **−13.2% per year**, R² = 0.944, slope p = 0.028.

Residuals (observed minus trend):

| Year | Observed | Trend predicts | Residual (log) |
|------|---------:|---------------:|---------------:|
| 2021 | 12.65 | 12.13 | +0.042 (above trend) |
| 2022 |  9.94 | 10.53 | −0.057 (below — biggest drop, **pre-ChatGPT**) |
| 2023 |  9.03 |  9.14 | −0.012 (on trend) |
| 2024 |  8.15 |  7.93 | +0.027 (slightly above) |

Year-over-year decline:

- 2021 → 2022: **−21.4%** — the largest single-year drop, but 2022 papers were written before ChatGPT existed.
- 2022 → 2023: −9.2%.
- 2023 → 2024: −9.8%.

Pre vs post-ChatGPT slope (log-rate):

- Pre-ChatGPT (2021 → 2022): **−0.241** (steepest).
- Post-ChatGPT (2023 → 2024): **−0.103** (about half as steep).
- The decline is **decelerating** after ChatGPT, not accelerating.

**Conclusion.** A single exponential-decay trend fitted to 2021–2024 explains 94% of the variance. Post-ChatGPT years sit on that pre-existing trend line. The earlier chi-square "significant drop" reflects a real pre-existing decline, not a ChatGPT effect. Chart: [outputs/trajectory.png](../outputs/trajectory.png).

## Difference-in-Differences by Field Exposure

If a real ChatGPT effect exists, it should hit ChatGPT-exposed fields more than ChatGPT-unaffected fields ([research/did_analysis.py](../research/did_analysis.py)).

**Groups:**

- HIGH exposure: Computer Science (ChatGPT *is* CS research — cleanest case).
- LOW exposure: Chemistry, Materials Science, Agricultural and Biological Sciences, Earth and Planetary Sciences, Immunology and Microbiology — empirical/wet-lab/field-data fields where LLMs change workflows less.

**Per-year mutual citation rate (papers in mutual pairs per 1000):**

| Year | HIGH (CS) | LOW (5 fields) |
|------|----------:|---------------:|
| 2021 | 32.59 | 10.93 |
| 2022 | 29.98 |  7.32 |
| 2023 | 31.28 |  6.21 |
| 2024 | 19.37 |  3.58 |

**Pre/post DiD:**

- HIGH change (2021–22 → 2023–24): 31.25 → 25.33 per 1000 = **−18.9%**.
- LOW  change (2021–22 → 2023–24):  9.09 →  4.86 per 1000 = **−46.5%**.
- DiD (log-rate): **+0.416**, SE 0.083, z = +5.02, p < 0.0001 (delta-method SE on Bernoulli proportions).

**Direction.** HIGH fell *less* than LOW. Taken at face value, this is the DiD signature of a positive treatment effect: if LOW is the counterfactual for what CS would have done without ChatGPT, then CS dropped 18.9% when it "should have" dropped ~46.5%. The +0.416 log-rate point estimate is directionally *consistent with* the hypothesis's mechanism (ChatGPT-exposed fields diverging upward from non-exposed fields). CS rate did decline in absolute terms, so the literal "mutual citations increased" framing didn't happen — but the *relative* direction DiD measures matches the hypothesis's prediction.

**Why the result still cannot support the hypothesis — pre-trends are not parallel.** From 2021 to 2022 (both pre-ChatGPT):

- HIGH log change: log(29.98 / 32.59) = **−0.083**.
- LOW log change:  log(7.32 / 10.93)  = **−0.401**.
- Pre-period gap: HIGH already declining **~0.32 log-units/year slower than LOW** *before* ChatGPT existed.

The pre-existing gap was opening at roughly the rate DiD attributes to the post-period treatment effect. So +0.416 is roughly what extrapolating the pre-existing field-level pattern would predict, with no ChatGPT needed.

**What this means.** DiD here is **inconclusive**, not refuting:

- The point estimate is *compatible* with a real ChatGPT lift in exposed fields that partially offset the secular decline.
- The point estimate is *also* compatible with "CS and empirical fields have different secular decline rates for unrelated reasons, and that pre-existing pattern continued."
- Non-parallel pre-trends mean DiD cannot separate these. It neither supports nor falsifies the hypothesis on its own.

The aggregate trajectory test (no Nov-2022 break in the pooled mutual rate) remains the strongest single piece of evidence on the question.

## Volume Check — Paper Counts Are Flat

Concern: do recent years just have more papers (with more low-quality ones), mechanically deflating per-paper rates? ([research/did_volume_check.py](../research/did_volume_check.py))

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

## Year-Gap Stratification — The Decline Is in Lagged Pairs

For each mutual pair, define `gap = |year_A − year_B|`. If ChatGPT compressed peer discovery, the cleanest prediction is on `gap = 0` (same-year pairs), where contemporaneous discovery matters most. Both papers restricted to 2020–2024 ([research/year_gap_analysis.py](../research/year_gap_analysis.py)).

**Trajectory fits on log(rate per 1000), 2021–2024:**

| Stratum | Annual change | R² | Slope p |
|---------|--------------:|---:|--------:|
| Aggregate (all gaps) | **−13.2%/yr** | 0.94 | 0.028 |
| gap = 0 (same-year)  | **−10.9%/yr** | 0.92 | 0.043 |
| gap = 1 (one-year)   | **−23.9%/yr** | 0.85 | 0.078 |

**Finding.** Same-year mutual pairs decline less than half as fast as one-year-apart pairs. The aggregate decline is driven by the lagged-pair collapse, not by contemporaneous peer discovery falling apart.

**ChatGPT test on the hypothesis's home turf.** `gap = 0` is the precise axis the original hypothesis predicts should rise. Post-ChatGPT residuals on the `gap = 0` trend are +0.027 (2023) and +0.004 (2024) — essentially zero. Same-year pairs sit on the pre-existing trend line. The hypothesis fails even on its strongest possible axis.

Chart: [outputs/year_gap.png](../outputs/year_gap.png).

## Forward-Citation Validity Check — The Gap=1 Decline Is Inherited

Every `gap = 1` mutual pair anchored to year Y has two citation edges: a normal backward citation (Y → Y−1) and a structurally unusual *forward* citation (Y−1 → Y, only possible via preprint awareness or late edits). If forward citations across the whole citation graph are collapsing on their own, then the `gap = 1` mutual decline is just inherited from that broader shift — not a mutual-reciprocity-specific phenomenon. ([research/forward_citation_check.py](../research/forward_citation_check.py))

**Forward gap=+1 rate per 1000 citing-year papers:**

| citing_year | 2020 | 2021 | 2022 | 2023 |
|-------------|-----:|-----:|-----:|-----:|
| rate | 42.1 *(COVID)* | 24.7 | 25.1 | 16.6 |

Manual 3-point fit on citing-years 2021–2023 gives roughly **−18%/yr**. The `gap = 1` mutual trajectory aligned to the same citing-years (pair-years 2022–2024) gives roughly −15%/yr. These are comparable.

For comparison: same-year citations are flat (−0.5%/yr), backward gap=−1 citations decline modestly (−4.6%/yr). Forward citing specifically is what's dropping fast.

**Finding.** The `gap = 1` mutual decline is largely **inherited from a broader forward-citation collapse**, not a mutual-reciprocity-specific phenomenon.

**Likely mechanism.** Preprint dating dynamics in OpenAlex. A forward citation only exists when the citing paper saw the cited paper as a preprint before its own publication. If OpenAlex's preprint→journal deduplication has changed over time, or if preprints reach journal publication faster, forward citations would mechanically decrease.

**Script limitation.** In-script trajectory fits for forward gap=+1 got skipped because `citing_year = 2024` has no observable forward citations within our 2020–2024 window. The −18%/yr above is a manual 3-point read; clean p-values and R² require fitting on `citing_years 2021–2023`.

## Citation Age — The Metric Was an Artifact

The previously reported "3.4× increase in citation age after ChatGPT" does not hold up under inspection ([research/citation_age.py](../research/citation_age.py), [tests/citation_age_test.py](../tests/citation_age_test.py)).

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

- 2020 can match only year 2020 → max possible age 0 → avg 0.09.
- 2021 can match 2020–2021 → avg 0.83.
- 2022 can match 2020–2022 → avg 1.39.
- 2023 can match 2020–2023 → avg 1.89.
- 2024 can match 2020–2024 → avg 2.33.

This is the exact shape we observe, and it would emerge from any citation behavior — even one in which every paper cites uniformly across all available years. The metric is mechanically constrained by the dense-region width.

**Conclusion.** The "citation age increase" is primarily a measurement artifact of the works table's year-coverage profile, not a behavior change. The previous interpretation ("researchers citing older established work instead of recent peers") cannot be supported from this data.

## Final Verdict on the Hypothesis

**Original hypothesis:** mutual citations increased after ChatGPT because AI tools compressed peer discovery, creating citation loops that wouldn't have existed before.

**Verdict: not supported by this data.** The hypothesis fails on its predicted axis at every resolution we can test:

1. **Aggregate trajectory** ([research/trajectory.py](../research/trajectory.py)): 2021–2024 mutual rate follows a smooth exponential decline (R² = 0.94). Post-ChatGPT years sit on the pre-existing trend line. No step-change at Nov 2022.
2. **Same-year pairs** ([research/year_gap_analysis.py](../research/year_gap_analysis.py)): `gap = 0` (the precise axis the hypothesis cares about — contemporaneous discovery) declines smoothly at −10.9%/yr, with 2023 and 2024 sitting on the pre-existing trend. The hypothesis fails on its home turf.

Two supporting checks that constrain how the data can be reinterpreted:

3. **DiD by field exposure** ([research/did_analysis.py](../research/did_analysis.py)): the point estimate (+0.416) is directionally consistent with a partial ChatGPT lift in CS, but pre-trends were already non-parallel, so DiD cannot identify a causal effect either way. Neither supports nor refutes.
4. **Forward-citation validity check** ([research/forward_citation_check.py](../research/forward_citation_check.py)): the `gap = 1` mutual decline is inherited from a broader forward-citation collapse, likely driven by OpenAlex preprint→journal dating dynamics — not a mutual-reciprocity-specific phenomenon.
5. **Volume check** ([research/did_volume_check.py](../research/did_volume_check.py)): paper counts are flat (−0.4%); the per-paper rates and field-level patterns are not explained by differential paper volume or citation-lag effects.

The hypothesis as literally written ("mutual citations *increased* after ChatGPT") didn't happen — mutual rates declined. The deeper question — whether ChatGPT *changed* mutual citation behavior at all (e.g. cushioned an existing decline) — is **not falsified** by this data; it's just untestable here. With only 4 yearly data points and a strong pre-existing trend, an effect smaller than annual noise cannot be distinguished from no effect.

## What We Found vs. What We Ruled Out

- **Found:** a real secular decline in mutual citation rates (−13.2%/yr, R² = 0.94) that started **before** ChatGPT.
- **Found:** the decline is concentrated in lagged (gap=1) pairs (−24%/yr), not same-year pairs (−11%/yr).
- **Found:** the gap=1 decline is itself largely inherited from a broader forward-citation collapse, likely a preprint-dating artifact in OpenAlex.
- **Found:** the apparent citation-age increase is a measurement artifact of the works table's year coverage, not a behavior signal.
- **Ruled out:** that ChatGPT caused a discrete, yearly-resolution step-change in mutual citation rate, in same-year mutual rate, or in citation age. Every post-ChatGPT year sits on a pre-existing trend line.
- **Not ruled out:** a small ChatGPT effect riding on top of the larger trend (4 yearly data points lack the power); sub-annual effects; effects on dimensions we didn't measure; long-run effects that haven't manifested in ~1.5 post-ChatGPT years.

**Methodological lesson.** At n ≈ 400,000, binary pre/post chi-square gives p ≈ 0 on any pre-existing trend — which is easy to mistake for a causal effect. The trajectory test (per-year trend + residuals + pre/post slope comparison), combined with cross-field DiD and stratification by year-gap, is what distinguished "real signal at the right time" from "real signal that predates the cause."

## Future Research

The questions below are the natural follow-ups to what this project established. The first two are the strongest leads — both have scripts already written ([research/monthly_trajectory.py](../research/monthly_trajectory.py), [research/monthly_robustness.py](../research/monthly_robustness.py)) and the required data backfilled, but results are not yet documented.

1. **Does a monthly-resolution Chow test detect a structural break at Nov 2022?** The yearly trajectory had near-zero power; ~48 monthly points across 2021–2024 give the strongest test available against a step-change at ChatGPT's launch.
2. **Is the broader forward-citation collapse a real behavior shift or an OpenAlex dating artifact?** The `gap = 1` mutual decline is inherited from it; isolating its mechanism would clarify how much of the −13.2%/yr aggregate decline is real behavior vs. ingestion semantics.
3. **Does a within-CS DiD (NLP/ML-adjacent subfields vs theory/compilers) show a ChatGPT lift?** Pre-trends inside CS are likely more parallel than the CS-vs-empirical split, so this version of DiD might actually identify a causal effect where the field-level version cannot.
4. **What is driving the pre-existing secular decline in mutual citation rates?** Candidates: within-field rate changes vs. between-field composition shifts; rising citation concentration (Gini/HHI) that mechanically suppresses pair formation. Independent of the ChatGPT question, this is a real finding the project surfaced and the cause is not yet known.
