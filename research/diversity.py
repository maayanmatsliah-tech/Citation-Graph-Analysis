import duckdb
import matplotlib.pyplot as plt

con = duckdb.connect("data/citations.duckdb")

print("Calculating lifespans and year averages...")

# step 1: get lifespan for every paper and the average for its publication year
papers = con.execute("""
    WITH lifespans AS (
        SELECT 
            w.id,
            w.year AS pub_year,
            MAX(w_citing.year) - w.year AS lifespan
        FROM works w
        JOIN citations c ON c.cited_id = w.id
        JOIN works w_citing ON c.citing_id = w_citing.id
        WHERE w.year BETWEEN 1960 AND 1989
        AND w_citing.year >= w.year
        GROUP BY w.id, w.year
    ),
    year_avgs AS (
        SELECT pub_year, AVG(lifespan) AS avg_lifespan
        FROM lifespans
        GROUP BY pub_year
    ),
    early_citers AS (
        SELECT 
            w.id,
            COUNT(DISTINCT c.citing_id) AS early_citer_count
        FROM works w
        JOIN citations c ON c.cited_id = w.id
        JOIN works w_citing ON c.citing_id = w_citing.id
        WHERE w.year BETWEEN 1960 AND 1989
        AND w_citing.year >= w.year
        AND w_citing.year <= w.year + 10
        GROUP BY w.id
        HAVING COUNT(DISTINCT c.citing_id) >= 2
    )
    SELECT 
        l.id,
        l.pub_year,
        l.lifespan,
        ya.avg_lifespan,
        l.lifespan / ya.avg_lifespan AS lifespan_ratio,
        e.early_citer_count
    FROM lifespans l
    JOIN year_avgs ya ON l.pub_year = ya.pub_year
    JOIN early_citers e ON l.id = e.id
""").fetchall()

print(f"Total papers: {len(papers)}")

# classify by ratio to their year's average
long_livers = [r for r in papers if r[4] >= 1.5]
short_livers = [r for r in papers if r[4] <= 0.5]

print(f"Long-livers (>=1.5x their year avg): {len(long_livers)}")
print(f"Short-livers (<=0.5x their year avg): {len(short_livers)}")

# step 2: calculate overlap scores for each group
def get_overlap_score(paper_id, pub_year, con):
    citers = con.execute("""
        SELECT DISTINCT c.citing_id
        FROM citations c
        JOIN works w_citing ON c.citing_id = w_citing.id
        WHERE c.cited_id = ?
        AND w_citing.year >= ?
        AND w_citing.year <= ?
    """, [paper_id, pub_year, pub_year + 10]).fetchall()

    citer_ids = [r[0] for r in citers]
    if len(citer_ids) < 2:
        return None

    citer_citations = {}
    for citer_id in citer_ids:
        refs = con.execute("""
            SELECT cited_id FROM citations WHERE citing_id = ?
        """, [citer_id]).fetchall()
        citer_citations[citer_id] = set(r[0] for r in refs)

    pairs = 0
    total_overlap = 0
    for j in range(len(citer_ids)):
        for k in range(j + 1, len(citer_ids)):
            a = citer_citations[citer_ids[j]]
            b = citer_citations[citer_ids[k]]
            if len(a | b) == 0:
                continue
            jaccard = len(a & b) / len(a | b)
            total_overlap += jaccard
            pairs += 1

    return total_overlap / pairs if pairs > 0 else None

print("\nCalculating overlap scores for long-livers...")
long_scores = []
for i, r in enumerate(long_livers):
    score = get_overlap_score(r[0], r[1], con)
    if score is not None:
        long_scores.append(score)
    if i % 20 == 0:
        print(f"  {i}/{len(long_livers)}...")

print("Calculating overlap scores for short-livers...")
short_scores = []
for i, r in enumerate(short_livers):
    score = get_overlap_score(r[0], r[1], con)
    if score is not None:
        short_scores.append(score)
    if i % 20 == 0:
        print(f"  {i}/{len(short_livers)}...")

print(f"\nLong-livers with scores: {len(long_scores)}")
print(f"Short-livers with scores: {len(short_scores)}")

if long_scores and short_scores:
    print(f"\nAvg overlap - long-livers:  {sum(long_scores)/len(long_scores):.4f}")
    print(f"Avg overlap - short-livers: {sum(short_scores)/len(short_scores):.4f}")

    plt.figure(figsize=(10, 5))
    plt.hist(short_scores, bins=30, alpha=0.6, color="red", label="Short-livers", edgecolor="white")
    plt.hist(long_scores, bins=30, alpha=0.6, color="blue", label="Long-livers", edgecolor="white")
    plt.title("Early Citer Overlap: Long-livers vs Short-livers\n(normalized by publication year)")
    plt.xlabel("Avg overlap between early citers (lower = more diverse)")
    plt.ylabel("Number of papers")
    plt.legend()
    plt.tight_layout()
    plt.savefig("outputs/diversity_comparison.png", dpi=150)
    plt.show()

print("done.")