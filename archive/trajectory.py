import duckdb
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

con = duckdb.connect("data/citations.duckdb")

# per-year mutual citation rate, using the corrected (deduped, no self-cite) query
rows = con.execute("""
    WITH mutual_pairs AS (
        SELECT a.citing_id AS p1, a.cited_id AS p2
        FROM citations a
        JOIN citations b ON a.citing_id = b.cited_id AND a.cited_id = b.citing_id
        WHERE a.citing_id < a.cited_id
    ),
    by_year AS (
        SELECT GREATEST(w1.year, w2.year) AS y, COUNT(*) AS pairs
        FROM mutual_pairs m
        JOIN works w1 ON m.p1 = w1.id
        JOIN works w2 ON m.p2 = w2.id
        WHERE w1.year BETWEEN 2018 AND 2024 AND w2.year BETWEEN 2018 AND 2024
        GROUP BY y
    )
    SELECT b.y, b.pairs,
           (SELECT COUNT(*) FROM works WHERE year = b.y) AS papers
    FROM by_year b ORDER BY b.y
""").fetchall()

per_year = {y: (pairs, papers, pairs / papers * 1000) for y, pairs, papers in rows}

print("=== Per-year mutual citation rate ===")
for y in sorted(per_year):
    pairs, papers, rate = per_year[y]
    print(f"  {y}: {pairs:,} pairs / {papers:,} papers = {rate:.2f} per 1000")

# 2020 excluded as a COVID-era outlier (see docs/research_notes.md)
fit_years = np.array([2021, 2022, 2023, 2024])
fit_rates = np.array([per_year[y][2] for y in fit_years])
log_rates = np.log(fit_rates)

# fit linear trend to log(rate) — i.e. exponential decay model
fit = linregress(fit_years, log_rates)
annual_change_pct = (np.exp(fit.slope) - 1) * 100

print("\n=== Linear trend on log(rate), 2021-2024 ===")
print(f"  Slope (log rate / year):    {fit.slope:.4f}")
print(f"  Annual % change in rate:    {annual_change_pct:+.1f}%")
print(f"  R-squared:                  {fit.rvalue**2:.4f}")
print(f"  Slope p-value:              {fit.pvalue:.4f}")

# residuals: is each year above or below the fitted trend?
predicted_log = fit.slope * fit_years + fit.intercept
residuals = log_rates - predicted_log
print("\n=== Residuals (observed vs trend prediction) ===")
print("  Negative residual = below trend (decline faster than trend)")
print("  Positive residual = above trend (decline slower than trend)")
for y, obs, pred, res in zip(fit_years, fit_rates, np.exp(predicted_log), residuals):
    print(f"  {y}: observed {obs:.2f}, trend predicts {pred:.2f}, residual {res:+.4f}")

# year-over-year drops: where is the steepest decline?
print("\n=== Year-over-year decline ===")
for i in range(1, len(fit_years)):
    y_prev, y_curr = fit_years[i-1], fit_years[i]
    r_prev, r_curr = fit_rates[i-1], fit_rates[i]
    pct = (r_curr / r_prev - 1) * 100
    marker = ""
    if y_curr == 2022:
        marker = "  <-- 2022 papers were written pre-ChatGPT (launched Nov 30, 2022)"
    elif y_curr == 2023:
        marker = "  <-- first year of papers possibly influenced by ChatGPT"
    print(f"  {y_prev} -> {y_curr}: {r_prev:.2f} -> {r_curr:.2f} ({pct:+.1f}%){marker}")

# compare pre-ChatGPT slope (2021->2022) vs post-ChatGPT slope (2023->2024)
pre_slope = np.log(fit_rates[1]) - np.log(fit_rates[0])
post_slope = np.log(fit_rates[3]) - np.log(fit_rates[2])
print("\n=== Pre vs post-ChatGPT slope comparison ===")
print(f"  Pre-ChatGPT (2021->2022) log-rate slope:  {pre_slope:+.4f}")
print(f"  Post-ChatGPT (2023->2024) log-rate slope: {post_slope:+.4f}")
if post_slope > pre_slope:
    print("  Post slope is LESS negative -> decline DECELERATED after ChatGPT.")
else:
    print("  Post slope is MORE negative -> decline ACCELERATED after ChatGPT.")

# plot
fig, ax = plt.subplots(figsize=(9, 6))

# show all years (including the excluded 2020) for visual context
all_years = sorted(per_year)
all_rates = [per_year[y][2] for y in all_years]
colors = ["lightgray" if y == 2020 else "steelblue" for y in all_years]
ax.scatter(all_years, all_rates, c=colors, s=80, zorder=3,
           label="Yearly rate (2020 excluded from fit)")

# fitted trend line
trend_x = np.linspace(2021, 2024, 100)
trend_y = np.exp(fit.slope * trend_x + fit.intercept)
ax.plot(trend_x, trend_y, "--", color="orange",
        label=f"Linear trend 2021-2024 ({annual_change_pct:+.1f}%/yr)")

ax.axvline(x=2022.92, color="red", linestyle=":", label="ChatGPT launch (Nov 2022)")
ax.set_title("Mutual citation rate trajectory: secular trend or ChatGPT break?")
ax.set_xlabel("Year")
ax.set_ylabel("Mutual pairs per 1000 papers")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("outputs/trajectory.png", dpi=150)
print("\nSaved chart to outputs/trajectory.png")
