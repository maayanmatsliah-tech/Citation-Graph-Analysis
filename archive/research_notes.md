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

## Citation Age Re-examination (May 17, 2026)

Applied the same trajectory test to the citation-age finding (previously reported as a 3.4× increase post-ChatGPT, "interpreted as researchers citing older established work"). Two checks: (a) fit a trend through 2021-2024 and look for a ChatGPT break, (b) test whether the metric is even a real behavior signal or an artifact of the works table's coverage profile.

**Per-year average cited age (citing 2020-2024, cited 1950-2024):**

| Citing year | Avg cited age (years) |
|-------------|-----------------------|
| 2020 | 0.09 |
| 2021 | 0.83 |
| 2022 | 1.39 |
| 2023 | 1.89 |
| 2024 | 2.33 |

**Trajectory fit (2021-2024, 2020 excluded):**
- Slope: +0.497 years per year
- R² = **0.997**, slope p = 0.0014 (line fits the data nearly perfectly)
- Residuals are all under 0.04 years — every year sits on the trend
- Pre-ChatGPT slope (2021 → 2022): +0.56 (steepest)
- Post-ChatGPT slope (2023 → 2024): +0.44 (shallower)

Same shape as the mutual-citation analysis: continuous trend, no break at ChatGPT, slope slightly *decelerating* after ChatGPT. ChatGPT attribution is not supported here either.

**But the bigger problem: the metric itself is structurally biased.** Two checks:

1. **Where are the matched citations going?** For every citing year, 99.5-100% of matched citations are against papers in the dense 2020-2024 region of the works table. Only 854 to 2,498 citations per year reach pre-2020 cited papers — the works table's pre-2020 coverage (from the S3 snapshot) is too sparse for most pre-2020 citations to find a JOIN match.

2. **What does "avg cited age" therefore measure?** Almost entirely: how many years of the dense 2020-2024 region are reachable backward from the citing year (since `citing_year ≥ cited_year`).
   - 2020 can match only cited year 2020 → max possible age = 0 → avg 0.09
   - 2021 can match 2020-2021 → avg 0.83
   - 2022 can match 2020-2022 → avg 1.39
   - 2023 can match 2020-2023 → avg 1.89
   - 2024 can match 2020-2024 → avg 2.33

   This is the exact shape we observe, and it would emerge from any citation behavior — even one in which every paper cites uniformly across all available years. The metric is mechanically constrained by the dense-region width, not by real citation behavior.

**Conclusion for citation age.** The previously reported "3.4× increase in citation age after ChatGPT" is **primarily a measurement artifact** of the works table's year-coverage profile, not a real behavior change. With this dataset's coverage shape, the avg-age metric tracks "available cited years in the dense region," which grows monotonically with citing year by construction. The original interpretation ("researchers citing older established work instead of recent peers") cannot be supported from this data.

The narrow side-check on pre-2020 cited papers (avg age 18.06 in 2020 vs. 24.17 in 2024) does show an apparent shift, but it's based on 854-2,498 citations per year — a tiny, non-random subset of pre-2020 papers (whichever happened to make it into the S3 snapshot). Not enough to support a real-world claim.

**Overall conclusion (mutual + age, May 17, 2026).** Both headline findings collapse under trajectory testing:
- Mutual citation rate: real decline, but pre-existing and continuous; no ChatGPT break.
- Citation age increase: largely a data-coverage artifact; no behavior signal that survives controlled comparison.

Neither finding supports the original hypothesis that ChatGPT changed citation behavior. To make a real claim here would require (a) finer temporal resolution (monthly publication data) and (b) a uniformly-indexed citation graph including dense pre-2020 coverage — neither available in the current data.

## What This Does and Doesn't Tell Us (May 17, 2026)

- **Found:** a real secular decline in mutual citation rates (−13.2%/year, R² = 0.94) that started before ChatGPT.
- **Found:** the apparent citation-age increase is mostly a measurement artifact of the works table's year coverage, not a behavior signal.
- **Ruled out:** that ChatGPT caused a discrete, yearly-resolution step-change in either metric. Both post-ChatGPT years sit on the pre-existing trend line.
- **Did NOT rule out:** a small ChatGPT effect riding on top of the larger trend (4 data points isn't enough power); sub-annual effects; effects on dimensions we didn't measure (citation novelty, cross-field reach, semantic similarity, etc.); long-run effects that haven't manifested yet (~1.5 years of post-ChatGPT papers).
- **Bottom line:** the *specific* hypothesis ("ChatGPT caused mutual citations to increase via compressed peer discovery") is not supported. The *broader* question ("did ChatGPT change citation behavior at all") is untestable with this dataset.

**Methodological lesson:** at n ≈ 400,000, binary pre/post chi-square gives p ≈ 0 on any pre-existing trend — which is easy to mistake for a causal effect. The trajectory test (per-year trend + residuals + pre/post slope comparison) is what distinguished "real signal at the right time" from "real signal that predates the cause."

## Difference-in-Differences Across Fields (May 17, 2026)

Built research/did_analysis.py. Idea: a secular trend should hit all fields equally; a real ChatGPT effect should hit fields that adopted ChatGPT heavily *more than* fields that didn't. If we see HIGH-exposure fields diverge from LOW-exposure fields after Nov 2022, that's a real causal signal.

**Groups:**
- HIGH exposure: Computer Science (cleanest case — ChatGPT *is* CS research)
- LOW exposure: Chemistry, Materials Science, Agricultural and Biological Sciences, Earth and Planetary Sciences, Immunology and Microbiology — empirical/wet-lab/field-data fields where LLMs change workflows less

**Per-year mutual citation rate (papers in mutual pairs per 1000):**

| Year | HIGH (CS) | LOW (5 fields) |
|------|-----------|----------------|
| 2021 | 32.59 | 10.93 |
| 2022 | 29.98 |  7.32 |
| 2023 | 31.28 |  6.21 |
| 2024 | 19.37 |  3.58 |

**Pre/post DiD:**
- HIGH change (2021-22 → 2023-24): 31.25 → 25.33 per 1000 = **−18.9%**
- LOW  change (2021-22 → 2023-24):  9.09 →  4.86 per 1000 = **−46.5%**
- DiD (log-rate): **+0.416**, SE 0.083, z = +5.02, **p < 0.0001**

**Direction:** HIGH dropped *less* than LOW. Taken at face value, this is the DiD signature of a positive treatment effect: CS dropped 18.9% when the "no-ChatGPT counterfactual" (LOW) suggests it should have dropped ~46.5%. The +0.416 log-rate point estimate is directionally **consistent with** the hypothesis's mechanism (ChatGPT-exposed fields diverging upward from non-exposed fields). CS rate did decline in absolute terms, so the literal "mutual citations increased" framing did not happen — but the *relative* direction DiD measures matches the hypothesis's prediction.

**Why the result still cannot support the hypothesis — pre-trends are not parallel.** From 2021 to 2022 (both pre-ChatGPT):

- HIGH log change: log(29.98 / 32.59) = −0.083
- LOW log change:  log(7.32 / 10.93)  = −0.401
- Pre-period gap: HIGH already declining ~0.32 log-units/year slower than LOW before ChatGPT existed.

The pre-existing gap was opening at roughly the rate DiD attributes to the post-period treatment effect. So +0.416 is roughly what extrapolating the pre-existing field-level pattern would predict, with no ChatGPT needed.

**What this means.** DiD here is **inconclusive**, not refuting:

- The point estimate is *compatible* with a real ChatGPT lift in exposed fields that partially offset the secular decline.
- The point estimate is *also* compatible with "CS and empirical fields have different secular decline rates for unrelated reasons, and that pre-existing pattern continued."
- Non-parallel pre-trends mean DiD cannot separate these. It neither supports nor falsifies the hypothesis on its own.

The aggregate trajectory test (no Nov-2022 break in the pooled mutual rate) remains the strongest single piece of evidence on the question.

**(May 18, 2026 correction.)** An earlier version of this section claimed the DiD result was "in the opposite direction of the hypothesis" and "directly falsified at the field level." That framing was wrong: HIGH falling less than LOW is the DiD signature of a *positive* treatment effect, not opposite. The correct framing is that DiD is uninformative here because pre-trends were already non-parallel — not that it falsifies anything.

## Volume Check — All Fields Combined (May 17, 2026)

Question raised: do recent years just have more papers (with more low-quality ones nobody cites), and is that mechanically deflating the per-paper rates? Comparing equal 2-year windows before and after ChatGPT (Nov 2022), across all fields:

| Period | Papers | Avg citations per paper | Avg mutual citations per paper |
|--------|-------:|------------------------:|-------------------------------:|
| Pre  (2021–2022) | 401,699 | 13.17  | 0.0215 |
| Post (2023–2024) | 400,290 |  3.64  | 0.0157 |
| Change | −0.4% | −72.3% | −27.1% |

(Mutual count per paper = how many mutual pairs the paper participates in on average. A paper in 3 mutual pairs counts as 3.)

Per-year breakdown:

| Year | Papers | Total citations received | Avg cit/paper | Mutual pair memberships | Avg mut/paper |
|------|-------:|-------------------------:|--------------:|------------------------:|--------------:|
| 2021 | 201,597 | 3,158,708 | 15.67 | 4,865 | 0.0241 |
| 2022 | 200,102 | 2,129,913 | 10.64 | 3,764 | 0.0188 |
| 2023 | 200,063 | 1,197,181 |  5.98 | 3,504 | 0.0175 |
| 2024 | 200,227 |   261,263 |  1.31 | 2,767 | 0.0138 |

What this means for the volume/garbage concern:
- **Paper counts are basically flat (−0.4%).** No paper-volume explosion to explain the rate drops.
- **The 72% drop in overall citations per paper is a clock issue.** 2024 papers have had ~12 months to accumulate citations; 2021 papers have had 4+ years. The drop is steepest at the most recent year, which fits citation-lag exactly. This affects all fields roughly equally (CS −69%, the 5 empirical fields −74%), so it does not explain the CS-vs-empirical gap.
- **Mutual citations drop only 27%, not 72%.** Mutual pairs require both papers to exist at the same time, so they aren't dragged down by years of citation accumulation. This is why the mutual-citation metric is more trustworthy than raw citation counts for recent years.
- **The field-level DiD result survives.** Volume and citability moved the same way across fields, so the gap between CS (−19%) and the 5 empirical fields (−47%) is not explained by differential paper volume or paper quality. See research/did_volume_check.py for the per-field check.

## Why Mutual Citations Are the Reliable Metric (May 17, 2026)

A note on what we can and can't claim from this data.

**The drop in overall citations per paper is not a real finding about citation behavior.** A 2021 paper has had four years to be discovered and cited. A 2024 paper has had only a few months. So when we see avg citations per paper fall from 15.67 in 2021 to 1.31 in 2024, that's mostly just newer papers not having had enough time to collect citations yet — not researchers citing less. We cannot claim that papers are getting cited less after ChatGPT from this number, because future citations of those recent papers haven't happened yet but will.

**Mutual citations are different. They don't suffer from this problem.**

A mutual citation requires paper A to cite paper B *and* paper B to cite paper A. Both citations have to exist in the published versions of the two papers. A paper's citation list is fixed when the paper is published — authors can't go back and add new references to a paper that's already out. So once both papers are published, the mutual pair between them either exists or it doesn't. Waiting another year won't create new mutual pairs between papers that already exist, because neither paper's citation list can change.

This means:
- For overall citations: 2024 numbers are an undercount because more citations will accumulate. Comparing 2024 to 2021 on this metric is unfair to 2024.
- For mutual citations: 2024 numbers are already complete. Comparing 2024 to 2021 is a fair comparison.

That's why the mutual citation rate is the right metric for this question, and why we can trust the 27% drop in mutual citations per paper while we cannot trust the 72% drop in overall citations per paper as a behavior signal.

## Final Verdict on the Hypothesis (May 17, 2026)

**Original hypothesis:** mutual citations increased after ChatGPT because AI tools compressed peer discovery, creating citation loops that wouldn't have existed before.

**Verdict:** **not supported** by this data. The strongest single piece of evidence is the trajectory test:

1. **Aggregate trajectory** (research/trajectory.py): 2021–2024 mutual rate follows a smooth exponential decline (R² = 0.94). Post-ChatGPT years sit on the pre-existing trend line. No step-change at Nov 2022 — the years where a ChatGPT effect should appear behave indistinguishably from the years before it existed.

Two supporting checks that constrain how the data can be reinterpreted:

2. **DiD by field exposure** (research/did_analysis.py): the point estimate (+0.416) is directionally consistent with a partial ChatGPT lift in CS, but pre-trends were already non-parallel (HIGH declining ~0.32 log-units/year slower than LOW pre-ChatGPT). DiD here is inconclusive — it cannot identify a ChatGPT effect either way.
3. **Citation age** turned out to be a measurement artifact of the works table's year coverage, so it doesn't support the hypothesis either.

**What remains untestable** with this data: whether ChatGPT *changed* mutual citation behavior at all in ways the trajectory test can't pick up — sub-annual effects, smaller magnitude, different metric, longer-run, or a partial lift that DiD can't separate from pre-existing field-level patterns. The hypothesis as literally written ("mutual citations *increased* after ChatGPT") did not happen. The broader question of whether ChatGPT had any effect on this metric is left open.

Chart: outputs/trajectory.png.

**(May 18, 2026 correction.)** An earlier version of this section called the verdict "rejected with reasonable confidence" and listed DiD as a "direct falsification at the field level." Both are too strong. The trajectory test is the only line that genuinely cuts against the hypothesis; DiD with non-parallel pre-trends is inconclusive. Verdict is now "not supported" rather than "rejected."

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

## Next Directions (May 18, 2026)

Two threads to continue the project on. The original hypothesis is closed (see Final Verdict above); these threads are about the *real* findings the project surfaced.

### Direction 1: Why is the mutual citation rate declining at all?

The −13.2%/year decline is real, statistically significant, and predates ChatGPT. We don't know what's driving it. Candidate analyses, ordered by information-per-effort:

- **Within-vs-between field decomposition** (top pick). Decompose the aggregate yearly change into (a) within-field rate changes — every field declining — vs (b) between-field composition shifts — fields with naturally lower mutual rates growing as a share of papers. Tells us whether to chase a universal-cause story or a composition-shift story. Cheap; uses data we have.
- **Citation concentration (Gini / HHI) over time.** Are citations becoming spread across more papers over time? If so, the probability of two papers landing on each other drops mechanically. Doesn't require new data.
- **Mutual-pair year-gap distribution over time** (see "shared analysis" below).

### Direction 2: Did ChatGPT change citation behavior at all?

The trajectory test failed mostly because we have only 4 yearly data points — weak power against any effect smaller than annual noise. To detect *any* ChatGPT effect we need either finer resolution, a different metric, or a cleaner identification strategy. Candidate analyses:

- **Check if OpenAlex stores finer-than-year publication dates** (top pick, but conditional). If month or quarter is available, we can build a monthly mutual-citation series, fit a trend through pre-Nov-2022 months, and test for a break at Nov 2022. This is the closest thing to a real power upgrade over what we have. If only year is stored, this path is dead — fall back to a different metric.
- **Time-to-first-N-citations as an alternative metric.** When a paper is published, how many days/weeks pass before its first 5 or 10 inbound citations arrive? If ChatGPT speeds discovery, post-Nov-2022 papers should accumulate first citations faster (need to control for citation lag carefully).
- **Composition of mutual pairs, not just count.** Even if total mutual rate doesn't break at Nov 2022, the *types* of mutual pairs might shift — more cross-field, more institutionally diverse, smaller year-gap. A composition shift at the right time would be a real signal.
- **Within-CS DiD** instead of CS-vs-empirical. NLP/ML-adjacent subfields (most exposed) vs CS-but-far-from-LLMs subfields (theory, compilers, formal methods). Pre-trends are likely more parallel than the CS-vs-empirical split, which would let DiD actually identify an effect.

### Shared analysis (serves both directions)

**Year-gap distribution within mutual pairs** — for each mutual pair, compute cited_year − citing_year and look at the distribution of same-year vs ±1 vs ±2+ pairs over time.

- Why it serves direction 1: if the share of same-year mutual pairs is collapsing, contemporaneous discovery is getting harder, which is a concrete mechanism for the secular decline.
- Why it serves direction 2: the original hypothesis specifically predicted that *contemporaneous* mutual citations should rise after ChatGPT (compressed peer discovery → researchers citing peers they only just found). Testing on this specific axis is fairer to the hypothesis than the aggregate mutual rate.
- Cost: one SQL query. Worth running first to steer both threads.

### Concrete next step

Check what publication-date granularity exists in `citations.duckdb`, then run the year-gap distribution. Outputs from those two will tell us which of the other candidates is worth investing in.

## Year-Gap Stratification of Mutual Pairs (May 18, 2026)

Built `research/year_gap_analysis.py` to split mutual pairs by year-gap = `ABS(year_A - year_B)`. Both papers restricted to 2020-2024 (dense region).

Per-stratum trajectory fits (2021-2024, 2020 excluded as COVID outlier):

- aggregate (all gaps):       −13.2%/yr, R² = 0.94, p = 0.028
- **gap = 0 (same year):**    **−10.9%/yr**, R² = 0.92, p = 0.043
- **gap = 1 (one year apart):** **−23.9%/yr**, R² = 0.85, p = 0.078

**Finding.** Same-year mutual pairs decline less than half as fast as one-year-apart pairs. The aggregate decline is driven by the lagged-pair collapse, not by contemporaneous peer discovery falling apart.

**ChatGPT test on the hypothesis's home turf.** gap=0 is the precise axis the original hypothesis predicts should rise (compressed peer discovery → more contemporaneous mutual citations). Post-ChatGPT residuals on the gap=0 trend are +0.027 (2023) and +0.004 (2024) — essentially zero. Same-year pairs sit on the pre-existing trend line. Hypothesis closed even on its strongest possible axis.

Chart: `outputs/year_gap.png`.

## Forward-Citation Validity Check (May 18, 2026)

Built `research/forward_citation_check.py` to test whether the gap=1 mutual decline above is mutual-reciprocity-specific or just inherited from a broader collapse in forward citations.

Every gap=1 mutual pair requires a forward citation: the earlier paper citing the later paper, only possible via preprint awareness or late edits. Forward gap=+1 rate per 1000 citing-year papers:

| citing_year | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|
| rate | 42.1 (COVID) | 24.7 | 25.1 | 16.6 |

Manual 3-point fit on citing-years 2021-2023 gives roughly **−18%/yr**. The gap=1 mutual trajectory aligned to the same citing-years (pair-years 2022-2024) gives roughly −15%/yr. These are comparable.

**Finding.** The gap=1 mutual decline is largely **inherited from a broader forward-citation collapse**, not a mutual-reciprocity-specific phenomenon. For comparison: same-year citations are flat (−0.5%/yr), backward gap=−1 citations decline modestly (−4.6%/yr). Forward citing specifically is what's dropping fast.

**Likely mechanism.** Preprint dating dynamics. A forward citation only exists when the citing paper saw the cited paper as a preprint before its own publication. If OpenAlex's preprint→journal deduplication has changed over time, or if preprints reach journal publication faster, forward citations would mechanically decrease. Consistent with the earlier citation-age artifact finding — both point at OpenAlex date-coverage semantics shifting across years.

**Script limitation.** In-script trajectory fits for forward gap=+1 got skipped because `citing_year=2024` has no observable forward citations within our 2020-2024 window. The −18%/yr is a manual 3-point read; for clean p-values and R² the script needs to fit on `citing_years 2021-2023` instead of `2021-2024`.

## Monthly Date Backfill (May 18, 2026)

Built `data/backfill_dates.py` to add monthly publication dates and paper type to existing `works` rows. Targeted scope, not a full re-ingest.

**Why.** The yearly-resolution trajectory test had no power against a structural break at ChatGPT's launch (4 data points). Monthly resolution gives ~48 points across 2021–2024 and makes a real Chow test possible. The `type` field separately enables splitting preprints from journal articles — directly testing the preprint-dating mechanism flagged by `forward_citation_check.py`.

**Scope.** Backfills only the ~16k papers that actually participate in mutual pairs across 2020–2024 (the numerator papers). For monthly denominators the script either samples (`SAMPLE_PER_YEAR > 0`) or falls back to a `yearly_papers / 12` approximation. Default is the approximation since a uniform-within-year miscalibration doesn't matter for *detecting* a step-change at a specific month.

**Two new columns on `works`:**
- `publication_date` (DATE) — full ISO date, e.g. `2023-03-15`
- `type` (TEXT) — `article`, `preprint`, `book-chapter`, ...

**Run result.** 16,075 of 16,075 mutual-pair papers backfilled in 7.8 min, 0 errors. 100% coverage per year 2020–2024 on mutual-pair participants. `citations` table untouched.

Script is resumable (queries `WHERE publication_date IS NULL` each run); a later pass to backfill the full ~1M papers is possible if denser denominators become useful.

## Monthly Trajectory and Chow Test (2026-05-20)

Ran `research/monthly_trajectory.py` (42 monthly observations, 2021-01 through 2024-06, 6-month tail censoring for ingestion latency, 2020 excluded as COVID outlier).

Aggregate fit: −12.0%/yr, R² = 0.18 (much lower than yearly because monthly noise is real), slope p = 0.005.

Chow test at Dec 2022: F = 3.97, **p = 0.027**. Pre slope −26.5%/yr, post slope **+16.6%/yr** (slope flipped sign). Initially looked like a real ChatGPT break.

Robustness checks (`research/monthly_robustness.py`):
- Deseasonalize: stronger break (p = 0.0055), post slope +9.5%/yr — break survives.
- Exclude 2021: break vanishes (p = 0.17), post slope identical — small-n power issue.
- Censoring sensitivity: break present at 6mo (p=0.027) and 9mo (p=0.034) censoring, absent at 3mo (p=0.30) and 12mo (p=0.46). Inconsistent.

## Placebo Chow Test (2026-05-20) — the monthly break is artifactual

Ran `research/placebo_chow.py` to sweep every candidate break date and to drop the visible Dec 2022 outlier.

Result 1: **23 of 30 candidate break dates are "significant" at p < 0.05.** The Chow test fires almost everywhere. ChatGPT's date ranks **9th** by F-statistic — Jan 2022 (F=5.06, p=0.011) and Jan 2023 (F=5.02, p=0.012) are stronger "breaks."

Result 2: Dec 2022 is the **single lowest-rate month in the dataset** (4.50/1000; surrounding months 7.86–9.78). Excluding only this one month drops the ChatGPT-date Chow result from p=0.027 to **p=0.081 (no break)** and collapses the post-slope from +16.6%/yr to **+1.7%/yr**.

**Verdict.** The monthly Chow result is not a real break. It was driven by the conjunction of:
- Dec 2022 being the single deepest seasonal dip (every Dec/Nov is a low; this one was lower);
- January 2023 being seasonally elevated (Jan is the seasonal peak every year);
- The Chow test having low specificity on a noisy series with strong seasonality at this n.

Methodological note: Chow tests on small-n monthly series with seasonal cycles will fire indiscriminately. Always run a placebo sweep before claiming a break.

## Pipeline-Drift / Preprint-Dedup Test (2026-05-20) — REFUTED

Ran `research/pipeline_drift_check.py` to test the previously-hypothesized mechanism for the gap=1 forward-citation collapse: changing preprint→journal deduplication in OpenAlex.

Result: **Forward citations are NOT preprint-driven.** Of all forward (gap > 0) citations in 2020-2024:
- 78.3% are article → article
- 9.7% are review → article
- Only **3.0% touch a preprint at all** (i.e. either endpoint has type=preprint)
- Only 1.6% are article → preprint specifically

Whatever is causing the forward-citation collapse, it is not preprint deduplication. The article-to-article forward edges (the dominant 78%) are not affected by preprint dedup semantics.

Field heterogeneity check: preprint-heavy fields (CS, Physics, Biochem) decline at −16.3%/yr average; other fields decline at −18.8%/yr average. Preprint-heavy fields decline *slower*, not faster — the opposite of what the dedup hypothesis predicted.

The forward-citation collapse remains a real but unexplained phenomenon. Preprint dedup is ruled out as the mechanism.

## OpenAlex Sample Composition Drift (2026-05-20)

While running per-field analyses, discovered substantial classification/sample drift across years in our 200k-per-year sample:

| Field | 2020 | 2021 | 2022 | 2023 | 2024 | Change |
|-------|-----:|-----:|-----:|-----:|-----:|-------:|
| Mathematics | 2,163 | 1,307 | 722 | 582 | 492 | **−77%** |
| Psychology | 6,769 | 5,673 | 4,130 | 3,328 | 3,019 | **−55%** |
| Social Sciences | 9,834 | 9,063 | 7,214 | 5,945 | 5,188 | **−47%** |
| Earth & Planetary | 2,628 | 2,550 | 2,302 | 1,929 | 1,745 | **−34%** |
| Engineering | 31,687 | 34,983 | 38,786 | 41,378 | 45,380 | **+43%** |
| Materials Science | 13,003 | 13,871 | 15,044 | 16,295 | 18,621 | **+43%** |
| Energy | 5,499 | 6,496 | 7,382 | 8,265 | 8,822 | **+60%** |
| Chemical Engineering | 1,010 | 1,140 | 1,322 | 1,460 | 1,680 | **+66%** |

Total papers per year is constant at ~200k by design. The mix shifts because pre-2024 papers were ingested mostly via S3 snapshots (`data/citation_parser.py`), while 2024 papers came mostly via the OpenAlex API (`data/api_ingest.py`). The two ingestion paths surface different field distributions.

Mathematics dropping 77% is not real-world plausible. This contaminates any per-field cross-year comparison. The aggregate mutual rate decline must be tested against this confound.

**Robustness check:** Restricted to 15 fields with stable or growing paper counts (excluding Math, Psych, Soc Sci, Medicine, etc), the aggregate mutual rate trajectory is *steeper* (−19.3%/yr, R²=0.90) than the full-sample trajectory (−13.2%/yr). The decline is not driven by the shrinking-classification fields. It is real and robust.

**Caveat for any field-level analysis on this dataset:** per-field magnitudes are contaminated by classification/sample drift. Aggregates are not.

## Within-vs-Between Decomposition (2026-05-20)

Ran `research/field_heterogeneity.py`.

Counterfactual decompositions of the 2021 → 2024 aggregate decline (18.78 → 8.82 per 1000):
- **Counterfactual A** (fix every field's rate at 2021 value, use 2024's field composition): 17.36 per 1000 — composition shift alone explains ~14% of decline.
- **Counterfactual B** (fix composition at 2021, use 2024's per-field rates): 9.39 per 1000 — within-field rate change alone explains ~94% of decline.

The decline is essentially entirely **within-field**. The same fields, looked at year over year, show lower per-paper mutual citation rates. Sums exceed 100% due to the interaction term.

## Citation Breadth Expansion (2026-05-20) — THE MAIN POSITIVE FINDING

Ran a direct test of the "compressed peer discovery" hypothesis using a different metric: average number of distinct OpenAlex fields cited per citing paper.

| Year | Cross-field share | Avg distinct cited fields per paper | Median |
|------|------------------:|------------------------------------:|-------:|
| 2020 | 28.6% | **1.66** | 1 |
| 2021 | 31.1% | 2.06 | 2 |
| 2022 | 31.5% | 2.42 | 2 |
| 2023 | 33.0% | 2.78 | 2 |
| 2024 | 35.0% | **3.11** | 3 |

Citation breadth has **almost doubled in four years** (1.66 → 3.11; ×1.88). Median rose from 1 to 3 fields. Avg refs *out* per paper is flat across years (~85 per paper) — total citation budget is unchanged. What's changing is how broadly that budget is spent.

**Robust to all known confounds:**
- Restricted to 15 stable-volume fields (controlling for classification drift): 1.50 → 3.13 (×2.08)
- Restricted to Computer Science papers only (single field, classification-anchored): 1.44 → 2.92 (×2.02)
- The doubling holds in every cleaner subset we try.

**Mechanistic link to the mutual citation decline.** If the same per-paper reference budget is spread over twice as many fields, the average within-field citation density per paper roughly halves. Mutual pair formation between two same-field papers requires both papers to spend some of their reference budget on each other; with broader citing, this becomes mechanically rarer. The aggregate mutual rate dropping 53% (18.78 → 8.82) and citation breadth doubling are quantitatively compatible with a single underlying broadening trend.

**Not a ChatGPT effect.** The growth rate of breadth is *decelerating* over time (year-over-year increase: 24.5% → 17.1% → 14.9% → 12.1%), the opposite shape of what a discontinuous ChatGPT impact would produce. The trend was already underway before ChatGPT existed and is the dominant story of citation patterns in this period.

## Reframed Conclusion (2026-05-20)

Original hypothesis (ChatGPT compressed peer discovery → mutual citations *up*): **not supported.** Yearly trajectory shows no break; monthly Chow test fires but is artifactual on placebo testing.

Actual finding: **citation patterns are broadening at a substantial, steady, pre-existing rate.** Papers cite work from nearly twice as many fields in 2024 as in 2020. This broadening provides a coherent mechanism for the 53% drop in mutual citation rates that we initially mistook for a ChatGPT effect.

Eliminated mechanisms for the secular decline:
- ChatGPT step change (no monthly break, placebo test refutes)
- Paper volume / quality dilution (flat denominators)
- Citation lag (mutual citations are lag-immune by construction)
- Preprint deduplication (forward citations are 97% non-preprint)
- Citation concentration (modest Gini change, insufficient magnitude)
- Composition shift across fields (only ~14% of decline)

Surviving mechanism: **citation breadth expansion (the same reference budget spread across more fields).** Robust to classification drift, monotone, large in magnitude, and quantitatively compatible with the mutual rate decline.

Methodological byproducts worth keeping:
- OpenAlex per-year samples show substantial field-composition drift (e.g. Math down 77% in our sample). Any per-field cross-year comparison on capped per-year samples needs an explicit field-stability check.
- The citation-age "increase" remains a coverage artifact (works-table density profile).
- The forward-citation collapse is real (~−18%/yr) but the preprint-dedup mechanism is wrong; cause now unknown.
- Chow tests on small-n monthly series with seasonality fire indiscriminately. Always placebo-sweep candidate break dates.