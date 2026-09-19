# -*- coding: utf-8 -*-
"""
fig_SI_cdf_distance_v2.py
-------------------------
SI figure: Trapping-weighted CDF of reservoir distance to
(a) nearest built-up area (GHSL) and
(b) nearest construction sand demand pixel (any demand > 0).
Two curves on one panel. High-demand (>1 Mt/yr) curve dropped.
Reads pre-computed CSVs — no raster re-processing needed.
"""

import sys, io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from datetime import datetime

today = datetime.today().strftime('%Y_%m_%d')
BASE = Path(r"C:\path\to\sand_cycle")
CSV_DEMAND = BASE / "data/GDW_enriched/reservoir_demand_exposure_v7_2026_06_15.csv"
CSV_GHSL   = BASE / "data/built-up areas/metrics_outputs/grei_distance_to_built_2026_06_17.csv"
OUT_PNG    = BASE / f"visuals/fig_SI_cdf_distance_v2_{today}.png"
OUT_PDF    = BASE / f"visuals/fig_SI_cdf_distance_v2_{today}.pdf"

plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 12,
    'axes.labelsize': 13,
    'axes.titlesize': 12,
    'legend.fontsize': 11.5,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'figure.dpi': 300,
    'savefig.dpi': 600,
})

# ── Load data ─────────────────────────────────────────────────────────────
print("Loading demand CSV ...")
dd = pd.read_csv(str(CSV_DEMAND))
trap_d   = dd['annual_sand_t'].values
dist_any = dd['dist_any_km'].values
total_d  = trap_d.sum()

print("Loading GHSL proximity CSV ...")
dg = pd.read_csv(str(CSV_GHSL))
trap_g    = dg['sand_Gtyr'].values * 1e9   # Gt -> t
dist_ghsl = dg['dist_to_built_km'].values
total_g   = trap_g.sum()

# ── CDF: demand ───────────────────────────────────────────────────────────
sidx_d = np.argsort(dist_any)
cum_d   = np.cumsum(trap_d[sidx_d]) / total_d * 100
x_d     = dist_any[sidx_d]

med_d = x_d[np.searchsorted(cum_d, 50)]
p75_d = x_d[np.searchsorted(cum_d, 75)]
p90_d = x_d[np.searchsorted(cum_d, 90)]

# ── CDF: built-up (GHSL) ─────────────────────────────────────────────────
sidx_g = np.argsort(dist_ghsl)
cum_g   = np.cumsum(trap_g[sidx_g]) / total_g * 100
x_g     = dist_ghsl[sidx_g]

med_g = x_g[np.searchsorted(cum_g, 50)]
p75_g = x_g[np.searchsorted(cum_g, 75)]
p90_g = x_g[np.searchsorted(cum_g, 90)]

# Unweighted median for reference
uw_med_g = np.median(dist_ghsl)

print(f"Demand    — median: {med_d:.0f} km | P75: {p75_d:.0f} km | P90: {p90_d:.0f} km")
print(f"Built-up  — median: {med_g:.0f} km | P75: {p75_g:.0f} km | P90: {p90_g:.0f} km")
print(f"Built-up unweighted median: {uw_med_g:.1f} km")

# ── Plot ──────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7.5, 5.2))
fig.subplots_adjust(left=0.13, right=0.97, top=0.93, bottom=0.13)

COLOR_DEM  = '#2166ac'   # blue  — demand
COLOR_GHSL = '#7b3294'   # purple — built-up

ax.plot(x_d, cum_d, color=COLOR_DEM,  lw=2.2,
        label='Nearest construction\ndemand pixel')
ax.plot(x_g, cum_g, color=COLOR_GHSL, lw=2.2, ls='--',
        label='Nearest built-up area\n(GHSL)')

# Horizontal reference lines
for pct, ls in [(50, '--'), (75, ':'), (90, ':')]:
    ax.axhline(pct, color='0.70', lw=0.8, ls=ls, zorder=0)
    ax.text(502, pct + 1, f'{pct}%', fontsize=10, color='0.55', va='bottom')

# Vertical annotations — demand
ax.axvline(med_d, color=COLOR_DEM,  lw=0.9, ls='--', alpha=0.55)
ax.axvline(p75_d, color=COLOR_DEM,  lw=0.9, ls=':',  alpha=0.55)
ax.text(med_d + 5, 3, f'Median\n{med_d:.0f} km',
        fontsize=10, color=COLOR_DEM, va='bottom')

# Vertical annotations — built-up
ax.axvline(med_g, color=COLOR_GHSL, lw=0.9, ls='--', alpha=0.55)
ax.text(med_g + 5, 55, f'Median\n{med_g:.0f} km',
        fontsize=10, color=COLOR_GHSL, va='bottom')

ax.set_xlim(0, 500)
ax.set_ylim(0, 101)
ax.set_xlabel('Distance (km)', fontsize=13)
ax.set_ylabel('Cumulative % of annual sand trapping\n(trapping-weighted)', fontsize=12)
ax.set_title('Geographic proximity of reservoir sand trapping\n'
             'to built-up areas and construction sand demand', fontsize=11.5, pad=8)

ax.legend(loc='lower right', framealpha=0.92, edgecolor='0.75',
          handlelength=1.8)
ax.grid(True, alpha=0.22, lw=0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

fig.savefig(str(OUT_PNG), dpi=600, bbox_inches='tight', facecolor='white')
fig.savefig(str(OUT_PDF), bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"\nSaved: {OUT_PNG.name}")
print(f"Saved: {OUT_PDF.name}")
