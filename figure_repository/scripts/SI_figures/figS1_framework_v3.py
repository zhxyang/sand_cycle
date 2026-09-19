# -*- coding: utf-8 -*-
"""
fig_S1_framework_v3.py
----------------------
Regenerate Fig S1: Schematic calculation framework diagram
Corrected database labels:
  - Database A1 (GREI): PRIMARY source — annual sedimentation volumes (555,960 reservoirs)
  - Database A2 (GDW): Spatial backbone — locations, storage capacity (35,295 reservoirs)
  - Database B: Sedimentation rates & cumulative capacity loss (literature, 508 reservoirs)
  - Database C: Sand fraction of deposited sediment (literature, 16 obs, median 20.1%)
  - Output: Annual sand trapping flux + Cumulative sand stock
"""

import sys, io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
from datetime import datetime

today = datetime.today().strftime('%Y_%m_%d')
BASE    = Path(r"C:\path\to\sand_cycle")
OUT_PNG = BASE / f"visuals/fig_S1_framework_v3_{today}.png"
OUT_PDF = BASE / f"visuals/fig_S1_framework_v3_{today}.pdf"

plt.rcParams.update({'font.family': 'Arial', 'font.size': 9})

fig, ax = plt.subplots(figsize=(11, 4.8))
ax.set_xlim(0, 11)
ax.set_ylim(0, 4.8)
ax.axis('off')

# ── Colors ────────────────────────────────────────────────────────────────
C_A1  = '#2166ac'   # GREI — primary (dark blue)
C_A2  = '#4393c3'   # GDW — spatial backbone (mid blue)
C_B   = '#74a9cf'   # Database B — sedimentation rates (blue-grey)
C_C   = '#e8f4f8'   # Database C — sand fraction (very light, dashed border)
C_EST = '#1a9641'   # Estimation step (green)
C_OUT = '#f4a582'   # Outputs (orange)
DARK  = '#222222'
GREY  = '#888888'

def box(ax, x, y, w, h, fc, lines, fs=8.5, tc='white',
        ec='#444444', lw=1.3, ls='-'):
    rect = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08',
                          facecolor=fc, edgecolor=ec, linewidth=lw,
                          linestyle=ls, zorder=3)
    ax.add_patch(rect)
    if isinstance(lines, str):
        lines = lines.split('\n')
    n = len(lines)
    for i, line in enumerate(lines):
        yy = y + h * (n - i) / (n + 0.6)
        fw = 'bold' if i == 0 else 'normal'
        fs_i = fs + 0.5 if i == 0 else fs - 0.5
        ax.text(x + w/2, yy, line, ha='center', va='center',
                fontsize=fs_i, color=tc, fontweight=fw, zorder=4)

def arr(ax, x1, y1, x2, y2, color='#444444', lw=1.5, ls='-'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=lw, mutation_scale=13,
                                linestyle=ls), zorder=5)

# ══════════════════════════════════════════════════════════════════════════
# ROW 1  —  Input databases  (y = 3.1 .. 4.35)
# ══════════════════════════════════════════════════════════════════════════
BH = 1.15   # box height

# A1 GREI — primary
box(ax, 0.15, 3.15, 2.55, BH, C_A1,
    ['Database A1: GREI', '555,960 reservoirs',
     'Annual sedimentation volume', '(primary source)'],
    tc='white')

# A2 GDW — spatial backbone
box(ax, 3.0, 3.15, 2.55, BH, C_A2,
    ['Database A2: GDW', '35,295 large reservoirs',
     'Spatial locations &', 'storage capacity'])

# B — sedimentation rates (literature)
box(ax, 5.85, 3.15, 2.55, BH, C_B,
    ['Database B: Literature', '508 reservoirs; 68 studies',
     'Sedimentation rates &', 'cumulative capacity loss'],
    tc='white')

# C — sand fraction (literature, dashed border)
box(ax, 8.7, 3.15, 2.15, BH, C_C,
    ['Database C', 'Sand fraction of deposits',
     '16 obs; median 20.1%'],
    tc='#444444', ec='#2166ac', lw=1.2, ls='--')

# ══════════════════════════════════════════════════════════════════════════
# ROW 2  —  Estimation step  (y = 1.6 .. 2.8)
# ══════════════════════════════════════════════════════════════════════════

# Main estimation box (A1 + C -> sand mass)
box(ax, 1.5, 1.6, 5.5, 1.1, C_EST,
    ['Sand trapping estimation',
     'Per reservoir: sedimentation volume x sand fraction x bulk density',
     'Aggregated globally and by AR6 region (annual & cumulative)'])

# GDW cross-check box (A2 + B, dashed)
box(ax, 7.8, 1.6, 3.05, 1.1, '#d9f0a3',
    ['GDW cross-validation',
     'Independent capacity-based approach',
     'Confirms GREI-based estimate'],
    tc='#2d6a0a', ec='#78c679', lw=1.2, ls='--')

# ══════════════════════════════════════════════════════════════════════════
# ROW 3  —  Outputs  (y = 0.2 .. 1.3)
# ══════════════════════════════════════════════════════════════════════════

box(ax, 0.5, 0.2, 3.3, 1.05, C_OUT,
    ['Annual sand trapping flux',
     'Global & regional aggregation',
     'Annual + cumulative estimates'],
    tc=DARK)

box(ax, 4.3, 0.2, 3.3, 1.05, C_OUT,
    ['Spatial distribution',
     'Proximity to built-up areas',
     'Coupling with sand demand'],
    tc=DARK)

# ══════════════════════════════════════════════════════════════════════════
# ARROWS
# ══════════════════════════════════════════════════════════════════════════

# A1 -> estimation (primary, thick)
arr(ax, 1.425, 3.15, 2.8, 2.7, color=C_A1, lw=2.0)
# A2 -> estimation (for spatial)
arr(ax, 4.275, 3.15, 4.3, 2.7, color=C_A2, lw=1.6)
# C -> estimation (sand fraction)
arr(ax, 9.775, 3.15, 5.7, 2.7, color='#2166ac', lw=1.6)
# B -> GDW cross-check (dashed)
arr(ax, 7.125, 3.15, 8.8, 2.7, color='#78c679', lw=1.2, ls='--')
# A2 -> GDW cross-check (dashed)
arr(ax, 4.275, 3.15, 8.32, 2.7, color='#78c679', lw=1.2, ls='--')
# estimation -> output 1
arr(ax, 3.0, 1.6, 2.15, 1.25, color=C_OUT, lw=1.6)
# estimation -> output 2
arr(ax, 5.25, 1.6, 5.95, 1.25, color=C_OUT, lw=1.6)

# ── Footer ────────────────────────────────────────────────────────────────
ax.text(0.15, 0.06,
        'Solid arrows: primary data flow.   Dashed arrows: validation/cross-check.   '
        'GREI = Global Reservoir and Evaporation Insights (Liu et al., Nat. Sustain. 2025).',
        fontsize=7, color=GREY, ha='left', va='bottom', style='italic')

fig.savefig(str(OUT_PNG), dpi=300, bbox_inches='tight', facecolor='white')
fig.savefig(str(OUT_PDF), bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"Saved: {OUT_PNG.name}")
print(f"Saved: {OUT_PDF.name}")
