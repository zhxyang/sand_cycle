# -*- coding: utf-8 -*-
"""
fig_S2_GHSL_overlay_v2.py
--------------------------
v1 -> v2: Use identical bin/color/size/alpha scheme as Fig 3a
          (fig3_separate_panels_v1.py).
          Units: Mt yr-1 (not Mm3 yr-1 as in v1).
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
from matplotlib.colors import PowerNorm
from pathlib import Path
from datetime import datetime
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from rasterio.crs import CRS

today_str = datetime.today().strftime('%Y_%m_%d')

BASE     = Path(r"C:\path\to\sand_cycle")
GREI_CSV = BASE / "data/GREI_sand_trapping_v1.csv"
GHSL_TIF = (BASE / "data/built-up areas"
            / "GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0"
            / "GHS_BUILT_S_E2030_GLOBE_R2023A_54009_100_V1_0.tif")
OUTDIR   = BASE / "visuals"
OUTDIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.family':    'Arial',
    'font.size':      15,
    'axes.labelsize': 16,
    'pdf.fonttype':   42,
    'ps.fonttype':    42,
})

# ── Bin/color/size scheme — identical to Fig 3a ───────────────────────────────
BINS   = [0,    0.01,  0.1,   1,     10,    100,   1e9]
LABELS = ['<0.01', '0.01\u20130.1', '0.1\u20131', '1\u201310', '10\u2013100', '>100']
COLORS = ['#c7e9b4', '#7fcdbb', '#41b6c4', '#2c7fb8', '#253494', '#081d58']
SIZES  = [0.5,        2,          7,         20,         50,         130]
ALPHAS = [0.25,       0.40,       0.62,      0.82,       0.92,       0.97]

# ── Load GREI ─────────────────────────────────────────────────────────────────
print("Loading GREI...")
df = pd.read_csv(str(GREI_CSV), low_memory=False)
df = df.dropna(subset=['Longitude', 'Latitude', 'sand_Gtyr']).copy()
df = df[(df['Latitude'].between(-60, 85)) & (df['sand_Gtyr'] > 0)].copy()
df['trap_Mt'] = df['sand_Gtyr'] * 1000.0
df['bin'] = pd.cut(df['trap_Mt'], bins=BINS, labels=LABELS, right=False)
print(f"  Reservoirs: {len(df):,}  |  Total: {df['sand_Gtyr'].sum():.2f} Gt/yr")

# ── World borders ─────────────────────────────────────────────────────────────
print("Loading world borders...")
world = gpd.read_file(
    'https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip')
world = world[world['CONTINENT'] != 'Antarctica']

# ── GHSL raster ───────────────────────────────────────────────────────────────
print("Reprojecting GHSL raster...")
TARGET_RES_DEG = 0.25
dst_crs       = CRS.from_epsg(4326)
dst_transform = from_origin(-180.0, 90.0, TARGET_RES_DEG, TARGET_RES_DEG)
dst_width     = int(360.0 / TARGET_RES_DEG)
dst_height    = int(180.0 / TARGET_RES_DEG)
ghsl = np.full((dst_height, dst_width), np.nan, dtype=np.float32)
with rasterio.open(str(GHSL_TIF)) as src:
    reproject(source=rasterio.band(src, 1), destination=ghsl,
              src_transform=src.transform, src_crs=src.crs,
              dst_transform=dst_transform, dst_crs=dst_crs,
              resampling=Resampling.average, dst_nodata=np.nan)
vmax_ghsl = float(np.nanpercentile(ghsl[np.isfinite(ghsl)], 98.0))
norm_ghsl = PowerNorm(gamma=0.25, vmin=0.0, vmax=vmax_ghsl)

# ── Figure ────────────────────────────────────────────────────────────────────
print("Plotting...")
fig, ax = plt.subplots(figsize=(16, 7))
fig.subplots_adjust(left=0.02, right=0.98, top=0.97, bottom=0.03)

ax.imshow(ghsl, extent=(-180, 180, -90, 90), origin='upper',
          cmap='Greys', norm=norm_ghsl, alpha=0.65, zorder=1,
          interpolation='nearest', aspect='auto')

world.boundary.plot(ax=ax, linewidth=0.25, color='0.50', zorder=2)

for lbl, col, sz, al in zip(LABELS, COLORS, SIZES, ALPHAS):
    sub = df[df['bin'] == lbl]
    if sub.empty:
        continue
    ax.scatter(sub['Longitude'], sub['Latitude'],
               s=sz, c=col, alpha=al, linewidths=0, zorder=3,
               rasterized=(sz < 10))

ax.set_xlim(-180, 180)
ax.set_ylim(-60, 85)
ax.axis('off')

# ── Legend — identical style to Fig 3a ───────────────────────────────────────
leg_handles = [
    mpatches.Patch(facecolor=c, label=l)
    for l, c in zip(LABELS, COLORS)
]
ax.legend(handles=leg_handles,
          title=r'Annual sand trapping (Mt yr$^{-1}$)',
          title_fontsize=13, fontsize=11,
          loc='lower left', bbox_to_anchor=(0.01, 0.01),
          frameon=True, framealpha=0.92, ncol=2,
          handlelength=1.0, handletextpad=0.4,
          columnspacing=0.6, borderpad=0.4)

# ── Save ──────────────────────────────────────────────────────────────────────
out_png = OUTDIR / f'fig_S2_GHSL_GREI_overlay_v2_{today_str}.png'
out_pdf = OUTDIR / f'fig_S2_GHSL_GREI_overlay_v2_{today_str}.pdf'
fig.savefig(str(out_png), dpi=300, bbox_inches='tight', facecolor='white')
fig.savefig(str(out_pdf),           bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"\nSaved: {out_png.name}")
print(f"Saved: {out_pdf.name}")
