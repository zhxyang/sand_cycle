# -*- coding: utf-8 -*-
"""
fig_S6_demand_sensitivity_v1.py

Sensitivity of global construction sand demand to sand-to-cement ratio.
Two-panel figure:
  a) Bar chart: demand estimate at ratio = 1.5, 2.0, 2.5, 3.0, 3.5, 4.0
     with trapping central estimate overlaid as horizontal line
  b) Ratio chart: trapping-to-demand ratio at each scenario,
     with "trapping > demand" threshold marked
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from pathlib import Path
from datetime import datetime

today_str = datetime.today().strftime("%Y_%m_%d")

BASE = Path(r"C:\path\to\sand_cycle")
DEM_PATH = BASE / "data/cement/sand_use_R10_2020.csv"
OUTDIR   = BASE / "visuals"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":       "sans-serif",
    "font.sans-serif":   ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size":         11,
    "axes.labelsize":    12,
    "axes.titlesize":    11,
    "xtick.labelsize":   10.5,
    "ytick.labelsize":   10.5,
    "axes.linewidth":    0.9,
    "xtick.major.width": 0.9,
    "ytick.major.width": 0.9,
    "pdf.fonttype":      42,
    "ps.fonttype":       42,
})

# ── Load cement data ───────────────────────────────────────────────────────
dem = pd.read_csv(DEM_PATH)
global_row = dem[dem["AR6_10"] == "Global"].iloc[0]

# Central demand uses ratio=2.5; scale linearly for other ratios
# demand = cement_consumption * ratio * density_factor
# Since demand_central = cement * 2.5 * factor, demand(r) = demand_central * (r / 2.5)
demand_central_base = global_row["sand_2020"] / 1e6   # Gt/yr at ratio=2.5

# Trapping central estimate
trapping_central = 21.86   # Gt/yr (P50 x P50)
trapping_low     = 6.3
trapping_high    = 152.0

# Sand-to-cement ratios to evaluate
ratios = np.array([1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
ratio_labels = ["1.5", "2.0", "2.5\n(central)", "3.0", "3.5", "4.0"]

# Demand scales linearly with ratio
demands = demand_central_base * (ratios / 2.5)   # Gt/yr

# Trapping-to-demand ratio
t2d = trapping_central / demands

# Literature context for ratio ranges
# Standard concrete (M15-M25): 1:2:4 vol → sand:cement mass ~2.0-2.5
# Low-grade / mortar-heavy construction: up to 3.5-4.0
# High-strength concrete (M40+): ~1.5-2.0
# Sources: standard mix design tables; Montoya et al. 2023 PNAS (concrete sand demand)

# ── Figure ─────────────────────────────────────────────────────────────────
fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5.5),
                                  layout="constrained",
                                  gridspec_kw={"width_ratios": [1, 1]})

x = np.arange(len(ratios))
bar_w = 0.55

# Colour bars: highlight central, shade others
bar_colors = ["#aec7e8"] * len(ratios)
bar_colors[2] = "#1f77b4"   # central = darker blue

# ── Panel a: Demand estimates ──────────────────────────────────────────────
bars = ax_a.bar(x, demands, width=bar_w,
                color=bar_colors, edgecolor="white",
                linewidth=0.6, zorder=3)

# Value labels on bars
for xi, d in zip(x, demands):
    ax_a.text(xi, d + 0.15, f"{d:.1f}",
              ha="center", va="bottom", fontsize=10, color="#333333")

# Trapping central line + uncertainty band
ax_a.axhline(trapping_central, color="#d62728", linewidth=2.0,
             linestyle="-", zorder=5, label=f"Annual trapping (central: {trapping_central:.1f} Gt/yr)")
ax_a.axhspan(trapping_low, trapping_high,
             color="#d62728", alpha=0.08, zorder=2,
             label=f"Trapping range (P10\u00d7P10\u2013P90\u00d7P90: {trapping_low:.0f}\u2013{trapping_high:.0f} Gt/yr)")

ax_a.set_xticks(x)
ax_a.set_xticklabels(ratio_labels, fontsize=10)
ax_a.set_xlabel("Sand-to-cement mass ratio", labelpad=7)
ax_a.set_ylabel(r"Construction sand demand (Gt yr$^{-1}$)", labelpad=7)
ax_a.set_ylim(0, max(demands) * 1.25)
ax_a.spines["top"].set_visible(False)
ax_a.spines["right"].set_visible(False)
ax_a.grid(axis="y", linestyle=":", alpha=0.25, linewidth=0.5)
ax_a.set_axisbelow(True)

# Legend
legend_handles = [
    mpatches.Patch(facecolor="#1f77b4", edgecolor="white", label="Central ratio (2.5)"),
    mpatches.Patch(facecolor="#aec7e8", edgecolor="white", label="Alternative ratios"),
    Line2D([0], [0], color="#d62728", linewidth=2.0, label=f"Annual trapping: {trapping_central:.1f} Gt/yr"),
    mpatches.Patch(facecolor="#d62728", alpha=0.15, edgecolor="none",
                   label=f"Trapping range: {trapping_low:.0f}\u2013{trapping_high:.0f} Gt/yr"),
]
ax_a.legend(handles=legend_handles, loc="upper left",
            fontsize=9, frameon=True, framealpha=0.92,
            edgecolor="0.6", handlelength=1.5)

# Mix design context annotation
ax_a.text(0.98, 0.97,
          "Mix design context:\n"
          "High-strength concrete (M40+): ~1.5\u20132.0\n"
          "Standard concrete (M15\u2013M25): ~2.0\u20132.5\n"
          "Mortar / low-grade construction: ~3.0\u20134.0",
          transform=ax_a.transAxes, ha="right", va="top",
          fontsize=8.5, color="#444444",
          bbox=dict(boxstyle="round,pad=0.4", fc="white",
                    ec="0.7", alpha=0.92))

ax_a.text(-0.12, 1.04, "a", transform=ax_a.transAxes,
          fontsize=15, fontweight="bold", va="top")

# ── Panel b: Trapping-to-demand ratio ─────────────────────────────────────
# Colour by whether trapping > demand
t2d_colors = ["#2ca02c" if v >= 1.0 else "#d62728" for v in t2d]
t2d_colors[2] = "#1a7a1a"   # darker green for central

bars_b = ax_b.bar(x, t2d, width=bar_w,
                  color=t2d_colors, edgecolor="white",
                  linewidth=0.6, zorder=3)

# Value labels
for xi, v in zip(x, t2d):
    ax_b.text(xi, v + 0.03, f"{v:.1f}\u00d7",
              ha="center", va="bottom", fontsize=10, color="#333333")

# Threshold line at 1.0
ax_b.axhline(1.0, color="black", linewidth=1.6,
             linestyle="--", zorder=5, label="Trapping = demand (1:1)")

# Uncertainty band for trapping (P10/P90 at central demand)
t2d_low  = trapping_low  / demands
t2d_high = trapping_high / demands
ax_b.fill_between(x, t2d_low, t2d_high,
                  color="#888888", alpha=0.12, zorder=2,
                  label="Trapping uncertainty (P10\u00d7P10\u2013P90\u00d7P90)")

ax_b.set_xticks(x)
ax_b.set_xticklabels(ratio_labels, fontsize=10)
ax_b.set_xlabel("Sand-to-cement mass ratio", labelpad=7)
ax_b.set_ylabel("Annual trapping / construction demand (ratio)", labelpad=7)
ax_b.set_ylim(0, max(t2d_high) * 1.15)
ax_b.spines["top"].set_visible(False)
ax_b.spines["right"].set_visible(False)
ax_b.grid(axis="y", linestyle=":", alpha=0.25, linewidth=0.5)
ax_b.set_axisbelow(True)

# "Trapping exceeds demand" label
ax_b.text(0.98, 0.97, "Trapping exceeds demand\nacross all ratio scenarios",
          transform=ax_b.transAxes, ha="right", va="top",
          fontsize=9, color="#2ca02c",
          bbox=dict(boxstyle="round,pad=0.35", fc="white",
                    ec="#2ca02c", alpha=0.92, lw=0.8))

legend_b = [
    Line2D([0], [0], color="black", linewidth=1.6, linestyle="--",
           label="Trapping = demand"),
    mpatches.Patch(facecolor="#888888", alpha=0.20, edgecolor="none",
                   label="Trapping uncertainty range"),
]
ax_b.legend(handles=legend_b, loc="upper right",
            fontsize=9, frameon=True, framealpha=0.92, edgecolor="0.6")

ax_b.text(-0.12, 1.04, "b", transform=ax_b.transAxes,
          fontsize=15, fontweight="bold", va="top")

# ── Save ───────────────────────────────────────────────────────────────────
out_png = OUTDIR / f"fig_S6_demand_sensitivity_v1_{today_str}.png"
out_pdf = OUTDIR / f"fig_S6_demand_sensitivity_v1_{today_str}.pdf"
fig.savefig(out_png, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(out_pdf,           bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {out_png.name}")

# Print table for reference
print("\nTable S2 values:")
print(f"{'Ratio':>6}  {'Demand (Gt/yr)':>15}  {'Trapping/Demand':>16}")
for r, d, v in zip(ratios, demands, t2d):
    print(f"{r:>6.1f}  {d:>15.1f}  {v:>16.1f}x")
