# -*- coding: utf-8 -*-
"""
fig3a_map_v2.py
---------------
Fig 3a (main text): all 555,960 GREI reservoirs overlaid on demand raster.
Reservoir points binned into 6 discrete tiers by annual sand trapping (Mt/yr).

Changes from variants_v1 / V1:
  - Single panel, clean publication layout (no title annotation)
  - Panel label "a" top-left
  - All labels use $^{-1}$ math mode (no Unicode superscript ⁻¹)
  - Colorbar label uses LaTeX math for units
  - dpi=600 for print quality
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

BASE = Path(r"C:\path\to\sand_cycle")
GREI_CSV = BASE / "data/GREI_sand_trapping_v1.csv"
TIF_50K = BASE / "data" / "sand-demand-2023-2025-BAU-50km.tif"
OUTDIR   = BASE / "visuals"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ── Coordinate transform ──────────────────────────────────────────────────
A_LON, B_LON =  1.813219, 336.0412
A_LAT, B_LAT = -2.393761, 163.6901

# ── Style ─────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':   'Arial',
    'font.size':     15,
    'axes.labelsize': 16,
    'pdf.fonttype':  42,
    'ps.fonttype':   42,
})

# ── Load demand raster ────────────────────────────────────────────────────
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
print(f"  {nrows}x{ncols}, total {float(np.nansum(demand_Mt))/1000:.1f} Gt/yr")

# ── Load GREI ─────────────────────────────────────────────────────────────
print("Loading GREI...")
df = pd.read_csv(GREI_CSV, low_memory=False)
df = df.dropna(subset=['Longitude', 'Latitude', 'sand_Gtyr']).copy()
df = df[df['sand_Gtyr'] > 0].copy()
df['trap_Mt'] = df['sand_Gtyr'] * 1000.0
print(f"  n = {len(df):,}  |  total = {df['sand_Gtyr'].sum():.2f} Gt/yr")

# ── World borders ─────────────────────────────────────────────────────────
print("Loading world borders...")
world = gpd.read_file(
    'https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip')
world = world[world['CONTINENT'] != 'Antarctica']

# ── Bin definitions ───────────────────────────────────────────────────────
BINS   = [0,    0.01,  0.1,   1,     10,    100,   1e9]
LABELS = ['<0.01', '0.01–0.1', '0.1–1', '1–10', '10–100', '>100']
COLORS = ['#c7e9b4', '#7fcdbb', '#41b6c4', '#2c7fb8', '#253494', '#081d58']
SIZES  = [0.5,        2,          7,         20,         50,         130]
ALPHAS = [0.25,       0.40,       0.62,      0.82,       0.92,       0.97]

df['bin'] = pd.cut(df['trap_Mt'], bins=BINS, labels=LABELS, right=False)

# Print bin counts for verification
print("\nBin counts:")
for lbl in LABELS:
    sub = df[df['bin'] == lbl]
    trap_share = sub['sand_Gtyr'].sum() / df['sand_Gtyr'].sum() * 100
    print(f"  {lbl:12s}: n={len(sub):7,}  ({trap_share:.1f}% of trapping)")

# ── Figure ────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 7))
fig.subplots_adjust(left=0.02, right=0.88, top=0.97, bottom=0.03)

# Demand raster background
im = ax.imshow(demand_Mt, extent=EXTENT,
               origin='upper', aspect='auto',
               cmap='YlOrRd', norm=LogNorm(vmin=0.05, vmax=50),
               alpha=0.55, zorder=1)

# Country borders
world.boundary.plot(ax=ax, linewidth=0.25, color='0.50', zorder=2)

# Reservoir points — smallest first so large ones render on top
for lbl, col, sz, al in zip(LABELS, COLORS, SIZES, ALPHAS):
    sub = df[df['bin'] == lbl]
    if sub.empty:
        continue
    ax.scatter(sub['Longitude'], sub['Latitude'],
               s=sz, c=col, alpha=al, linewidths=0, zorder=3,
               rasterized=(sz < 10))

# Map extent
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 85)
ax.axis('off')

# Panel label
ax.text(0.005, 0.99, 'a', transform=ax.transAxes,
        fontsize=20, fontweight='bold', va='top', ha='left')

# ── Legend (reservoir bins) ───────────────────────────────────────────────
leg_handles = [
    mpatches.Patch(facecolor=c,
                   label=r'$\mathregular{' + l.replace('–', r'-') + r'}$'
                         r' Mt yr$^{-1}$')
    for l, c in zip(LABELS, COLORS)
]
ax.legend(handles=leg_handles,
          title=r'Annual sand trapping (Mt yr$^{-1}$)',
          title_fontsize=14, fontsize=13,
          loc='lower left', bbox_to_anchor=(0.005, 0.01),
          frameon=True, framealpha=0.93, edgecolor='0.6',
          ncol=2, columnspacing=0.8, handlelength=1.2)

# ── Demand colorbar ───────────────────────────────────────────────────────
cax = fig.add_axes([0.895, 0.22, 0.010, 0.58])
cbar = plt.colorbar(im, cax=cax)
cbar.set_label(r'Construction sand demand (Mt yr$^{-1}$ per 50-km pixel)',
               fontsize=14)
cbar.ax.tick_params(labelsize=13)

# ── Save ──────────────────────────────────────────────────────────────────
out_png = OUTDIR / f'fig3a_map_v2_{today_str}.png'
out_pdf = OUTDIR / f'fig3a_map_v2_{today_str}.pdf'
fig.savefig(str(out_png), dpi=600, bbox_inches='tight', facecolor='white')
fig.savefig(str(out_pdf),           bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"\nSaved: {out_png.name}")
print(f"Saved: {out_pdf.name}")
