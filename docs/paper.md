# Mutual Citations After ChatGPT: A Hypothesis That Does Not Survive Trajectory Testing

## Abstract

ChatGPT, released in November 2022, plausibly compressed the process by which researchers discover and extract specific information from each other's work. If so, we should see this change reflected in the citation graph — in particular, in the rate of *mutual citations*, the unusual case where two papers cite each other. We test this hypothesis using ~1M papers from OpenAlex spanning 2020–2024. A first-pass test finds a large, statistically significant decline in mutual citation rate after ChatGPT, but this turns out to reflect a continuing pre-existing trend rather than any change at ChatGPT's launch. We confirm this with five additional checks: a trajectory fit (R² = 0.94, post-ChatGPT years sit on the pre-existing trend line), a cross-field difference-in-differences, a paper-volume control, a year-gap stratification that tests the hypothesis on its strongest predicted axis (same-year mutual pairs), and a forward-citation validity check that traces part of the decline to a likely artifact of preprint dating semantics in OpenAlex. The hypothesis as written — that ChatGPT *increased* mutual citation rates — is not supported. The broader question of whether ChatGPT changed citation behavior at all in smaller ways remains open and would require finer temporal resolution to test.

## 1. Introduction

When ChatGPT was released to the public in November 2022, it changed how many researchers interact with the scientific literature. Instead of reading a paper end-to-end to extract a single claim, researchers can now ask a language model for the relevant passage. This plausibly compresses the front end of the research process — finding, filtering, and extracting from prior work — in a way that could leave a measurable fingerprint on what people cite.

This paper tests one specific prediction of that hypothesis: that *mutual citations* — where paper A cites paper B and paper B cites paper A — should have risen after ChatGPT.

Mutual citations are structurally rare. For one to exist, both authors must have been aware of each other's work at the time of writing, and each must have decided to cite it. Before ChatGPT, the cost of discovering and absorbing a recent or in-progress paper from another group was high enough that mutual citations were unusual. If ChatGPT really did compress that discovery process — surfacing relevant recent work faster, extracting the salient claim without requiring a full read — then citation loops that would not previously have formed should start forming. Mutual citation rate per 1000 papers is the natural quantity to look at.

We find that this prediction is not borne out. Mutual citation rates declined after ChatGPT, but the decline started *before* ChatGPT existed and continued smoothly through and after its launch. We rule out the most obvious alternative explanations (paper volume, citation lag, field composition), and we show that even on the axis the hypothesis cares about most — same-year mutual pairs, where compressed peer discovery should matter most — there is no break at ChatGPT.

The contribution of this paper is therefore a clean null result on a specific testable mechanism, together with a methodological note: at this sample size, a binary pre/post statistical test will declare almost any pre-existing trend "significant," which is easy to mistake for a causal effect.

## 2. Hypothesis and Definitions

We test the following hypothesis:

> Mutual citation rate per 1000 papers increased after November 2022, beyond what would be expected from changes in paper volume alone.

A few definitions that recur throughout:

- A **citation graph** is a directed network of papers. An edge from paper A to paper B means A's reference list contains B.
- A **mutual citation** (or *mutual pair*) is the case where both A → B and B → A are present.
- A **self-citation** is an edge from a paper to itself (an artifact in our raw data; excluded).

The hypothesis predicts a *rate* increase, not just a count increase, because the total number of papers published each year fluctuates. We normalize throughout to "mutual pairs per 1000 papers," and separately check that paper volume itself is roughly flat in the period studied.

## 3. Data

All data comes from [OpenAlex](https://openalex.org/), a public bibliographic database. We use two ingestion paths:

1. The OpenAlex S3 snapshot ([data/citation_parser.py](../data/citation_parser.py)) — used for older papers and for full-snapshot coverage. The S3 snapshot has no publication-year filter, so it contributes papers from any year present in the snapshot.
2. The OpenAlex API ([data/api_ingest.py](../data/api_ingest.py)) — used to top up 2020–2024 coverage.

Both ingesters write to the same `works` and `citations` tables in a single DuckDB database. For each paper we store an ID, title, publication year, and field; for each citation, the citing and cited paper IDs. Duplicates are removed by [data/deduplicate.py](../data/deduplicate.py). The resulting dataset contains approximately 200,000 papers for each year from 2020 through 2024 — a deliberately flat denominator that simplifies year-over-year comparisons.

Pre-2020 coverage in the works table is sparse. This becomes important in §5.8: pre-2020 cited papers usually fail to find a JOIN match because the citing paper's reference is not in the works table. This is a limitation of the snapshot, not of our analysis pipeline.

In a separate pass ([data/backfill_dates.py](../data/backfill_dates.py)), full ISO publication dates and paper types were added for the ~16,000 papers that participate in any mutual pair during 2020–2024. This sets up monthly-resolution analyses that are listed under Future Work; the analyses presented in this paper use yearly resolution.

## 4. Methods

### 4.1 Time windows

- **Pre-ChatGPT baseline:** 2021. 2020 is excluded (see §5.4).
- **Buffer:** 2022. ChatGPT launched on November 30, 2022, so papers published in 2022 were largely written and submitted before its launch.
- **Post-ChatGPT:** 2023–2024.

### 4.2 Detecting mutual pairs

A mutual pair is detected by joining the `citations` table to itself on the condition that one row's citing paper equals another row's cited paper, and vice versa. The naive form of this query has two well-known bugs that affected our earliest analyses (see [research_notes.md](research_notes.md) for the full history):

1. Without an additional filter, every self-citation matches itself and is counted as a "mutual pair."
2. Even without self-citations, each true mutual pair `{X, Y}` is returned *twice* — once as (X→Y, Y→X) and once as (Y→X, X→Y) — so all counts are doubled.

We resolve both with a single filter: `WHERE a.citing_id < a.cited_id`. Comparing the two IDs as strings excludes self-cites (because X < X is false) and uniquely orders each unordered pair (because exactly one of X < Y or Y < X is true). All numbers in this paper use this corrected query.

### 4.3 Why mutual citations are a fair metric across years

A common concern in citation analyses is that recent papers haven't had time to accumulate citations yet. A 2024 paper has been in print for ~12 months; a 2021 paper has been in print for over four years. Raw "citations received per paper" is therefore biased downward for recent years.

Mutual citations are immune to this. A paper's reference list is fixed at the moment of publication — authors cannot retroactively add references. So for any two already-published papers, the mutual citation between them either exists or it doesn't, and waiting another year cannot create new mutual pairs between papers that already exist. Comparing 2024 to 2021 on this metric is fair in a way that comparing them on inbound citations is not.

This is the central methodological reason mutual citations are the right axis for testing what we want to test.

### 4.4 Statistical approach

The first-pass test is a **chi-square test of independence**, a standard tool for checking whether the rate of an event differs between two groups. In our case, we ask: of papers from the pre-ChatGPT period, what fraction participate in at least one mutual pair? Of papers from the post-ChatGPT period, what fraction? Each paper is one independent trial (a Bernoulli outcome — "in a mutual pair" or "not"), so the test is well-defined.

Where the first-pass test is informative about *whether* the rates differ, it cannot distinguish a step-change at ChatGPT's launch from a pre-existing trend that happened to be running through the same period. For that, we fit a **trajectory model**: a straight line through the logarithm of yearly rates, which corresponds to assuming the rate follows an exponential decay (or growth) curve. The slope gives an annualized percentage change; the **R²** statistic, between 0 and 1, gives the fraction of year-to-year variation the line explains. We then ask where each year sits relative to that line: post-ChatGPT years substantially below the line would be evidence of a ChatGPT-driven acceleration; on or above the line is evidence the existing trend continued unbroken.

For cross-field comparisons we use **difference-in-differences** (DiD): we compare the pre-to-post change in a "treated" group (here, a high ChatGPT-exposure field) to the pre-to-post change in a "control" group (low-exposure fields). The DiD estimate is the difference between those two changes. It is valid as a causal estimate only if the two groups were trending in parallel *before* the treatment — a condition we test explicitly in §5.7.

## 5. Results

### 5.1 Per-year mutual citation rates

Across 2020–2024, mutual citation rates declined steadily:

| Year | Mutual pairs | Papers | Pairs per 1000 |
|------|-------------:|-------:|---------------:|
| 2020 | 3,010 | 202,323 | 14.88 |
| 2021 | 2,550 | 201,597 | 12.65 |
| 2022 | 1,989 | 200,102 |  9.94 |
| 2023 | 1,806 | 200,063 |  9.03 |
| 2024 | 1,631 | 200,227 |  8.15 |

The pattern is monotone: every year is lower than the one before, with no obvious discontinuity at the ChatGPT release.

### 5.2 First-pass test and why we questioned it

Taking 2021 as the baseline (see §5.4 for why 2020 is excluded) and 2023–2024 as the post-ChatGPT period, the chi-square test on per-paper participation in mutual pairs gives:

- Pre-ChatGPT (2021): 3,786 of 201,597 papers → 18.78 per 1000.
- Post-ChatGPT (2023–2024): 4,403 of 400,290 papers → 10.99 per 1000.
- Chi-square statistic: 604.20, **p ≈ 0**.

A 41% drop and a p-value indistinguishable from zero. By the usual reporting conventions this looks like a striking, statistically significant decline.

It is also misleading. With sample sizes of ~400,000 per group, a chi-square test will return p < 0.001 on any difference of even a fraction of a percentage point. The *p-value at this scale is not evidence of a meaningful effect* — it is mostly evidence that the sample is large. What we actually want to know is whether the change reflects a behavior shift at the right time. For that we need the trajectory.

### 5.3 The decline is pre-existing

Fitting `log(rate) = a + b · year` to the four post-2020 yearly rates ([research/trajectory.py](../research/trajectory.py)) gives:

- Annualized rate of change: **−13.2% per year**.
- R² = 0.944 (one trend line explains 94% of the variation across years).
- Slope p-value: 0.028.

The fit is tight, and the post-ChatGPT years sit essentially on the pre-existing line:

| Year | Observed | Trend predicts | Residual (log) |
|------|---------:|---------------:|---------------:|
| 2021 | 12.65 | 12.13 | +0.042 |
| 2022 |  9.94 | 10.53 | **−0.057** (biggest deviation — pre-ChatGPT) |
| 2023 |  9.03 |  9.14 | −0.012 |
| 2024 |  8.15 |  7.93 | +0.027 |

The largest single-year drop in the entire window is **2021 → 2022, a 21.4% decline** — and 2022 papers were written and submitted before ChatGPT existed. The two post-ChatGPT years move at roughly half the rate of that pre-ChatGPT drop. Comparing the slopes directly:

- Pre-ChatGPT slope (log-rate from 2021 to 2022): −0.241.
- Post-ChatGPT slope (log-rate from 2023 to 2024): −0.103.

The decline is *decelerating* after ChatGPT, not accelerating. If ChatGPT had caused a meaningful break in citation behavior, we would expect the post-ChatGPT years to fall notably below the pre-existing trend. They do not.

### 5.4 The 2020 outlier

2020 was excluded from the trajectory fit above. The per-paper distribution of within-year citations shows it is a clear outlier:

| Year | Avg within-year refs/paper | Median | 95th percentile | Max |
|------|---------------------------:|-------:|---------------:|----:|
| **2020** | **5.46** | 2 | **20** | **244** |
| 2021 | 3.19 | 2 | 10 | 139 |
| 2022 | 3.05 | 2 |  9 |  88 |
| 2023 | 3.20 | 2 | 10 | 127 |
| 2024 | 3.43 | 2 | 11 | 118 |

2020 has roughly twice the within-year citation density of any other year, concentrated in the upper tail (the median is the same as every other year). This is consistent with COVID-era research clustering — large groups of medical and epidemiological papers published in rapid waves, citing each other heavily within months.

It is not consistent with an ingestion artifact: neither ingestion path filters by year, the average outgoing reference count for 2020 papers is *lower* (78.6) than for other years (~86), and only the top fields most associated with COVID research (Medicine in particular) show a 2020-specific inflation.

Including 2020 in the baseline would make any normal year look like a "decline." The 2021 baseline is the conservative choice.

### 5.5 Paper volume and citability are not driving the rate drop

A natural concern is whether recent years simply contain more papers, or lower-quality papers that nobody cites, so the per-paper rate falls mechanically. We check this directly ([research/did_volume_check.py](../research/did_volume_check.py)):

| Period | Papers | Avg citations received per paper | Avg mutual pair memberships per paper |
|--------|-------:|--------------------------------:|--------------------------------------:|
| Pre (2021–2022)  | 401,699 | 13.17 | 0.0215 |
| Post (2023–2024) | 400,290 |  3.64 | 0.0157 |
| Change | −0.4% | −72.3% | −27.1% |

Three things are visible here. First, **paper volume is essentially flat (−0.4%)** — there is no paper-count explosion to mechanically deflate per-paper rates.

Second, the huge drop in raw inbound citations per paper (−72%) is the citation-lag artifact discussed in §4.3: 2024 papers have been in print for one year, 2021 papers for four. This is exactly the reason raw citations cannot be used as a behavior metric across this time window.

Third, **mutual citations only fall 27% rather than 72%** — almost three times more resistant to citation lag — because, as established in §4.3, mutual pairs between already-published papers cannot grow over time. This is the empirical justification for using mutual citations as the metric.

### 5.6 Cross-field difference-in-differences (inconclusive)

A different test of the hypothesis: if ChatGPT really changed citation behavior, it should have affected ChatGPT-exposed fields more than fields where LLMs barely touch the workflow. We compare:

- **HIGH exposure:** Computer Science (ChatGPT *is* research about and within CS).
- **LOW exposure:** Chemistry, Materials Science, Agricultural and Biological Sciences, Earth and Planetary Sciences, Immunology and Microbiology — empirical / wet-lab / field-data disciplines where ChatGPT changes day-to-day work much less.

Per-year mutual citation rates ([research/did_analysis.py](../research/did_analysis.py)):

| Year | HIGH (CS) | LOW (5 fields) |
|------|----------:|---------------:|
| 2021 | 32.59 | 10.93 |
| 2022 | 29.98 |  7.32 |
| 2023 | 31.28 |  6.21 |
| 2024 | 19.37 |  3.58 |

The pre/post DiD:

- HIGH change (2021–22 → 2023–24): 31.25 → 25.33 per 1000 = **−18.9%**.
- LOW change  (2021–22 → 2023–24):  9.09 →  4.86 per 1000 = **−46.5%**.
- DiD on log rates: **+0.416** (SE 0.083, z = +5.02, p < 0.0001).

Read at face value, this is the signature of a *positive* treatment effect: CS dropped 19% when the no-ChatGPT counterfactual implied by LOW suggests it "should have" dropped 47%. The point estimate is directionally consistent with the hypothesis.

But it does not survive a check on the pre-trends. Difference-in-differences only identifies a causal effect if the two groups were on parallel trajectories before the treatment. Looking only at the two pre-ChatGPT years:

- HIGH log change 2021 → 2022: log(29.98 / 32.59) = −0.083.
- LOW log change  2021 → 2022: log(7.32 / 10.93) = **−0.401**.

Before ChatGPT existed, HIGH was already declining ~0.32 log-units per year slower than LOW. That pre-existing gap is roughly the same size as the +0.416 "treatment effect" DiD attributes to the post-period. In other words, the apparent ChatGPT effect is what you would predict by extrapolating the pre-existing field-level pattern with no ChatGPT at all.

DiD is therefore **inconclusive** rather than supportive: the point estimate is compatible with a real ChatGPT lift in exposed fields, but also compatible with "CS and empirical fields decline at different rates for unrelated reasons, and that pre-existing pattern continued." Non-parallel pre-trends mean DiD cannot separate the two stories.

### 5.7 Year-gap stratification: testing the hypothesis on its strongest axis

The hypothesis's specific mechanism — compressed peer discovery — predicts an increase in *contemporaneous* mutual citations: pairs of papers published in the same year that find and cite each other very quickly. The aggregate mutual rate pools all year-gaps together, which could in principle wash out a real effect concentrated in same-year pairs. We test this directly ([research/year_gap_analysis.py](../research/year_gap_analysis.py)).

For each mutual pair, define `gap = |year_A − year_B|`. Restricting both papers to 2020–2024 and fitting log-trajectories over 2021–2024:

| Stratum | Annual change | R² | Slope p |
|---------|--------------:|---:|--------:|
| Aggregate (all gaps) | −13.2%/yr | 0.94 | 0.028 |
| **gap = 0 (same-year)** | **−10.9%/yr** | 0.92 | 0.043 |
| gap = 1 (one year apart) | −23.9%/yr | 0.85 | 0.078 |

Two things stand out. First, **the aggregate decline is driven by lagged (one-year-apart) pairs, not by same-year pairs**. Same-year pairs decline at less than half the rate of lagged pairs.

Second, and more importantly: **same-year pairs — the exact axis the hypothesis cares about most — also show no break at ChatGPT**. Post-ChatGPT residuals on the gap = 0 trend are +0.027 (2023) and +0.004 (2024). Essentially zero. The hypothesis fails even on its strongest predicted axis.

### 5.8 Forward-citation validity check

The much steeper decline in gap = 1 pairs raised a structural question. A gap = 1 mutual pair requires one "normal" citation (the later paper citing the earlier one) and one *forward* citation — the earlier paper citing the later one. Forward citations are unusual: they're only possible if the earlier paper's authors saw the later paper as a preprint (a working draft posted publicly before formal publication) and added a citation late in the editorial cycle.

If forward citations across the entire citation graph — not just within mutual pairs — are collapsing on their own, then the gap = 1 mutual decline would be inherited from a broader shift rather than a story specifically about mutual reciprocity. We check this ([research/forward_citation_check.py](../research/forward_citation_check.py)).

Forward "+1" citations (an earlier paper citing a paper published one year later) per 1000 citing-year papers:

| citing year | 2020 | 2021 | 2022 | 2023 |
|-------------|-----:|-----:|-----:|-----:|
| rate | 42.1 *(COVID)* | 24.7 | 25.1 | 16.6 |

A three-point fit on 2021–2023 gives roughly −18%/yr. The gap = 1 mutual trajectory aligned to the same citing-years gives roughly −15%/yr. These are comparable. Meanwhile same-year citations are flat (−0.5%/yr) and ordinary backward citations decline only modestly (−4.6%/yr). What's collapsing fast is *forward citing specifically*.

The most plausible mechanism is not a behavioral one. OpenAlex deduplicates preprint versions of a paper into their formal-publication record over time. If that deduplication process has become more aggressive in recent years, or if preprints reach formal publication faster, the apparent "forward citation" — citing-year X to cited-year X+1 — would mechanically disappear: the preprint's date would get rewritten to match the journal version, and the citation would no longer span a year boundary. This would not be a citation-behavior change; it would be a dating-pipeline change inside the dataset.

In short: **the gap = 1 mutual decline is largely inherited from a broader forward-citation collapse, which itself is most plausibly explained by changes in how OpenAlex assigns dates to preprints rather than by any behavior shift**. This further constrains what the aggregate decline can be telling us about citation behavior.

### 5.9 Excluded: citation age as a behavioral signal

Earlier in this project a striking secondary finding appeared: the average age of cited papers (`citing_year − cited_year`) appeared to rise sharply over the window, from 0.09 years in 2020 to 2.33 years in 2024. Interpreted naively this looks like researchers shifting from peer literature toward established older work.

This finding does not survive inspection ([research/citation_age.py](../research/citation_age.py)). For every citing year in our data, 99.5 to 100% of matched citations land on papers in the dense 2020–2024 region of the works table — because pre-2020 coverage is too sparse for most pre-2020 citations to find a JOIN match. The metric therefore effectively measures *how many years of the dense region are reachable backward from the citing year*, which grows monotonically by construction:

- 2020 can only match 2020 → max possible age 0.
- 2021 can match 2020–2021 → max possible age 1.
- 2024 can match 2020–2024 → max possible age 4.

The observed shape would emerge from *any* citation behavior, including one in which every paper cites uniformly across all available years. The metric is mechanically constrained by the width of the dense region, not by behavior. We exclude it from our conclusions.

## 6. Discussion

The hypothesis tested in this paper is specific: ChatGPT caused mutual citations to *increase* after November 2022. That hypothesis is not supported. Mutual citation rates declined across our window, but the decline began before ChatGPT existed, follows a single smooth trend through and after its launch, and shows no break — including on the same-year subset where the hypothesized mechanism (compressed peer discovery) should be strongest.

A weaker version of the question — *did ChatGPT change citation behavior at all?* — is harder to answer with this data. The trajectory test has only four yearly data points and therefore very limited statistical power against an effect smaller than the year-to-year noise. We cannot exclude a modest ChatGPT effect riding on top of the larger pre-existing trend, an effect concentrated in a sub-annual window, or an effect on dimensions we did not measure (citation novelty, cross-field reach, semantic similarity). What we *can* say is that the data we have is fully consistent with no ChatGPT effect at all in the mutual citation axis, and inconsistent with the specific large effect the original hypothesis predicted.

Several methodological points generalize beyond this study:

**Sample size makes p-values misleading.** At n ≈ 400,000 the chi-square test would call a 0.5% absolute difference statistically significant. p ≈ 0 was the first thing we observed, and on its own it pointed in the wrong direction. The trajectory test — fitting a line through per-year rates, then asking where each year sits relative to the line — is what distinguished a real signal at the right time from a real signal that predates the cause.

**Counterfactual claims need counterfactual controls.** Our cross-field DiD looked supportive on the surface (HIGH dropped less than LOW), but the pre-trends were already non-parallel, which is exactly the assumption DiD needs. The point estimate ended up being inconclusive — neither supporting nor falsifying — once the pre-trend was visible. We initially read this result as falsifying the hypothesis in the wrong direction, then later as supporting it. Both were wrong; it is neither.

**Behavior signals and data-pipeline artifacts are easy to confuse.** Two of our supposed findings — the citation-age increase and (most likely) part of the forward-citation collapse — turned out to be artifacts of how the dataset itself is constructed rather than signals about how researchers behave. The citation-age artifact was obvious once we looked at where the matches were landing in the works table. The forward-citation artifact is more speculative but consistent with what is publicly known about OpenAlex's preprint deduplication. In any bibliometric study with a non-uniform underlying dataset, the relevant first question is "what would this metric look like if behavior were unchanged?" — and if the answer matches what is observed, the metric is not a behavior signal.

## 7. Limitations

- **Yearly resolution.** With four yearly data points across 2021–2024 we have very low power against any effect smaller than annual variation. Monthly resolution would help substantially; see §8.
- **Two post-ChatGPT years.** Effects that take time to materialize — for example, citation patterns in papers that started development just after ChatGPT but were published in 2025 — would not appear in this window.
- **Single citation graph.** All results depend on OpenAlex's coverage and dating semantics. The citation-age artifact and the likely preprint-dating artifact in forward citations both originate in the dataset, not in the analysis. Replicating against another source (e.g. Semantic Scholar, Crossref) would strengthen any claim.
- **Field exposure was coarsely defined.** "Computer Science" is one OpenAlex field label and contains substantial within-field heterogeneity (NLP/ML, theory, systems, etc.) that would respond differently to ChatGPT. The §5.6 DiD is therefore a conservative test in one direction (broad CS) and a noisy test in another (within-CS variation washed out).

## 8. Future Work

Four follow-up questions emerged from this analysis. The first two are the strongest leads.

1. **Does a monthly-resolution structural-break test find anything at November 2022?** This is the closest available power upgrade. Approximately 48 monthly observations across 2021–2024 enable a formal break test (a Chow test, which checks whether a single line fits a time series or whether two lines — one before, one after a candidate breakpoint — fit significantly better). Publication dates and paper types have been backfilled for all mutual-pair papers ([data/backfill_dates.py](../data/backfill_dates.py)); the scripts to run the test exist ([research/monthly_trajectory.py](../research/monthly_trajectory.py), [research/monthly_robustness.py](../research/monthly_robustness.py)). Even a null result at monthly resolution would substantially strengthen the conclusions in this paper.

2. **Is the broader forward-citation collapse real behavior, or an OpenAlex dating artifact?** §5.8 points strongly toward the latter, but does not prove it. Comparing preprint-dating semantics in OpenAlex across snapshot versions, or replicating against a source with explicit preprint metadata, would settle this. It matters because some non-trivial fraction of our aggregate −13.2%/yr decline may be pipeline drift rather than real behavior.

3. **Does within-CS DiD (NLP/ML-adjacent subfields vs theory/compilers) show a ChatGPT effect?** Pre-trends within CS are likely more parallel than the CS-vs-empirical split we used here, which would allow DiD to actually identify a causal effect where the field-level version cannot. This is the natural follow-up to the inconclusive §5.6 result.

4. **What is driving the pre-existing secular decline in mutual citation rates?** Independent of the ChatGPT question, the decline itself is a real finding (R² = 0.94 over four years, with a comparable trajectory in its dominant gap = 1 component). Candidate causes: within-field rate changes vs. between-field composition shifts; rising citation concentration (a small number of papers absorbing more citations) mechanically reducing pair-formation probability. The decline predates ChatGPT and is independently worth understanding.

## 9. Conclusion

We tested a specific hypothesis — that ChatGPT increased the rate of mutual citations by compressing peer discovery — and found that the data does not support it. The mutual citation rate did decline after ChatGPT, but the decline started before ChatGPT existed, continues smoothly through and after its launch, and shows no break even on the same-year subset where the hypothesized mechanism should be strongest. The most striking results we initially obtained (a 41% headline drop, a 3.4× increase in cited paper age, a positive cross-field DiD) all weakened or reversed under closer inspection — illustrating, in our view, the principal methodological lesson of the project: at industrial sample sizes, statistical significance is cheap, and only tests that examine *when* and *where* a change appears can distinguish a behavior shift from a coincident pre-existing trend.
