# -*- coding: utf-8 -*-
"""
fig3c_scatter_v5.py

Fig. 3c: Regional scatter — annual sand demand vs annual reservoir sand trapping.
Sized to match Fig. 3 panels (a)+(b): width=8.8 in, font=14pt.
Uses GDW_enriched_rates_2026_04_30_brazil_fix.csv.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from matplotlib.lines import Line2D

today_str = datetime.today().strftime("%Y_%m_%d")

BASE = Path(r"C:\path\to\sand_cycle")
OUTDIR = BASE / "visuals"
OUTDIR.mkdir(parents=True, exist_ok=True)

GDW_PATH    = BASE / "data/GDW_enriched/GDW_enriched_rates_2026_04_30_brazil_fix.csv"
DEMAND_PATH = BASE / "data/cement/sand_use_R10_2020.csv"
RMAP_PATH   = BASE / "data/regions/Mapping_GDW_reservior_country_to_R10.csv"

DENSITY = 1.6  # t/m³

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 14,
    "axes.labelsize": 14,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
    "axes.linewidth": 1.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# ── Load and compute trapping ──────────────────────────────────────────────
df = pd.read_csv(GDW_PATH, low_memory=False)
for c in ["CAP_MCM", "annual_rate_final", "annual_rate_low", "annual_rate_high",
          "sand_friction_final", "sand_friction_low", "sand_friction_high"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["CAP_MCM", "annual_rate_final", "sand_friction_final"])

df["trap_c"] = df["CAP_MCM"] * df["annual_rate_final"] * df["sand_friction_final"] * DENSITY
df["trap_l"] = df["CAP_MCM"] * df["annual_rate_low"]   * df["sand_friction_low"]   * DENSITY
df["trap_h"] = df["CAP_MCM"] * df["annual_rate_high"]  * df["sand_friction_high"]  * DENSITY

# ── Map to AR6 regions ─────────────────────────────────────────────────────
rmap = pd.read_csv(RMAP_PATH)[["COUNTRY", "AR6_10"]].drop_duplicates()
df   = df.merge(rmap, on="COUNTRY", how="left")

trap = (df.groupby("AR6_10", dropna=False)[["trap_c","trap_l","trap_h"]]
          .sum().reset_index())

# Add Global row
trap = pd.concat([trap, pd.DataFrame({
    "AR6_10":  ["Global"],
    "trap_c":  [trap["trap_c"].sum()],
    "trap_l":  [trap["trap_l"].sum()],
    "trap_h":  [trap["trap_h"].sum()],
})], ignore_index=True)

# Convert Mt → Gt
for col in ["trap_c","trap_l","trap_h"]:
    trap[col] /= 1000

# ── Load demand ────────────────────────────────────────────────────────────
dem = pd.read_csv(DEMAND_PATH)
dem["dem_c"] = dem["sand_2020"]      / 1e6
dem["dem_h"] = dem["sand_2020_high"] / 1e6
dem["dem_l"] = dem["sand_2020_low"]  / 1e6

plot_df = trap.merge(dem[["AR6_10","dem_c","dem_h","dem_l"]], on="AR6_10", how="left")
plot_df = plot_df.dropna(subset=["dem_c"])

# ── Labels ─────────────────────────────────────────────────────────────────
abbr = {
    "Eastern Asia":                           "E. Asia",
    "Southern Asia":                          "S. Asia",
    "North America":                          "N. America",
    "Middle East":                            "Mid. East",
    "Latin America and Caribbean":            "Lat. Am.",
    "South-East Asia and developing Pacific": "SE Asia",
    "Asia-Pacific Developed":                 "Asia-Pac. Dev.",
    "Europe":                                 "Europe",
    "Africa":                                 "Africa",
    "Global":                                 "Global",
}
plot_df["label"] = plot_df["AR6_10"].map(lambda x: abbr.get(x, x))

# ── Plot ───────────────────────────────────────────────────────────────────
# Width=8.8 to match panels (a)+(b); height=7.0 for square-ish log-log axes
fig, ax = plt.subplots(figsize=(8.8, 7.0))

is_global = plot_df["AR6_10"] == "Global"
regions   = plot_df[~is_global]
glob_row  = plot_df[is_global]

# axis limits — log scale
all_vals = pd.concat([plot_df["dem_c"], plot_df["trap_c"]]).dropna()
lim_min = 0.05
lim_max = all_vals.max() * 2.5
ref = np.logspace(np.log10(lim_min), np.log10(lim_max), 100)
ax.plot(ref, ref, color="0.55", lw=1.2, ls="--", zorder=1, label="1:1 line")

# nudge offsets
nudge = {
    "E. Asia":        (  7,   5),
    "S. Asia":        (  7, -13),
    "N. America":     (  7,   5),
    "Mid. East":      (  7, -13),
    "Lat. Am.":       (  7,   5),
    "SE Asia":        (-80, -13),
    "Asia-Pac. Dev.": (  7,   5),
    "Europe":         (  7,   5),
    "Africa":         (  7,   5),
    "Eurasia":        (  7,   5),
}

for _, row in regions.iterrows():
    x = row["dem_c"]
    y = row["trap_c"]
    ax.scatter(x, y, color="#3182bd", s=70, alpha=0.85, zorder=3)
    ox, oy = nudge.get(row["label"], (7, 5))
    ax.annotate(row["label"], (x, y),
                textcoords="offset points", xytext=(ox, oy),
                fontsize=10, color="black", zorder=4)

for _, row in glob_row.iterrows():
    x = row["dem_c"]
    y = row["trap_c"]
    ax.scatter(x, y, color="#e6550d", s=110, marker="D", alpha=0.95, zorder=5)
    ax.annotate("Global", (x, y),
                textcoords="offset points", xytext=(7, 5),
                fontsize=10, fontweight="bold", color="#e6550d", zorder=6)

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Annual sand demand for concrete (Gt yr$^{-1}$)")
ax.set_ylabel("Annual reservoir sand trapping (Gt yr$^{-1}$)")
ax.set_xlim(lim_min, lim_max)
ax.set_ylim(lim_min, lim_max)
ax.set_aspect("equal", adjustable="box")
ax.grid(ls=":", alpha=0.35, lw=0.6, which="both")
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Panel label to match (a) and (b)
ax.text(0.01, 0.98, "(c)", transform=ax.transAxes, ha="left", va="top",
        fontsize=14, fontweight="bold",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1.5))

handles = [
    Line2D([0],[0], marker="o", ls="", color="#3182bd", ms=8, alpha=0.85, label="Region"),
    Line2D([0],[0], marker="D", ls="", color="#e6550d", ms=10, alpha=0.95, label="Global"),
    Line2D([0],[0], color="0.55", lw=1.2, ls="--", label="1:1 line (trapping = demand)"),
]
ax.legend(handles=handles, frameon=False, loc="upper left",
          bbox_to_anchor=(0.0, 0.90), fontsize=12)

plt.tight_layout()

out_png = OUTDIR / f"fig3c_scatter_v5_{today_str}.png"
out_pdf = OUTDIR / f"fig3c_scatter_v5_{today_str}.pdf"
fig.savefig(out_png, dpi=600, bbox_inches="tight", facecolor="white")
fig.savefig(out_pdf, bbox_inches="tight", facecolor="white")
plt.close(fig)

print(f"Saved: {out_png.name}")
print(f"Saved: {out_pdf.name}")
print()
print("Regional values (Gt/yr):")
print(plot_df[["label","dem_c","trap_c"]]
      .rename(columns={"dem_c":"demand","trap_c":"trap_central"})
      .to_string(index=False))
