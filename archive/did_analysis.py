import duckdb
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

con = duckdb.connect("data/citations.duckdb")

# Difference-in-differences: does ChatGPT exposure level interact with the
# post-ChatGPT period? Idea: a secular trend hits both groups equally; a
# real ChatGPT effect should hit high-exposure fields more.
HIGH_EXPOSURE = ["Computer Science"]  # most unambiguous case
LOW_EXPOSURE = [
    "Chemistry",
    "Materials Science",
    "Agricultural and Biological Sciences",
    "Earth and Planetary Sciences",
    "Immunology and Microbiology",
]

def field_year_counts(fields):
    """For each year, return (papers, papers_in_mutual_pair) summed across fields."""
    placeholders = ",".join(["?"] * len(fields))
    rows = con.execute(f"""
        WITH mutual_pairs AS (
            SELECT a.citing_id AS p1, a.cited_id AS p2
            FROM citations a
            JOIN citations b ON a.citing_id=b.cited_id AND a.cited_id=b.citing_id
            WHERE a.citing_id < a.cited_id
        ),
        papers_in_mutual AS (
            SELECT DISTINCT p1 AS pid FROM mutual_pairs
            UNION
            SELECT DISTINCT p2 FROM mutual_pairs
        ),
        per_year AS (
            SELECT w.year,
                   COUNT(*) AS papers,
                   COUNT(*) FILTER (WHERE pi.pid IS NOT NULL) AS in_mutual
            FROM works w
            LEFT JOIN papers_in_mutual pi ON pi.pid = w.id
            WHERE w.field IN ({placeholders})
              AND w.year BETWEEN 2021 AND 2024
            GROUP BY w.year
        )
        SELECT year, papers, in_mutual FROM per_year ORDER BY year
    """, fields).fetchall()
    return {y: (p, m) for y, p, m in rows}

high = field_year_counts(HIGH_EXPOSURE)
low = field_year_counts(LOW_EXPOSURE)

print(f"HIGH exposure fields: {HIGH_EXPOSURE}")
print(f"LOW  exposure fields: {LOW_EXPOSURE}\n")

def summarize(label, data):
    print(f"=== {label} ===")
    for y in sorted(data):
        p, m = data[y]
        print(f"  {y}: {m:>5,} in mutual / {p:>7,} papers = {m/p*1000:>6.2f} per 1000")

summarize("HIGH (Computer Science)", high)
print()
summarize("LOW (5 empirical fields)", low)

# Pool pre (2021-2022) vs post (2023-2024) for each group
def pool(data, years):
    p = sum(data[y][0] for y in years)
    m = sum(data[y][1] for y in years)
    return p, m

high_pre_p, high_pre_m = pool(high, [2021, 2022])
high_post_p, high_post_m = pool(high, [2023, 2024])
low_pre_p, low_pre_m = pool(low, [2021, 2022])
low_post_p, low_post_m = pool(low, [2023, 2024])

high_pre_rate = high_pre_m / high_pre_p * 1000
high_post_rate = high_post_m / high_post_p * 1000
low_pre_rate = low_pre_m / low_pre_p * 1000
low_post_rate = low_post_m / low_post_p * 1000

print("\n=== Pre vs Post (pooled) ===")
print(f"  HIGH pre  (2021-2022): {high_pre_m:>5,} / {high_pre_p:>7,} = {high_pre_rate:>6.2f} per 1000")
print(f"  HIGH post (2023-2024): {high_post_m:>5,} / {high_post_p:>7,} = {high_post_rate:>6.2f} per 1000")
print(f"  HIGH change: {high_post_rate - high_pre_rate:+.2f} per 1000 ({(high_post_rate/high_pre_rate - 1)*100:+.1f}%)")
print()
print(f"  LOW  pre  (2021-2022): {low_pre_m:>5,} / {low_pre_p:>7,} = {low_pre_rate:>6.2f} per 1000")
print(f"  LOW  post (2023-2024): {low_post_m:>5,} / {low_post_p:>7,} = {low_post_rate:>6.2f} per 1000")
print(f"  LOW  change: {low_post_rate - low_pre_rate:+.2f} per 1000 ({(low_post_rate/low_pre_rate - 1)*100:+.1f}%)")

# Difference in differences (absolute and log-relative)
did_abs = (high_post_rate - high_pre_rate) - (low_post_rate - low_pre_rate)
did_log = (np.log(high_post_rate) - np.log(high_pre_rate)) - (np.log(low_post_rate) - np.log(low_pre_rate))

print("\n=== Difference-in-differences ===")
print(f"  DiD (absolute):   {did_abs:+.2f} per 1000")
print(f"  DiD (log-rate):   {did_log:+.4f}")
print(f"  HIGH relative change: {(high_post_rate/high_pre_rate - 1)*100:+.1f}%")
print(f"  LOW  relative change: {(low_post_rate/low_pre_rate - 1)*100:+.1f}%")
print(f"  Hypothesis predicts: HIGH should drop MORE than LOW (DiD < 0 if drop, > 0 if rise)")

# Test the interaction: is the post*group interaction significant?
# Build a 2x2x2 table and use chi-square as a quick test of the interaction.
# More principled: compute the standard error of the log-rate DiD using the
# delta method on Bernoulli proportions.
def log_rate_se(m, p):
    """SE of log(m/p) for a Bernoulli proportion via delta method."""
    return np.sqrt((1 - m / p) / m)

se_high_pre  = log_rate_se(high_pre_m, high_pre_p)
se_high_post = log_rate_se(high_post_m, high_post_p)
se_low_pre   = log_rate_se(low_pre_m, low_pre_p)
se_low_post  = log_rate_se(low_post_m, low_post_p)
se_did = np.sqrt(se_high_pre**2 + se_high_post**2 + se_low_pre**2 + se_low_post**2)

z = did_log / se_did
from scipy.stats import norm
p_two_sided = 2 * (1 - norm.cdf(abs(z)))

print(f"\n  Log-rate DiD: {did_log:+.4f} (SE {se_did:.4f}, z = {z:+.2f}, p = {p_two_sided:.4f})")
if p_two_sided < 0.05:
    if did_log < 0:
        print("  HIGH dropped MORE than LOW (consistent with hypothesis)")
    else:
        print("  HIGH dropped LESS than LOW (OPPOSITE of hypothesis)")
else:
    print("  Cannot reject the null of no differential ChatGPT effect.")

# Plot trajectories
fig, ax = plt.subplots(figsize=(10, 6))
years = [2021, 2022, 2023, 2024]
high_rates = [high[y][1] / high[y][0] * 1000 for y in years]
low_rates = [low[y][1] / low[y][0] * 1000 for y in years]

ax.plot(years, high_rates, "o-", color="darkblue", linewidth=2, markersize=10,
        label=f"HIGH exposure (CS, n~{sum(p for p,_ in high.values()):,})")
ax.plot(years, low_rates, "s-", color="darkorange", linewidth=2, markersize=10,
        label=f"LOW exposure (5 empirical fields, n~{sum(p for p,_ in low.values()):,})")
ax.axvline(x=2022.92, color="red", linestyle=":", label="ChatGPT launch")
ax.set_title("Difference-in-differences: high vs low ChatGPT-exposure fields")
ax.set_xlabel("Year")
ax.set_ylabel("Papers in mutual pairs (per 1000)")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/did_analysis.png", dpi=150)
print("\nSaved chart to outputs/did_analysis.png")
