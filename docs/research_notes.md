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

## Results (May 14, 2026)

Ran research/motif_analysis.py and research/stat_test.py on the cleaned dataset.
Pre-ChatGPT (2020–2021): 19,769 mutual citation pairs across 403,920 papers — 48.94 per 1000 papers.
Post-ChatGPT (2023–2024): 14,055 mutual citation pairs across 400,290 papers — 35.11 per 1000 papers.
Chi-square statistic: 954.21, p-value: ~0.000000000 — statistically significant.

Finding: mutual citation rate decreased by 28% after ChatGPT's release.
This is the opposite of the hypothesis. The decrease is statistically significant and cannot be attributed to random variation.
Next step: investigate why.