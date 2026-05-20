# Mutual Citations After ChatGPT: A Null Result and Its Limits

## Abstract

ChatGPT, released in November 2022, plausibly compressed the process by which researchers discover and extract specific information from each other's work. If so, we should see this change reflected in the citation graph — perhaps, in particular, in the rate of *mutual citations*, the unusual case where two papers cite each other. We test this prediction using ~1M papers from OpenAlex spanning 2020–2024. A first-pass test finds a large, statistically significant decline in mutual citation rate after ChatGPT, but this appears to reflect a continuing pre-existing trend rather than any change at ChatGPT's launch. Four additional checks — a yearly trajectory fit, a cross-field difference-in-differences, a paper-volume control, and a year-gap stratification — are consistent with that reading, and a fifth check traces part of the decline to a likely artifact of preprint dating semantics in OpenAlex. **However, all of our tests are weak in important ways.** The trajectory fit has only four yearly data points; the two-year post-ChatGPT window may be shorter than the submission-to-publication lag for affected papers; and mutual citation rate is a narrow proxy for "compressed peer discovery" that may miss the mechanism entirely. We therefore do not claim to have refuted the hypothesis. What we have shown is that the most direct version of the predicted effect is not visible in this data at yearly resolution, and that the cause of the pre-existing decline — which the hypothesis cannot have produced — is itself not yet understood.

## 1. Introduction

When ChatGPT was released to the public in November 2022, it changed how many researchers interact with the scientific literature. Instead of reading a paper end-to-end to extract a single claim, researchers can now ask a language model for the relevant passage. This plausibly compresses the front end of the research process — finding, filtering, and extracting from prior work — in a way that could leave a measurable fingerprint on what people cite.

This paper tests one specific prediction of that hypothesis: that *mutual citations* — where paper A cites paper B and paper B cites paper A — should have risen after ChatGPT.

Mutual citations are structurally rare. For one to exist, both authors must have been aware of each other's work at the time of writing, and each must have decided to cite it. Before ChatGPT, the cost of discovering and absorbing a recent or in-progress paper from another group was high enough that mutual citations were unusual. If ChatGPT really did compress that discovery process — surfacing relevant recent work faster, extracting the salient claim without requiring a full read — then citation loops that would not previously have formed should start forming. Mutual citation rate per 1000 papers is the natural quantity to look at.

We find that this prediction is not borne out at the resolution we can test. Mutual citation rates declined after ChatGPT, but the decline started *before* ChatGPT existed and continued smoothly through and after its launch. We rule out the most obvious alternative explanations for the headline rate change (paper volume, citation lag, field composition), and we find no break at ChatGPT even on the same-year mutual subset, where compressed peer discovery should matter most.

Two qualifications belong at the front, not in a limitations section at the back. First, mutual citations are themselves a *narrow* proxy for the hypothesized mechanism. ChatGPT cannot help paper A cite paper B if paper B does not yet exist when A is being written, and mutual reciprocity requires *both* directions to clear that bar. A compressed-discovery effect would more naturally show up in metrics like citation breadth, novelty, or time-to-first inbound citation. Our test addresses the most direct surface prediction of the hypothesis, not the only plausible one.

Second, the data we have is thin in two ways that limit our statistical power. With four yearly observations across 2021–2024, any monotone sequence will fit a line well — the "trajectory" framework we rely on has limited ability to *distinguish* a smooth pre-existing decline from a smooth pre-existing decline plus a small ChatGPT effect that happens to push in the same direction. And with only two post-ChatGPT years, papers whose writing was substantially shaped by ChatGPT — given typical submission and review lag — may be largely absent from the data even now.

What this paper contributes, then, is a careful documentation of what the most direct test of the hypothesis shows at yearly resolution, together with the auxiliary findings that emerged in the process: a real, pre-existing secular decline whose cause we cannot identify; evidence that part of that decline is likely a dataset artifact rather than a behavior change; and a methodological note that at this sample size, p-values from binary pre/post tests are misleading in a way that is easy to overlook.

## 2. Hypothesis and Definitions

We test the following hypothesis:

> Mutual citation rate per 1000 papers increased after November 2022, beyond what would be expected from changes in paper volume alone.

A few definitions that recur throughout:

- A **citation graph** is a directed network of papers. An edge from paper A to paper B means A's reference list contains B.
- A **mutual citation** (or *mutual pair*) is the case where both A → B and B → A are present.
- A **self-citation** is an edge from a paper to itself (an artifact in our raw data; excluded).

The hypothesis predicts a *rate* increase, not just a count increase, because the total number of papers published each year fluctuates. We normalize throughout to "mutual pairs per 1000 papers," and separately check that paper volume itself is roughly flat in the period studied.

It is worth being explicit about what mutual citations can and cannot capture. For a mutual pair to exist between papers A and B, paper B must already exist (at least as a preprint) when paper A is being written, *and* paper A must exist when paper B is being written. This rules out ChatGPT helping with discovery of work that simply hadn't been written yet, and it doubles the timing constraint — both authors have to clear the awareness bar within roughly the same writing window. ChatGPT-assisted discovery of recent literature would also and perhaps more naturally show up in *non-mutual* directional citations: a paper citing more recent work, more broadly, or with shorter time-to-discovery. Mutual citation rate is therefore one specific testable surface of the hypothesis, not the whole hypothesis. A null result on mutual rate does not by itself falsify the broader claim that ChatGPT changed citation behavior; it only constrains one channel through which that claim could have manifested.

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

### 5.3 The decline appears to be pre-existing

Fitting `log(rate) = a + b · year` to the four post-2020 yearly rates ([research/trajectory.py](../research/trajectory.py)) gives:

- Annualized rate of change: **−13.2% per year**.
- R² = 0.944.
- Slope p-value: 0.028.

A note on what R² means here is essential, because the test cuts both ways. A high R² on four data points is a much weaker claim than a high R² on, say, forty. Any monotone sequence of four points fits a straight line well by construction — there simply aren't enough degrees of freedom for a poor fit to register. So R² = 0.944 should be read as "the four yearly rates are monotone-ish and roughly evenly spaced in log-space," not as "we have established that a single trend really describes the data." In particular, this fit cannot distinguish a smooth pre-existing decline from a smooth pre-existing decline plus a small ChatGPT effect operating in the same direction; both would produce a high R² with the post-ChatGPT years roughly on-line. The trajectory test is therefore informative against the *strong* version of the hypothesis (a sharp, large increase post-ChatGPT — which is not what we see), but underpowered against a weaker version (a small effect riding the existing trend).

With that caveat front-loaded: the post-ChatGPT years sit essentially on the line implied by the pre-ChatGPT data.

| Year | Observed | Trend predicts | Residual (log) |
|------|---------:|---------------:|---------------:|
| 2021 | 12.65 | 12.13 | +0.042 |
| 2022 |  9.94 | 10.53 | **−0.057** (biggest deviation — pre-ChatGPT) |
| 2023 |  9.03 |  9.14 | −0.012 |
| 2024 |  8.15 |  7.93 | +0.027 |

The largest single-year drop in the entire window is **2021 → 2022, a 21.4% decline** — and 2022 papers were written and submitted before ChatGPT existed. The two post-ChatGPT years move at roughly half the rate of that pre-ChatGPT drop. Comparing the slopes directly:

- Pre-ChatGPT slope (log-rate from 2021 to 2022): −0.241.
- Post-ChatGPT slope (log-rate from 2023 to 2024): −0.103.

The decline is *decelerating* after ChatGPT, not accelerating. If ChatGPT had caused a sharp break in citation behavior — the version of the hypothesis the test can actually see — we would expect the post-ChatGPT years to fall notably below the pre-existing trend. They do not. We cannot, however, rule out a smaller effect riding the existing trend; see the R² caveat above. Chart: [outputs/trajectory.png](../outputs/trajectory.png).

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

- **HIGH exposure:** Computer Science.
- **LOW exposure:** Chemistry, Materials Science, Agricultural and Biological Sciences, Earth and Planetary Sciences, Immunology and Microbiology — empirical / wet-lab / field-data disciplines where ChatGPT changes day-to-day work much less.

Both groupings are coarse. "Computer Science" as a single label conflates NLP, ML, systems, theory, compilers, formal methods and security — subfields whose actual ChatGPT exposure varies dramatically. Treating all of CS as uniformly "high exposure" is a stretch in one direction, and pooling the empirical fields into a single counterfactual is a stretch in the other. The test below is therefore a noisy approximation of the cross-field comparison the hypothesis actually invites.

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

DiD is therefore **genuinely inconclusive**: the point estimate is compatible with a real ChatGPT lift in exposed fields *and* compatible with "CS and empirical fields decline at different rates for unrelated reasons, and that pre-existing pattern continued." Non-parallel pre-trends mean DiD cannot separate the two stories. We should not let this result narrow the conclusion in either direction. In particular, the direction of the point estimate is the direction the hypothesis predicts, which is worth registering — even if we cannot quantify how much of it (if any) is attributable to ChatGPT.

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

### What we can and cannot claim

The hypothesis tested in this paper has two layers. The narrow version — *ChatGPT caused a large, sharp increase in mutual citation rates after November 2022* — is not visible in our data. Yearly rates declined across the window, the decline began before ChatGPT existed, and the same-year subset (the strongest possible test of the proposed mechanism) shows no break either. Whatever ChatGPT may have done, it did not produce the dramatic mutual-citation lift the original hypothesis predicted.

The broader version — *ChatGPT changed citation behavior at all* — is something this paper does **not** establish either way. There are at least four reasons to keep that question open:

1. **The trajectory test is underpowered.** Four yearly data points cannot distinguish a smooth pre-existing decline from a smooth pre-existing decline plus a small ChatGPT effect operating in the same direction. Both produce a tight line with the post-ChatGPT years on or near it. A high R² at this resolution is structural, not evidential.
2. **The window may be too short.** Submission-to-publication lag means many papers in our 2023–2024 post-ChatGPT cohort were largely written before the tool was a stable part of researcher workflow. The papers most likely to show a ChatGPT effect on citation behavior are 2024+, and 2024 is itself at the edge of OpenAlex's reliable coverage. We may be looking at the wrong years.
3. **Mutual citation rate is a narrow proxy.** As discussed in §2 and §4.3, ChatGPT cannot help a paper cite work that does not yet exist, and mutual reciprocity requires both directions to clear that bar. A compressed-discovery effect would more naturally manifest in directional citations (more recent, broader, faster-arriving) than in mutual reciprocity. Our null on mutual rate constrains one channel; it does not foreclose others.
4. **The DiD is genuinely inconclusive.** The point estimate is directionally consistent with the hypothesis but cannot be interpreted causally because of non-parallel pre-trends. We should not let this widen *or* narrow the conclusion.

### The pre-existing decline is itself unexplained

Our most reliable finding is also our most unsettling one: mutual citation rates were already falling at roughly −13%/year before ChatGPT, and we do not know why. The trajectory documents the decline; it does not explain it.

This matters for the central question in a way the paper has so far underplayed. We argue that the pre-existing decline cannot be a ChatGPT effect, because ChatGPT did not yet exist. That argument is sound on its face. But it relies on the assumption that the "pre-existing decline" we measure is itself a real behavior signal — that what looks like a smooth fall in mutual citation rate across 2021, 2022, 2023, 2024 reflects what researchers actually did, rather than what OpenAlex's pipeline records about what researchers did. The same kind of artifact we identified for citation age in §5.9, and that most plausibly explains the forward-citation collapse in §5.8, could in principle be contributing to the aggregate decline as well. We have no positive evidence that it is. But until the cause of the secular decline is independently understood — within-field rate changes vs. between-field composition shifts, rising citation concentration, dataset coverage drift — we cannot say with confidence what the "pre-existing trend" we are netting out actually represents.

### Methodological notes that generalize

Three observations from the project that apply beyond it:

**Sample size makes p-values misleading.** At n ≈ 400,000 the chi-square test would call a 0.5% absolute difference statistically significant. Our headline first-pass result, p ≈ 0, was on its own a piece of structural arithmetic about the sample. Conversely, **fit quality is misleading at very small n.** Our R² = 0.94 on four points is the same kind of trap in the opposite direction: it sounds like strong evidence of a single trend, but four monotone points will fit a line by construction. Both failure modes have the same root — reporting a statistic without asking what its sampling distribution looks like at this n.

**Counterfactual claims need counterfactual controls.** Our cross-field DiD looked supportive on the surface (HIGH dropped less than LOW), but the pre-trends were already non-parallel, which is exactly the assumption DiD needs. The result is genuinely inconclusive — it should widen uncertainty rather than narrow it in either direction.

**Behavior signals and data-pipeline artifacts are easy to confuse.** Two of our findings — the apparent citation-age increase and (most likely) part of the forward-citation collapse — were dataset artifacts, not behavior. The citation-age artifact was straightforward to identify once we asked where the matches were landing in the works table. The forward-citation artifact is more speculative but consistent with what is publicly known about OpenAlex's preprint deduplication. In bibliometric studies generally, the first question to ask of any time-varying metric is: "what would this look like if behavior were unchanged but the dataset's coverage shifted over the same window?" If the answer matches what is observed, the metric is not a behavior signal.

## 7. Limitations

- **Yearly resolution gives little statistical power.** Four yearly data points across 2021–2024 cannot distinguish a pre-existing trend from a pre-existing trend plus a small effect operating in the same direction. The R² = 0.94 we report is largely structural at this n. Monthly resolution would help substantially; see §8.
- **Two post-ChatGPT years may not cover the affected papers.** Submission-to-publication lag in most fields is 6–24 months. Papers whose writing was substantially shaped by ChatGPT — adopted as a stable workflow tool in early 2023 — would mostly be 2024 papers at the earliest, and many would publish in 2025+. Our window may simply not include the relevant cohort.
- **Mutual citation is a narrow proxy.** ChatGPT cannot help a paper cite work that did not exist when the paper was written, and mutual reciprocity requires both authors to clear the awareness bar within a narrow window. A compressed-discovery effect would more naturally show in directional metrics (citation breadth, novelty, time-to-first inbound citation). Our null on mutual rate constrains one channel through which the hypothesis could manifest; it does not test the others.
- **The pre-existing decline is unexplained.** We use the pre-ChatGPT trajectory as a counterfactual for what would have happened without ChatGPT, but we have no positive explanation for why mutual citations were already falling. If part of that decline is itself a dataset artifact (as appears to be the case for the citation-age finding and likely for the forward-citation collapse), our counterfactual is partly built on artifact.
- **Single citation graph.** All results depend on OpenAlex's coverage and dating semantics. Two of our supposed findings turned out to be dataset artifacts; we cannot rule out that others are. Replicating against another source (e.g. Semantic Scholar, Crossref, Web of Science) would substantially strengthen any conclusion about real behavior.
- **Field exposure is coarsely defined.** "Computer Science" as a single OpenAlex label conflates NLP, ML, systems, theory, compilers, and security — subfields whose actual ChatGPT exposure varies dramatically. Treating all of CS as uniformly high-exposure is a stretch in one direction; pooling five empirical fields into a single counterfactual is a stretch in the other. §5.6 should be read as a rough, exploratory cross-field comparison, not a precise estimate.

## 8. Future Work

Four follow-up questions emerged from this analysis. The first two are the strongest leads.

1. **Does a monthly-resolution structural-break test find anything at November 2022?** This is the closest available power upgrade. Approximately 48 monthly observations across 2021–2024 enable a formal break test (a Chow test, which checks whether a single line fits a time series or whether two lines — one before, one after a candidate breakpoint — fit significantly better). Publication dates and paper types have been backfilled for all mutual-pair papers ([data/backfill_dates.py](../data/backfill_dates.py)); the scripts to run the test exist ([research/monthly_trajectory.py](../research/monthly_trajectory.py), [research/monthly_robustness.py](../research/monthly_robustness.py)). Even a null result at monthly resolution would substantially strengthen the conclusions in this paper.

2. **Is the broader forward-citation collapse real behavior, or an OpenAlex dating artifact?** §5.8 points strongly toward the latter, but does not prove it. Comparing preprint-dating semantics in OpenAlex across snapshot versions, or replicating against a source with explicit preprint metadata, would settle this. It matters because some non-trivial fraction of our aggregate −13.2%/yr decline may be pipeline drift rather than real behavior.

3. **Does within-CS DiD (NLP/ML-adjacent subfields vs theory/compilers) show a ChatGPT effect?** Pre-trends within CS are likely more parallel than the CS-vs-empirical split we used here, which would allow DiD to actually identify a causal effect where the field-level version cannot. This is the natural follow-up to the inconclusive §5.6 result.

4. **What is driving the pre-existing secular decline in mutual citation rates?** Independent of the ChatGPT question, the decline itself is a real finding (R² = 0.94 over four years, with a comparable trajectory in its dominant gap = 1 component). Candidate causes: within-field rate changes vs. between-field composition shifts; rising citation concentration (a small number of papers absorbing more citations) mechanically reducing pair-formation probability. The decline predates ChatGPT and is independently worth understanding.

## 9. Conclusion

We tested a specific prediction of a specific hypothesis: that ChatGPT, by compressing peer discovery, would increase the rate at which papers cite each other mutually. At yearly resolution, on the most direct measurement, this prediction is not visible in our data. The mutual citation rate did decline after ChatGPT, but the decline started before ChatGPT existed, continues smoothly through and after its launch, and shows no break even on the same-year subset where the hypothesized mechanism should be strongest.

We are deliberately not claiming more than this. The trajectory test is underpowered against a smaller effect riding the existing trend; the two-year post-ChatGPT window may not yet include the papers most likely to be affected; mutual citation rate is a narrow proxy for the proposed mechanism; and the pre-existing decline we use as a counterfactual is itself not understood, and is plausibly contaminated by the same kind of dataset artifacts we identified in two of our auxiliary findings. The honest summary is that the *strong* version of the hypothesis is not visible in this data, and that any *weaker* version remains untestable with the resolution, window, and proxy available here.

The most striking results we initially obtained — a 41% headline drop, a 3.4× increase in cited paper age, a positive cross-field DiD — all weakened or reversed under closer inspection. The principal methodological lesson of the project, then, runs in both directions: at large n, statistical significance is cheap and easy to overread; at small n, fit quality is cheap and easy to overread; and in both cases, only tests that examine *when* and *where* a change appears, *across more than one metric and one dataset*, can distinguish a real behavior shift from a coincident pre-existing trend or a coincident pipeline artifact.
