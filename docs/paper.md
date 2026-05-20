# Citation Breadth Has Nearly Doubled in Four Years: A Mutual-Citation Decline With an Identified Mechanism

## Abstract

We set out to test whether ChatGPT, released in November 2022, increased the rate of *mutual citations* — the unusual case where two papers cite each other — by compressing peer discovery. Across roughly 1M papers from OpenAlex spanning 2020–2024, we find no evidence for the ChatGPT prediction: mutual citation rates declined steadily across the window, and the apparent step-change at ChatGPT's launch dissolves under a placebo test (in which 23 of 30 candidate break dates produce nominally "significant" Chow statistics, and removing a single outlier month kills the result). What we found instead is a clear, robust, previously-undocumented phenomenon: **the average paper now cites work from nearly twice as many distinct fields as it did four years ago** (1.66 fields in 2020 to 3.11 in 2024), with a flat total reference budget. This broadening is monotone, persists when the analysis is restricted to fields with stable sample composition, and persists even within Computer Science taken alone. We argue it provides a quantitative mechanism for the 53% decline in mutual citation rates over the same window: the same reference budget spread over more fields produces less within-field overlap, and mutual pair formation drops mechanically. The broadening trend is decelerating over time, not accelerating, so it is not a ChatGPT effect — it is a longer-running shift in how scientific literature is being cited.

## 1. Introduction

When ChatGPT was released to the public in November 2022, it changed how many researchers interact with the scientific literature. Instead of reading a paper end-to-end to extract a single claim, researchers can now ask a language model to surface a relevant passage. This plausibly compresses the front end of the research process — finding, filtering, and extracting from prior work — in ways that could leave a measurable fingerprint on what people cite.

This project began by testing one specific prediction of that hypothesis: that *mutual citations* — where paper A cites paper B and paper B cites paper A — should have risen after ChatGPT. Mutual citations are structurally rare. They require both authors to discover each other's work and decide to cite it, within an overlapping writing window. If ChatGPT compressed that discovery process, citation loops that previously didn't form should start forming.

The mutual-citation prediction did not hold. But the path to ruling it out led us to a much more substantial finding: citation patterns in our dataset are broadening at a striking rate. Papers in 2024 cite work from roughly twice as many fields as papers in 2020. The change is monotone year over year, the total reference budget per paper is essentially flat, and the trend predates ChatGPT and is decelerating — so it cannot be attributed to any single technology shock. It is, however, the most plausible mechanistic explanation we can identify for the substantial decline in mutual citations that we and others have observed in this period.

The contribution of this paper is therefore twofold: a careful null result on the ChatGPT-mutual-citation hypothesis, including a methodological note about how Chow tests behave on noisy small-*n* monthly series, and a positive finding about citation breadth expansion that reframes the secular mutual-citation decline as a mechanically downstream consequence of broader citation behavior.

## 2. Hypothesis and Definitions

We initially tested the following hypothesis:

> Mutual citation rate per 1000 papers increased after November 2022, beyond what would be expected from changes in paper volume alone.

A few definitions that recur throughout:

- A **citation graph** is a directed network of papers. An edge from A to B means A's reference list contains B.
- A **mutual citation** (or *mutual pair*) is the case where both A → B and B → A are present.
- A **self-citation** is an edge from a paper to itself (an artifact in our raw data; excluded throughout).
- A **field** is one of OpenAlex's ~27 top-level subject labels (e.g. "Computer Science", "Materials Science"). Each paper has exactly one primary field.

A note on the original hypothesis. Mutual citations require both papers to exist when each is written, *and* both authors to clear the awareness bar within a narrow temporal window. ChatGPT cannot help A cite B if B does not yet exist, and the mutuality requirement doubles the temporal constraint. Mutual citation rate is therefore one specific testable surface of "compressed peer discovery," not the whole hypothesis. We discuss this limitation in §6.

## 3. Data

All data comes from [OpenAlex](https://openalex.org/), a public bibliographic database. We use two ingestion paths: the OpenAlex S3 snapshot for older papers and the OpenAlex API for 2020–2024 top-up. Both ingesters write to the same `works` and `citations` tables in a single DuckDB database. The resulting dataset contains approximately 200,000 papers for each year from 2020 through 2024 — a deliberately flat denominator that simplifies year-over-year comparisons.

A diagnostic finding worth flagging upfront: our 200k-per-year sample shows substantial field-classification drift across years (see §5.6). Mathematics drops 77% across our window; Engineering grows 43%. These shifts are not real-world plausible and are almost certainly an artifact of OpenAlex's API ordering and topic-classification pipeline rather than real publication-volume changes. Per-field cross-year comparisons in this dataset require an explicit field-stability robustness check; the aggregate measures (which do not depend on field labels) are unaffected.

For each paper we store an ID, title, publication year, and field. For each citation we store the citing and cited paper IDs. As of an earlier pass, full publication dates and paper types were also backfilled for the ~16,000 papers participating in any mutual pair. Pre-2020 coverage in the works table is sparse, which matters for the citation-age artifact discussed in §5.7.

## 4. Methods

### 4.1 Time windows and exclusions

- **Pre-ChatGPT baseline:** 2021. 2020 is excluded from trajectory fits — it has roughly 2× the within-year citation density of other years, concentrated entirely in the upper tail and driven by the COVID-era Medicine cohort. Including it would falsely make any normal year look like a decline.
- **Buffer:** 2022. ChatGPT launched on November 30, 2022; papers published in 2022 were largely written and submitted before its launch.
- **Post-ChatGPT:** 2023–2024.

### 4.2 Detecting mutual pairs

A mutual pair is detected by joining the `citations` table to itself on the symmetric condition `a.citing_id = b.cited_id AND a.cited_id = b.citing_id`. A naive form of this query (a) counts every self-citation as a mutual pair, since the join matches `(X → X)` against itself, and (b) returns each true mutual pair `{X, Y}` twice. We resolve both with a single filter — `WHERE a.citing_id < a.cited_id` — which excludes self-cites and uniquely orders each unordered pair. All numbers in this paper use the corrected query.

### 4.3 Why mutual citations are a fair metric across years

A paper's reference list is fixed at the moment of publication; authors cannot retroactively add references. So for any two already-published papers, the mutual citation between them either exists or it doesn't, and waiting another year cannot create new mutual pairs between papers that already exist. Comparing 2024 to 2021 on this metric is therefore fair in a way that comparing them on inbound citation counts is not (a 2024 paper has been in print for ~12 months while a 2021 paper has had four-plus years to accumulate).

### 4.4 Statistical tools

For testing whether the mutual rate differs between two periods, we use a **chi-square test of independence** on a per-paper Bernoulli table: of papers from period P, what fraction participate in at least one mutual pair? Each paper is one independent trial.

To distinguish a step-change at a specific date from a continuing pre-existing trend, we fit a **trajectory model** — a straight line through the logarithm of yearly rates — and ask where each year sits relative to the line. The **R²** statistic gives the fraction of variation the line explains.

For finer temporal resolution we use the **Chow test**, which compares the fit of a single line across the whole series against the fit of two lines (one before, one after a candidate breakpoint). The reported F-statistic and p-value test whether the two-line fit is significantly better than the one-line fit.

For cross-field comparisons we use **difference-in-differences**, which compares the pre-to-post change in a treated group to the pre-to-post change in a control group. The estimator is valid causally only if the two groups were trending in parallel before treatment.

For citation breadth (the central finding) we compute, for each citing paper, the number of *distinct* OpenAlex fields that appear among its references, then average across all citing papers within a year cohort.

## 5. Results

We report the analyses in roughly the order they were performed. The early results (§5.1–5.3) constrained but did not falsify the original hypothesis; §5.4 tested it at monthly resolution and produced what initially looked like a positive result, which §5.5 showed was artifactual; §5.6 surfaced a methodological surprise (sample composition drift); §5.7 confirmed the citation-age finding was an artifact; and §5.8 is the central positive finding.

### 5.1 The aggregate mutual citation rate declined steadily

| Year | Mutual pairs | Papers | Pairs per 1000 |
|------|-------------:|-------:|---------------:|
| 2020 | 3,010 | 202,323 | 14.88 *(COVID outlier)* |
| 2021 | 2,550 | 201,597 | 12.65 |
| 2022 | 1,989 | 200,102 |  9.94 |
| 2023 | 1,806 | 200,063 |  9.03 |
| 2024 | 1,631 | 200,227 |  8.15 |

Taking 2021 as baseline and 2023–2024 as post-ChatGPT, the per-paper Bernoulli chi-square gives χ² = 604.20, p ≈ 0 — a nominally striking decline. But at n ≈ 400,000 the chi-square test would call almost any non-zero difference significant; the p-value here reflects sample size more than effect strength.

### 5.2 No ChatGPT break at yearly resolution

Fitting `log(rate) = a + b · year` to the 2021–2024 yearly rates gives an annualized decline of **−13.2%/yr** (R² = 0.944, slope p = 0.028). Post-ChatGPT years sit essentially on the line implied by the pre-ChatGPT data (residuals: 2023 −0.012, 2024 +0.027). The largest single-year drop is **2021 → 2022 (−21.4%)**, before ChatGPT existed. The post-ChatGPT slope (−10.3%/yr) is actually *shallower* than the pre-ChatGPT slope (−21.4%/yr).

A high R² on four data points should not be read as strong evidence for a single trend — four monotone points fit a line by construction. The right interpretation is that this test can rule out a *large* discontinuity at ChatGPT (which we don't see) but cannot rule out a small effect riding the existing trend.

### 5.3 Year-gap stratification: same-year pairs fail the hypothesis even on its home turf

If ChatGPT compressed contemporaneous peer discovery, the cleanest prediction is on same-year mutual pairs. Restricting both papers to 2020–2024 and fitting log-trajectories on 2021–2024:

| Stratum | Annual change | R² |
|---------|--------------:|---:|
| All gaps | −13.2%/yr | 0.94 |
| **gap = 0 (same year)** | **−10.9%/yr** | 0.92 |
| gap = 1 (one year apart) | −23.9%/yr | 0.85 |

Same-year pairs — the precise axis the hypothesis predicts should rise — decline smoothly at −11%/yr with post-ChatGPT residuals essentially zero (+0.027 and +0.004). The hypothesis fails even on its strongest possible axis. The aggregate decline is driven by lagged pairs, not by contemporaneous discovery breaking down.

### 5.4 Monthly resolution: an apparent ChatGPT break

The yearly trajectory has only four data points and limited power against a small effect. We backfilled monthly publication dates for the ~16,000 mutual-pair papers and ran a Chow test at the ChatGPT cutoff (Dec 2022). The result looked striking:

- Aggregate monthly trend (2021-01 to 2024-06): −12.0%/yr, R² = 0.18, slope p = 0.005.
- Chow test at Dec 2022: F = 3.97, **p = 0.027**.
- Pre slope: **−26.5%/yr**. Post slope: **+16.6%/yr**. Sign flip.

Robustness checks were mixed: the break survived deseasonalization (in fact got stronger, p = 0.0055), but was sensitive to censoring choice (present at 6- and 9-month tail censoring, absent at 3- and 12-month). Before claiming this as a ChatGPT effect we ran two specificity tests.

### 5.5 Placebo testing: the monthly break is a Dec 2022 outlier artifact

We swept every candidate break date that leaves at least six months on each side. The result is unambiguous:

- **23 of 30 candidate break dates** show p < 0.05.
- ChatGPT's date ranks **9th** by F-statistic. Jan 2022 (F=5.06, p=0.011) and Jan 2023 (F=5.02, p=0.012) are stronger "breaks."

The Chow test is firing essentially everywhere on this series.

We then noticed Dec 2022 is the **single lowest-rate month in the entire dataset** (rate 4.50/1000; surrounding months 7.86–9.78 per 1000). Removing only this one month from the analysis drops the ChatGPT-date Chow result from p = 0.027 to **p = 0.081 (no break)**, and the post-ChatGPT slope collapses from +16.6%/yr to **+1.7%/yr**.

The "break" was a conjunction of (a) Dec 2022 being the single deepest seasonal dip, (b) Jan 2023 being seasonally elevated (every January is the seasonal peak), and (c) the Chow test having low specificity on a noisy 42-point series with strong seasonality. This is a general lesson: **Chow tests on small-*n* monthly series should always be paired with a placebo sweep before claiming a break.**

### 5.6 Aside: OpenAlex sample composition drift

While running per-field analyses we discovered a substantial confound. Field paper counts in our 200k-per-year sample shift in ways that are not real-world plausible:

| Field | 2020 | 2021 | 2022 | 2023 | 2024 | Change |
|-------|-----:|-----:|-----:|-----:|-----:|-------:|
| Mathematics | 2,163 | 1,307 | 722 | 582 | 492 | **−77%** |
| Psychology | 6,769 | 5,673 | 4,130 | 3,328 | 3,019 | **−55%** |
| Social Sciences | 9,834 | 9,063 | 7,214 | 5,945 | 5,188 | **−47%** |
| Engineering | 31,687 | 34,983 | 38,786 | 41,378 | 45,380 | **+43%** |
| Chemical Engineering | 1,010 | 1,140 | 1,322 | 1,460 | 1,680 | **+66%** |

Total papers per year is constant by construction. The mix changes because 2020–2023 papers were ingested mostly via the OpenAlex S3 snapshot and 2024 papers via the API; the two pipelines surface different field distributions. Mathematics losing 77% of its papers is not a real phenomenon.

**Any per-field comparison on this data is contaminated.** To check whether the aggregate decline survives, we restricted to fifteen fields with stable or growing sample populations across the window (excluding Math, Psychology, Social Sciences, Medicine, and others). On this restricted set, the aggregate trajectory is *steeper* than on the full sample: **−19.3%/yr, R² = 0.90**, p = 0.054. The decline is not an artifact of the disappearing fields. It is real and pervasive.

A within-vs-between field decomposition (counterfactual: fix 2021 field rates, use 2024 composition) shows the aggregate decline is essentially entirely within-field. Only ~14% is attributable to composition shift; ~94% is within-field rate change. (The numbers sum to over 100% because of an interaction term.) Whatever is driving the secular decline, it is acting *within* fields, not shifting the mix of papers between them.

### 5.7 Citation age was an artifact (excluded)

An earlier preliminary finding — that the average age of cited papers tripled from 2020 to 2024 — does not hold up under inspection. For every citing year, 99.5–100% of matched citations land on papers in the dense 2020–2024 region of the works table, because pre-2020 coverage is too sparse. The metric therefore mechanically measures *how many years of the dense region are reachable backward from the citing year*, which grows monotonically by construction. The trajectory we observed (0.09 → 2.33 years) is exactly what this constraint produces regardless of behavior. We exclude this finding.

### 5.8 Citation breadth has nearly doubled

The central positive finding of this paper. For each citing paper, we compute the number of *distinct* OpenAlex fields appearing among its references, then average within each year cohort. The trend is monotone and large:

| Year | Citing papers | Avg distinct cited fields | Median | Cross-field cite share |
|------|--------------:|--------------------------:|-------:|-----------------------:|
| 2020 |  94,173 | **1.66** | 1 | 28.6% |
| 2021 | 169,887 | 2.06 | 2 | 31.1% |
| 2022 | 187,584 | 2.42 | 2 | 31.5% |
| 2023 | 192,650 | 2.78 | 2 | 33.0% |
| 2024 | 193,530 | **3.11** | 3 | 35.0% |

The average paper in 2024 cites work from **3.11 distinct fields**, up from 1.66 in 2020 — a factor of **1.88**. The median rose from 1 to 3. Total references per paper is essentially flat across years (~85 refs/paper; range 76 to 85). Papers are not citing more *total* work; they are spreading the same budget more broadly.

**Robustness to the sample-composition confound.** The same exercise restricted to the 15 stable-volume fields gives 1.50 → 3.13 (×2.08). Restricted to Computer Science papers alone — a single field, classification-anchored, large enough for a clean estimate — it gives 1.44 → 2.92 (×2.02). The doubling appears in every cleaner subset we try.

**Trend shape.** The year-over-year growth rate is *decelerating* (+24.5% → +17.1% → +14.9% → +12.1%), opposite to what a discrete ChatGPT-driven discontinuity would produce. The trend was already running steeply before ChatGPT existed and is not attributable to it. It is a longer-running shift in citation behavior, plausibly driven by improved cross-field search tools, rising interdisciplinarity in research, and the general accumulation of citation infrastructure.

**Quantitative link to the mutual citation decline.** If each paper's citation budget is now spread across roughly twice as many fields, the average citation density within any single field roughly halves. Mutual pair formation between two same-field papers requires both papers to spend reference budget on each other; halving the within-field budget per paper roughly squares to a quarter of the mutual pair probability under a simple independent-citation model. The observed mutual rate dropped 53% over the same window — substantial but less than the squared-density prediction, which is consistent with imperfect independence and the lag-tolerance of mutual pairs across years.

This is the most coherent mechanistic explanation we found for the secular decline, and it is robust to the artifacts that defeated the other candidates we tested.

### 5.9 Mechanisms we ruled out

The full inventory of candidate mechanisms tested and eliminated:

- **ChatGPT step-change.** Yearly trajectory (§5.2): no break. Monthly Chow with placebo testing (§5.5): no specific break.
- **Paper volume / quality dilution.** Paper counts are flat (−0.4% pre vs. post). The 72% drop in raw inbound citations per paper is citation lag, not behavior. Mutual citations, which are immune to citation lag, drop only 27% — a sharper test that still falsifies the volume story.
- **Citation lag.** Mutual citations are immune by construction; the metric is fair across years.
- **Preprint deduplication** as a cause of the forward-citation collapse. Forward citations are 78% article→article and only 3% preprint-touching; preprint-heavy fields decline *slower*, not faster.
- **Citation concentration (Matthew effect).** Gini moves only modestly (0.519 → 0.557 between 2021 and 2023; 2024 is contaminated by citation lag). Not enough magnitude to explain a 53% mutual decline.
- **Field composition shift.** Within-vs-between decomposition attributes only ~14% to composition. The aggregate decline survives restriction to stable-volume fields.

What remains is the citation-breadth mechanism in §5.8.

## 6. Discussion

The original ChatGPT hypothesis is not supported by this data. Mutual citation rates declined across our window, but the decline started before ChatGPT existed, follows a smooth trajectory across its launch, and fails its strongest sub-test (same-year pairs) too. The monthly-resolution test that initially looked positive turned out to be a placebo-level Chow artifact.

But the path to that null result surfaced a substantive finding. Citation patterns in the OpenAlex 2020–2024 record are broadening at a striking rate. The average paper cites work from nearly twice as many fields as it did four years ago, on the same flat reference budget. This is a real, large, monotone, multiply-robust phenomenon that almost no current bibliometric narrative about science publishing centers on, and it is — for now — the most parsimonious explanation we can identify for the substantial secular decline in mutual citations.

A few points worth emphasizing.

**Mutual citations are downstream of breadth, mechanically.** Spreading the same number of references across more fields lowers within-field citation density. Within-field density is what supports mutual pair formation. The two phenomena are not independent; they are causally linked by simple arithmetic once you accept that the total reference budget is flat.

**The breadth expansion is not a ChatGPT effect.** The trend predates ChatGPT and is decelerating, not accelerating. If it has a single causal driver, that driver is something that has been operating for at least the 2020–2022 pre-ChatGPT period — candidates include search tools (Google Scholar, Semantic Scholar), the institutional rise of interdisciplinarity, and improving cross-field linkage in citation databases themselves. None of these are testable with the data we have, and we make no claim about which is correct.

**Mutual citation as a proxy for the original hypothesis was narrower than ideal.** The breadth metric is much closer to what "compressed peer discovery" actually predicts. The fact that this metric *is* rising substantially — but at a steady pre-existing rate with no discontinuity at ChatGPT — is the cleanest answer we have to the broader version of the original question. Citation behavior is changing rapidly in the direction the hypothesis predicted, but the change is not specifically attributable to ChatGPT.

**Methodological notes that generalize.** Three observations from the project that apply beyond it:

- At industrial sample sizes, statistical significance is cheap. At n ≈ 400,000 the chi-square test calls a 0.5% absolute difference significant. The first-pass result (p ≈ 0) reflected sample size, not effect strength.
- At very small n the symmetric trap applies to fit quality. R² = 0.94 on four points is structural, not evidential. Any monotone sequence will fit a line.
- Chow tests on noisy monthly series with seasonality fire indiscriminately. In our data, 77% of candidate break dates were "significant" at p < 0.05; the ChatGPT date ranked 9th by F-statistic. Always run a placebo sweep.

## 7. Limitations

- **Single dataset.** All results depend on OpenAlex's coverage, dating semantics, and topic classification. The citation-age artifact and the sample-composition drift both originate in the dataset rather than in the analysis. Replication against Semantic Scholar, Crossref, or Web of Science would substantially strengthen any claim, particularly the breadth finding.
- **Field labels are coarse.** OpenAlex's ~27 top-level fields lump together subfields with very different citation cultures. The breadth metric counts distinct top-level fields, so increases reflect genuine cross-discipline spread rather than within-field topic mobility. A finer-grained version (using OpenAlex topics or concepts) would be more sensitive but also more sensitive to classification drift.
- **The link between breadth and the mutual decline is mechanistic, not causal.** We argue the two are quantitatively compatible under simple independence assumptions, but we have not directly demonstrated that the breadth expansion *causes* the mutual decline. A within-paper instrumental analysis would be needed to establish that.
- **The pre-2024 vs 2024 ingestion split** (S3 snapshot vs API) is a confound for any cross-year comparison, but the breadth finding is robust to restricting the analysis to a single ingestion-stable field (Computer Science) and to a basket of stable-volume fields.
- **Two post-ChatGPT years is thin.** Papers whose writing was substantially shaped by ChatGPT — given typical submission and review lag — would mostly be 2024 papers at the earliest, with many appearing in 2025+. A small ChatGPT effect riding on top of the breadth trend cannot be ruled out from this data.

## 8. Future Work

Four follow-up questions emerge naturally from the findings.

1. **Replicate the breadth expansion in an independent citation graph.** Semantic Scholar and Crossref both expose citation data with different ingestion histories. If the doubling appears in both, it is a real characteristic of scientific publishing in this period, not an OpenAlex artifact.
2. **Identify the driver of breadth expansion.** Three candidate explanations stand out: better search/discovery tools, institutional pressure toward interdisciplinarity, and citation-database infrastructure improvements that surface more cross-field links. Each predicts a different starting date and different field-level signatures.
3. **Test whether the breadth-mutual link is causal at the paper level.** For each paper, do papers with higher breadth participate in fewer mutual pairs, controlling for field, year, and citation count? A within-paper test would confirm the mechanism implied by §5.8.
4. **Resolve the forward-citation collapse.** Forward (cited_year > citing_year) citations decline at roughly −18%/yr in this dataset, and the preprint-deduplication mechanism we initially hypothesized for this was refuted in §5.9. The cause is now unknown and is the second-largest unexplained signal in our analysis.

## 9. Conclusion

We tested a specific hypothesis about ChatGPT and mutual citations. The hypothesis is not supported by this data, at either yearly or monthly resolution; the apparent monthly break failed a placebo test. But the investigation led to a finding we did not expect and that is, on its own, larger and more substantively interesting than the original question: the average paper in our 2024 cohort cites work from nearly twice as many distinct fields as the average paper in our 2020 cohort, on the same flat reference budget, with a trend that is monotone, decelerating, and predates ChatGPT. This broadening provides a clean mechanistic account of the secular decline in mutual citation rates that we initially mistook for a ChatGPT effect, and it points to a longer-running and probably more consequential shift in how scientific work is being cited than any single technology release would explain.
