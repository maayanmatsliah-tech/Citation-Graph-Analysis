"""
Visualize the OpenAlex sample-composition drift for §5.6 of the paper.

The same fields show wildly different paper counts across years in our
200k-per-year sample (Math −77%, Engineering +43%, etc.). Total per-year
is constant by construction, so the mix must be shifting. This chart
shows the dramatic shifts side by side with a normalized view that puts
shrinking and growing fields on the same axis.

Fields to highlight:
  - Shrinking: Mathematics, Psychology, Social Sciences, Earth & Planetary
  - Growing:   Engineering, Energy, Materials Science, Chemical Engineering

These are the fields whose year-to-year counts make per-field cross-year
comparisons unreliable in this dataset.
"""

import duckdb
import matplotlib.pyplot as plt

con = duckdb.connect("data/citations.duckdb", read_only=True)

# Pull paper counts by field by year
rows = con.execute("""
    SELECT field, year, COUNT(*)
    FROM works
    WHERE year BETWEEN 2020 AND 2024 AND field IS NOT NULL
    GROUP BY field, year
""").fetchall()

by_field = {}
for f, y, n in rows:
    by_field.setdefault(f, {})[y] = n

years = list(range(2020, 2025))

# The dramatic shifters
SHRINKING = ["Mathematics", "Psychology", "Social Sciences", "Earth and Planetary Sciences"]
GROWING = ["Engineering", "Energy", "Materials Science", "Chemical Engineering"]

# Color palettes — distinct, colorful
shrink_colors = ["#d62728", "#ff7f0e", "#e377c2", "#8c564b"]   # red, orange, pink, brown
grow_colors   = ["#1f77b4", "#2ca02c", "#9467bd", "#17becf"]   # blue, green, purple, teal

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left panel: raw paper counts (log scale to fit both magnitudes)
ax = axes[0]
for field, color in zip(SHRINKING, shrink_colors):
    vals = [by_field[field][y] for y in years]
    ax.plot(years, vals, "o-", color=color, linewidth=2.5, markersize=8, label=field)
for field, color in zip(GROWING, grow_colors):
    vals = [by_field[field][y] for y in years]
    ax.plot(years, vals, "s--", color=color, linewidth=2.5, markersize=8, label=field)

ax.axvline(x=2022.92, color="red", linestyle=":", linewidth=1.5, alpha=0.7,
           label="ChatGPT launch")
ax.set_yscale("log")
ax.set_title("Paper counts by field, 2020–2024 (log scale)")
ax.set_xlabel("Year")
ax.set_ylabel("Papers per year in 200k sample")
ax.set_xticks(years)
ax.grid(True, alpha=0.3, which="both")
ax.legend(fontsize=8, ncol=2, loc="lower left")

# Right panel: indexed to 100 at 2020 — shows directional drift on common axis
ax = axes[1]
for field, color in zip(SHRINKING, shrink_colors):
    base = by_field[field][2020]
    vals = [by_field[field][y] / base * 100 for y in years]
    pct = (vals[-1] - 100)
    ax.plot(years, vals, "o-", color=color, linewidth=2.5, markersize=8,
            label=f"{field} ({pct:+.0f}%)")
for field, color in zip(GROWING, grow_colors):
    base = by_field[field][2020]
    vals = [by_field[field][y] / base * 100 for y in years]
    pct = (vals[-1] - 100)
    ax.plot(years, vals, "s--", color=color, linewidth=2.5, markersize=8,
            label=f"{field} ({pct:+.0f}%)")

ax.axhline(y=100, color="black", linestyle="-", linewidth=0.5, alpha=0.5)
ax.axvline(x=2022.92, color="red", linestyle=":", linewidth=1.5, alpha=0.7,
           label="ChatGPT launch")
ax.set_title("Field counts indexed to 2020 = 100\n(real-world impossible — drift is an ingestion artifact)")
ax.set_xlabel("Year")
ax.set_ylabel("Papers (2020 = 100)")
ax.set_xticks(years)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=8, ncol=2, loc="upper left")

plt.tight_layout()
plt.savefig("outputs/field_drift.png", dpi=150)
print("Saved chart to outputs/field_drift.png")

# Print the actual numbers for the paper text
print("\nField counts by year:")
print(f"{'field':<42}" + "".join(f"{y:>8}" for y in years) + f"{'change':>10}")
for field in SHRINKING + GROWING:
    counts = [by_field[field][y] for y in years]
    pct = (counts[-1] / counts[0] - 1) * 100
    print(f"  {field:<40}" + "".join(f"{c:>8,}" for c in counts) + f"{pct:>+9.1f}%")
