"""
Visualize the citation-breadth rise that supports §5.7 of the paper.

For each citing year, compute the average number of *distinct* OpenAlex
fields appearing in each citing paper's reference list, across three
subsets of the data:

  (a) Full sample of all citing papers in 2020-2024.
  (b) Citing papers restricted to 15 fields whose paper counts in our
      200k-per-year sample are stable or growing across the window. This
      controls for the OpenAlex sample-composition drift documented in
      §5.6.
  (c) Citing papers restricted to Computer Science alone. CS is the
      largest field whose paper count grows steadily and monotonically
      across all five years, so its measurement is anchored against
      classification drift.

The rise should appear in all three subsets. 2020 is shown for context
but is the COVID outlier excluded from the headline comparison (§5.4).
"""

import duckdb
import numpy as np
import matplotlib.pyplot as plt

con = duckdb.connect("data/citations.duckdb", read_only=True)

STABLE = [
    "Computer Science", "Engineering", "Materials Science", "Chemistry",
    "Chemical Engineering", "Physics and Astronomy", "Energy",
    "Environmental Science", "Biochemistry, Genetics and Molecular Biology",
    "Agricultural and Biological Sciences", "Immunology and Microbiology",
    "Decision Sciences", "Pharmacology, Toxicology and Pharmaceutics",
    "Nursing", "Veterinary",
]


def avg_breadth_by_year(citing_field_filter_sql, params):
    """Returns {year: avg_distinct_cited_fields} for the given citing-field filter."""
    rows = con.execute(f"""
        WITH per_paper AS (
            SELECT c.citing_id, wc.year, COUNT(DISTINCT wd.field) AS n_fields
            FROM citations c
            JOIN works wc ON c.citing_id = wc.id
            JOIN works wd ON c.cited_id  = wd.id
            WHERE c.citing_id <> c.cited_id
              AND wc.year BETWEEN 2020 AND 2024
              AND wd.year BETWEEN 2020 AND 2024
              AND wd.field IS NOT NULL
              {citing_field_filter_sql}
            GROUP BY c.citing_id, wc.year
        )
        SELECT year, AVG(n_fields) FROM per_paper GROUP BY year ORDER BY year
    """, params).fetchall()
    return dict(rows)


print("Computing avg distinct cited fields per citing paper by year...")
full_sample = avg_breadth_by_year("AND wc.field IS NOT NULL", [])
ph = ",".join(["?"] * len(STABLE))
stable = avg_breadth_by_year(f"AND wc.field IN ({ph})", STABLE)
cs = avg_breadth_by_year("AND wc.field = ?", ["Computer Science"])

years = sorted(full_sample.keys())
print(f"\n{'year':<6}{'full':>10}{'stable':>10}{'CS only':>10}")
for y in years:
    print(f"{y:<6}{full_sample[y]:>10.3f}{stable[y]:>10.3f}{cs[y]:>10.3f}")

# ---- Chart ----
fig, ax = plt.subplots(figsize=(9, 6))

# 2020 styled differently to mark as COVID outlier
for series, color, marker, label in [
    (full_sample, "steelblue", "o", "Full sample"),
    (stable,      "darkorange", "s", "Stable-volume fields (15)"),
    (cs,          "seagreen",   "^", "Computer Science only"),
]:
    vals = [series[y] for y in years]
    # solid line for 2021-2024, dashed segment to 2020 to mark exclusion
    ax.plot(years[1:], vals[1:], marker=marker, color=color, linewidth=2,
            markersize=8, label=label)
    ax.plot([years[0], years[1]], [vals[0], vals[1]], color=color,
            linewidth=1.5, linestyle=":", alpha=0.6)
    ax.scatter([years[0]], [vals[0]], color=color, marker=marker, s=60,
               facecolors="white", edgecolors=color, linewidths=2,
               zorder=3)

ax.axvline(x=2022.92, color="red", linestyle=":", linewidth=1.5,
           label="ChatGPT launch (Nov 2022)")

# annotation explaining 2020 markers
ax.annotate("2020 (open markers): COVID outlier,\nexcluded from headline comparison",
            xy=(2020, full_sample[2020]), xytext=(2020.05, 1.0),
            fontsize=9, color="gray",
            arrowprops=dict(arrowstyle="->", color="gray", lw=0.8))

ax.set_title("Citation breadth: avg distinct cited fields per citing paper, 2020–2024")
ax.set_xlabel("Citing year")
ax.set_ylabel("Avg number of distinct fields cited")
ax.set_xticks(years)
ax.set_ylim(bottom=0)
ax.grid(True, alpha=0.3)
ax.legend(loc="lower right", fontsize=10)

plt.tight_layout()
plt.savefig("outputs/citation_breadth.png", dpi=150)
print("\nSaved chart to outputs/citation_breadth.png")
