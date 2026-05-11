# Citation Graph Research Notes

## Dataset
- Source: OpenAlex S3 snapshot
- Total papers ingested: 7.7 million
- Total citation links: 6.4 million
- Storage: citations.duckdb (214MB)

## Scope
- Working dataset: papers published 1960–1989
- Reason: full citation lifespans observable (35-65 years of history)
- Papers in scope: 886,484
- Papers with traceable citations: 9,783
- Papers with early citation data (cited within first 10 years): 3,004

## Research Question
Among papers published 1960–1989, do papers that live significantly longer than the average citation lifespan for their decade share a structural pattern in how they were cited in their first 10 years — specifically, were they cited by a more diverse set of papers?

## Hypothesis
Papers cited by many different, unrelated papers early on outlive papers cited the same number of times by the same small group — suggesting that early citation diversity, not volume, predicts long-term survival.

## Key Decisions
- Dropped post-1990 papers entirely to avoid tech boom bias
- Using citation overlap between early citers as a proxy for field diversity (no field metadata available)
- Comparing each paper against others from its own decade to normalize for era

## Findings So Far

### Lifespan Distribution (lifespan_distribution.png)
- Average lifespan: 8.3 years
- Shortest: 0 years
- Longest: 56 years
- Most papers die within 0–10 years
- Long tail stretches to 56 years
- Curious second bump around 28–32 years — possible two distinct populations of long-livers

### Group Definitions
- Short-livers: lifespan below 8 years (below average)
- Long-livers: lifespan above 25 years (top ~10%)

## Next Steps
- Step 2: measure early citation diversity for each paper
- Step 3: compare diversity scores between short-livers and long-livers
- Step 4: test whether the pattern holds across publication decades