# -*- coding: utf-8 -*-
"""
fig_SI_map_top10pct_v3.py
--------------------------
v2 -> v3: legend labels no longer repeat units; unit kept in title only.
"""

import sys, io, warnings
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LogNorm
import tifffile
from pathlib import Path
from datetime import datetime

today_str = datetime.today().strftime('%Y_%m_%d')

BASE     = Path(r"C:\path\to\sand_cycle")
GREI_CSV = BASE / "data/GREI_sand_trapping_v1.csv"
TIF_50K = BASE / "data" / "sand-demand-2023-2025-BAU-50km.tif"
OUTDIR   = BASE / "visuals"
OUTDIR.mkdir(parents=True, exist_ok=True)

A_LON, B_LON =  1.813219, 336.0412
A_LAT, B_LAT = -2.393761, 163.6901

plt.rcParams.update({
    'font.family':    'Arial',
    'font.size':      15,
    'axes.labelsize': 16,
    'pdf.fonttype':   42,
    'ps.fonttype':    42,
})

# ── Load demand raster ────────────────────────────────────────────────────────
print("Loading demand raster...")
with tifffile.TiffFile(str(TIF_50K)) as t:
    dem_raw = t.asarray().astype(np.float32)
dem_annual = dem_raw / 3.0
nrows, ncols = dem_annual.shape
demand_Mt = dem_annual / 1e6
demand_Mt[demand_Mt <= 0] = np.nan

lon_min = (0      - B_LON) / A_LON
lon_max = (ncols  - B_LON) / A_LON
lat_max = (0      - B_LAT) / A_LAT
lat_min = (nrows  - B_LAT) / A_LAT
EXTENT = [lon_min, lon_max, lat_min, lat_max]

# ── Load GREI, filter top 10% ─────────────────────────────────────────────────
print("Loading GREI...")
df = pd.read_csv(GREI_CSV, low_memory=False)
df = df.dropna(subset=['Longitude', 'Latitude', 'sand_Gtyr']).copy()
df = df[df['sand_Gtyr'] > 0].copy()
df['trap_Mt']    = df['sand_Gtyr'] * 1000.0
df['Volume_MCM'] = df['Volume'] * 100.0

total_trap_Gt = df['sand_Gtyr'].sum()
thr_10pct     = df['Volume_MCM'].quantile(0.90)
df_top10      = df[df['Volume_MCM'] >= thr_10pct].copy()
pct_trap_10   = df_top10['sand_Gtyr'].sum() / total_trap_Gt * 100
print(f"  Top 10% (>={thr_10pct:.1f} MCM): n={len(df_top10):,}, {pct_trap_10:.1f}% of trapping")

# ── World borders ──────────────────────────────────────────────────────────────
print("Loading world borders...")
world = gpd.read_file(
    'https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip')
world = world[world['CONTINENT'] != 'Antarctica']

# ── Figure ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 7))
fig.subplots_adjust(left=0.02, right=0.88, top=0.97, bottom=0.03)

im = ax.imshow(demand_Mt, extent=EXTENT,
               origin='upper', aspect='auto',
               cmap='YlOrRd', norm=LogNorm(vmin=0.05, vmax=50),
               alpha=0.55, zorder=1)

world.boundary.plot(ax=ax, linewidth=0.25, color='0.50', zorder=2)

BINS   = [0,    0.01,  0.1,   1,     10,    100,   1e9]
LABELS = ['<0.01', '0.01–0.1', '0.1–1', '1–10', '10–100', '>100']
COLORS = ['#c7e9b4', '#7fcdbb', '#41b6c4', '#2c7fb8', '#253494', '#081d58']
SIZES  = [2,         6,          18,        45,         100,        220]
ALPHAS = [0.35,      0.55,       0.70,      0.85,       0.92,       0.97]

df_top10['bin'] = pd.cut(df_top10['trap_Mt'], bins=BINS, labels=LABELS, right=False)

for lbl, col, sz, al in zip(LABELS, COLORS, SIZES, ALPHAS):
    sub = df_top10[df_top10['bin'] == lbl]
    if sub.empty:
        continue
    ax.scatter(sub['Longitude'], sub['Latitude'],
               s=sz, c=col, alpha=al, linewidths=0, zorder=3)

ax.set_xlim(-180, 180)
ax.set_ylim(-60, 85)
ax.axis('off')

# ── Legend: unit in title only, not repeated in each label ───────────────────
leg_handles = [
    mpatches.Patch(facecolor=c,
                   label=r'$\mathregular{' + l.replace('–', r'-') + r'}$')
    for l, c in zip(LABELS, COLORS)
]
ax.legend(handles=leg_handles,
          title=r'Annual sand trapping (Mt yr$^{-1}$)',
          title_fontsize=14, fontsize=13,
          loc='lower left', bbox_to_anchor=(0.005, 0.01),
          frameon=True, framealpha=0.93, edgecolor='0.6',
          ncol=2, columnspacing=0.8, handlelength=1.2)

# ── Colorbar ──────────────────────────────────────────────────────────────────
cax1 = fig.add_axes([0.895, 0.22, 0.010, 0.58])
cb1  = plt.colorbar(im, cax=cax1)
cb1.set_label(r'Construction sand demand (Mt yr$^{-1}$ per 50-km pixel)',
              fontsize=14)
cb1.ax.tick_params(labelsize=13)

# ── Save ──────────────────────────────────────────────────────────────────────
out_png = OUTDIR / f'fig_SI_map_top10pct_v3_{today_str}.png'
out_pdf = OUTDIR / f'fig_SI_map_top10pct_v3_{today_str}.pdf'
fig.savefig(str(out_png), dpi=300, bbox_inches='tight', facecolor='white')
fig.savefig(str(out_pdf),           bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"\nSaved: {out_png.name}")
print(f"Saved: {out_pdf.name}")
