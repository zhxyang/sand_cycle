# -*- coding: utf-8 -*-
"""
fig_jim9_trapping_vs_size_v7.py
--------------------------------
Fig S3: Annual reservoir sand trapping vs. storage capacity + Lorenz curves

Data: GREI_sand_trapping_v1.csv (555,960 reservoirs) — consistent with main analysis
Style: v6 visual style (marginal histograms, R10 region colours, boxed Lorenz annotations)
"""

import sys, io, warnings
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
from scipy import stats
from pathlib import Path
from datetime import datetime

today_str = datetime.today().strftime("%Y_%m_%d")

BASE     = Path(r"C:\path\to\sand_cycle")
GREI_CSV = BASE / "data/GREI_sand_trapping_v1.csv"
REG_CSV  = BASE / "data/regions/Mapping_GDW_reservior_country_to_R10.csv"
OUTDIR   = BASE / "visuals"
OUTDIR.mkdir(parents=True, exist_ok=True)

SAND_DENSITY = 1.6  # t/m3

# ── R10 region colours (same as v6) ───────────────────────────────────────
REGION_COLORS = {
    "Eastern Asia":                           "#e41a1c",
    "Southern Asia":                          "#ff7f00",
    "South-East Asia and developing Pacific": "#984ea3",
    "Asia-Pacific Developed":                 "#a65628",
    "Middle East":                            "#f781bf",
    "Africa":                                 "#4daf4a",
    "Europe":                                 "#377eb8",
    "Eurasia":                                "#00bcd4",
    "North America":                          "#1b7837",
    "Latin America and Caribbean":            "#d95f02",
}
REGION_ABBR = {
    "Eastern Asia":                           "E. Asia",
    "Southern Asia":                          "S. Asia",
    "South-East Asia and developing Pacific": "SE Asia & dev. Pac.",
    "Asia-Pacific Developed":                 "Asia-Pac. Dev.",
    "Middle East":                            "Middle East",
    "Africa":                                 "Africa",
    "Europe":                                 "Europe",
    "Eurasia":                                "Eurasia",
    "North America":                          "N. America",
    "Latin America and Caribbean":            "Lat. Am. & Carib.",
}

# Name fixes for unmatched GREI countries
NAME_FIXES = {
    "RUSSIAN FEDERATION":   "Russia",
    "CZECH REPUBLIC":       "Czech Republic",
    "SRILANKA":             "Sri Lanka",
    "VIET NAM":             "Viet Nam",
    "SYRIAN ARAB REPUBLIC": "Syrian Arab Republic",
    "KOREA, REPUBLIC OF":   "Korea, Republic of",
    "KOREA,DEMOCRATIC PEOPLE'S REPUBLIC OF": "Korea, Dem. People's Rep.",
    "CONGO,THE DEMOCRATIC REPUBLIC OF THE":  "Congo, Dem. Rep.",
    "CANARIAS":             "Spain",
    "SOUTH SUDAN":          "South Sudan",
    "JAMAICA":              "Jamaica",
    "MALTA":                "Europe",   # direct AR6 fallback
}

# ── Style ─────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":       "sans-serif",
    "font.sans-serif":   ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size":         11,
    "axes.labelsize":    13,
    "axes.titlesize":    12,
    "xtick.labelsize":   11,
    "ytick.labelsize":   11,
    "axes.linewidth":    0.9,
    "xtick.major.width": 0.9,
    "ytick.major.width": 0.9,
    "xtick.minor.width": 0.6,
    "ytick.minor.width": 0.6,
    "legend.fontsize":   11,
    "pdf.fonttype":      42,
    "ps.fonttype":       42,
})

# ── Load & merge region ───────────────────────────────────────────────────
df  = pd.read_csv(GREI_CSV, low_memory=False)
reg = pd.read_csv(REG_CSV)[["COUNTRY", "AR6_10"]].drop_duplicates()

df["key"]  = df["Country"].str.upper().str.strip()
reg["key"] = reg["COUNTRY"].str.upper().str.strip()

# Apply name fixes before merge
for bad, good in NAME_FIXES.items():
    # If good is an AR6_10 value (direct fallback), assign directly
    if good in REGION_COLORS:
        df.loc[df["key"] == bad, "key"] = "__DIRECT__" + bad
    else:
        df.loc[df["key"] == bad, "key"] = good.upper()

df = df.merge(reg[["key", "AR6_10"]], on="key", how="left")

# Direct AR6 fallbacks
for bad, ar6 in NAME_FIXES.items():
    if ar6 in REGION_COLORS:
        df.loc[df["key"] == "__DIRECT__" + bad, "AR6_10"] = ar6

df["AR6_10"] = df["AR6_10"].fillna("Unknown")

df["Volume_MCM"] = df["Volume"] * 100.0
df["trap_Mt"]    = df["sand_Gtyr"] * 1000.0

df_valid     = df[(df["Volume_MCM"] > 0) & (df["trap_Mt"] > 0)].copy()
total_trap_Gt = df_valid["sand_Gtyr"].sum()

print(f"N valid = {len(df_valid):,}  |  Total = {total_trap_Gt:.2f} Gt/yr")
print(f"Region coverage: {(df_valid['AR6_10'] != 'Unknown').sum()/len(df_valid)*100:.1f}%")

# Pareto stats
pareto = {}
for pct in [1, 5, 10]:
    thr   = df_valid["Volume_MCM"].quantile(1 - pct / 100)
    big   = df_valid[df_valid["Volume_MCM"] >= thr]
    share = big["sand_Gtyr"].sum() / total_trap_Gt * 100
    pareto[pct] = (thr, share, len(big))
    print(f"  Top {pct}% ({len(big):,} res, >={thr:.1f} MCM): {share:.1f}% of trapping")

# ── Lorenz helper ─────────────────────────────────────────────────────────
def lorenz_curve(cap_vals, trap_vals):
    order  = np.argsort(cap_vals)
    w_sort = trap_vals[order]
    w_cum  = np.cumsum(w_sort) / np.sum(w_sort)
    x_cum  = np.arange(1, len(cap_vals) + 1) / len(cap_vals)
    return x_cum * 100, w_cum * 100

# ── Figure layout: single panel (Lorenz only) ─────────────────────────────
fig, ax_B = plt.subplots(1, 1, figsize=(7.5, 6.2), layout="constrained")

# ── Panel b Lorenz ────────────────────────────────────────────────────────
region_order_B = sorted(
    REGION_COLORS.keys(),
    key=lambda r: df_valid[df_valid["AR6_10"] == r]["sand_Gtyr"].sum(),
    reverse=True
)

for region in region_order_B:
    grp = df_valid[df_valid["AR6_10"] == region].sort_values("Volume_MCM")
    if len(grp) < 20:
        continue
    xc, yc = lorenz_curve(grp["Volume_MCM"].values, grp["sand_Gtyr"].values)
    ax_B.plot(xc, yc, color=REGION_COLORS[region], linewidth=1.4,
              alpha=0.78, zorder=4, label=REGION_ABBR[region])

# Global curve on top
xg, yg = lorenz_curve(df_valid["Volume_MCM"].values, df_valid["sand_Gtyr"].values)
ax_B.plot(xg, yg, color="black", linewidth=2.4, zorder=8, label="Global")

# Perfect equality
ax_B.plot([0, 100], [0, 100], color="0.50", linewidth=1.0,
          linestyle="--", zorder=3, label="Perfect equality")

# Shaded area
ax_B.fill_between(xg, yg, xg, color="#ddeeff", alpha=0.40, zorder=1)

# Reference lines with boxed annotations (v6 style)
ref_cfg = [
    (1,  ":",  97, "right"),
    (5,  "-.", 88, "right"),
    (10, "--", 78, "left"),
]
for pct, ls, y_lbl, ha in ref_cfg:
    x_line = 100 - pct
    share  = pareto[pct][1]
    ax_B.axvline(x_line, color="#bbbbbb", linewidth=0.8, linestyle=ls, zorder=2)
    x_offset = -1.2 if ha == "right" else 1.2
    ax_B.text(x_line + x_offset, y_lbl,
              f"top {pct}%\n= {share:.0f}%",
              ha=ha, va="top", fontsize=11, color="#444444",
              bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.80",
                        alpha=0.90, linewidth=0.6))

ax_B.set_xlabel("Cumulative share of reservoirs\n(%, small \u2192 large by capacity)")
ax_B.set_ylabel("Cumulative share of annual sand trapping (%)")
ax_B.set_xlim(0, 100); ax_B.set_ylim(0, 100)
ax_B.xaxis.set_major_formatter(mticker.FormatStrFormatter("%g%%"))
ax_B.yaxis.set_major_formatter(mticker.FormatStrFormatter("%g%%"))
ax_B.xaxis.set_major_locator(mticker.MultipleLocator(20))
ax_B.yaxis.set_major_locator(mticker.MultipleLocator(20))
ax_B.spines["top"].set_visible(False)
ax_B.spines["right"].set_visible(False)
ax_B.grid(linestyle=":", alpha=0.25, linewidth=0.5)
ax_B.set_axisbelow(True)

ax_B.text(-0.10, 1.04, "a", transform=ax_B.transAxes,
          fontsize=15, fontweight="bold", va="top")

# Legend below panel b
leg_handles_B = (
    [Line2D([0], [0], color="black", linewidth=2.4, label="Global")]
    + [Line2D([0], [0], color=REGION_COLORS[r], linewidth=1.4,
               alpha=0.78, label=REGION_ABBR[r])
       for r in region_order_B]
    + [Line2D([0], [0], color="0.65", linewidth=1.0,
               linestyle="--", label="Perfect equality")]
)
ax_B.legend(handles=leg_handles_B,
            loc="upper center", bbox_to_anchor=(0.5, -0.14),
            fontsize=11, frameon=True, framealpha=0.92, edgecolor="0.55",
            ncol=4, columnspacing=0.7, handletextpad=0.4, borderpad=0.5)

# ── Save ──────────────────────────────────────────────────────────────────
out_png = OUTDIR / f"fig_jim9_trapping_vs_size_v7_{today_str}.png"
out_pdf = OUTDIR / f"fig_jim9_trapping_vs_size_v7_{today_str}.pdf"
fig.savefig(out_png, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(out_pdf,           bbox_inches="tight", facecolor="white")
plt.close(fig)

print(f"\nSaved: {out_png.name}")
