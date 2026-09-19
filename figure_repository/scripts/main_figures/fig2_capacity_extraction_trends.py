
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 27 09:46:53 2025

@author: zhongx

UPDATED:
- Uses enriched GDW file (GDW_enriched_rates_YYYY_MM_DD.csv)
- Uses reservoir-specific annual sedimentation rates (annual_rate_final) instead of a global r
- Computes effective capacity time series as sum of cohort decays per reservoir:
    Eff(t) = sum_i C_i * (1 - r_i)^(t - year_i), for year_i <= t
- Computes annual sedimentation loss as:
    Loss(t) = sum_i Eff_i(t-1) * r_i
"""

import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.patches import Rectangle
import matplotlib.ticker as mticker
from matplotlib.ticker import StrMethodFormatter
from pathlib import Path

today_str = datetime.today().strftime("%Y_%m_%d")

# =============================

# Set the local path to the repository
BASE = Path(r"C:\path\to\sand_cycle")

grand_shp = BASE / "data" / "GRanD_Version_1_3" / "GRanD_reservoirs_v1_3.shp"

gdw_csv = (
    BASE
    / "data"
    / "GDW_enriched"
    / "GDW_enriched_rates_2026_02_01.csv"
)

out_dir = BASE / "visuals"
out_dir.mkdir(parents=True, exist_ok=True)

# Fallback if annual_rate_final has missing values (should be rare)
FALLBACK_GLOBAL_R = 0.0036  # 0.36%/yr (only used if annual_rate_final missing)

# =============================
# Read GRanD (optional for this plot, but kept as in your script)
# =============================
gdf_reservoir_GRanD_13 = gpd.read_file(grand_shp)
df_reservoir_GRanD_13 = gdf_reservoir_GRanD_13.drop(columns="geometry")

print(df_reservoir_GRanD_13.shape)
print(df_reservoir_GRanD_13.columns)
print(df_reservoir_GRanD_13.head())

# =============================
# Read enriched GDW / GDM reservoir table
# =============================
df_reservoir_GDM = pd.read_csv(gdw_csv, low_memory=False)
print(df_reservoir_GDM.head())
print("Loaded enriched GDW:", gdw_csv)

# =============================
# Plot the capacity trends
# enriched GDW (df_reservoir_GDM) + detailed-rate sedimentation effective capacity
# + linked zoom panel (Nature-style)
# =============================

# --- global style ---
plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 14,
    "axes.labelsize": 14,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
    "axes.linewidth": 1.0,
    "pdf.fonttype": 42,  # embed TrueType fonts in PDF
    "ps.fonttype": 42
})

df = df_reservoir_GDM.copy()

# -----------------------------
# Helper: pick a column by priority list (case-insensitive)
# -----------------------------
def pick_col(df_in, candidates):
    cols = {c.lower(): c for c in df_in.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None

# -----------------------------
# 1) Identify year + capacity + rate columns
# -----------------------------
year_col = pick_col(df, ["YEAR_DAM", "Year_dam", "YEAR", "Year"])
cap_col = pick_col(df, ["CAP_MCM", "Cap_mcm", "CAP_REP", "Cap_rep", "CAP_KM3", "Cap_km3"])
rate_col = pick_col(df, ["annual_rate_final", "annual_rate", "ANNUAL_RATE_FINAL", "ANNUAL_RATE"])

if year_col is None:
    raise KeyError("Could not find a dam year column (expected YEAR_DAM or similar).")
if cap_col is None:
    print("Capacity-like columns found:", [c for c in df.columns if "cap" in c.lower()])
    raise KeyError("Could not auto-detect a capacity column (expected CAP_MCM/CAP_REP/CAP_KM3).")
if rate_col is None:
    raise KeyError(
        "Could not find a detailed annual sedimentation rate column. "
        "Expected 'annual_rate_final' from GDW_enriched_rates_*.csv."
    )

print("Using columns:", {"year_col": year_col, "cap_col": cap_col, "rate_col": rate_col})

# -----------------------------
# 2) Clean year, capacity, and rates
# -----------------------------
year = pd.to_numeric(df[year_col], errors="coerce")
year = year.replace(-99, np.nan)            # GDW missing code
year = year.where(year.between(1800, 2022)) # data-faithful for your file (observed max ~2022)

cap = pd.to_numeric(df[cap_col], errors="coerce")

# Convert capacity to km³ if needed
if ("km3" in cap_col.lower()) or cap_col.lower().endswith("km3"):
    cap_km3 = cap
else:
    cap_km3 = cap / 1000.0  # MCM -> km³

r_i = pd.to_numeric(df[rate_col], errors="coerce")

# Fallback if missing (should be minimal given hierarchy fill)
n_missing_r = int(r_i.isna().sum())
if n_missing_r > 0:
    print(f"WARNING: {n_missing_r} rows have missing {rate_col}. Filling with FALLBACK_GLOBAL_R={FALLBACK_GLOBAL_R}.")
    r_i = r_i.fillna(FALLBACK_GLOBAL_R)

# Clip for numerical sanity (rates are fractions per year)
r_i = r_i.clip(lower=0.0, upper=0.99)

mask = year.notna() & cap_km3.notna() & (cap_km3 > 0) & r_i.notna()

d = pd.DataFrame({
    "year": year[mask].astype(int),
    "cap_km3": cap_km3[mask].astype(float),
    "r": r_i[mask].astype(float),
})

print("Records used (known year & positive capacity & rate):", len(d))
print("Max year used:", int(d["year"].max()))
print("Rate summary (fraction/yr):", d["r"].describe(percentiles=[0.1, 0.5, 0.9]).to_dict())

# -----------------------------
# 3) Annual additions + nominal cumulative capacity
# -----------------------------
annual_add = d.groupby("year")["cap_km3"].sum().sort_index()

start_year = int(annual_add.index.min())
end_year = int(annual_add.index.max())  # likely 2022
all_years = np.arange(start_year, end_year + 1)

annual_add_full = annual_add.reindex(all_years, fill_value=0.0)
nominal_cum = annual_add_full.cumsum()

# Smoothed annual additions (optional)
annual_add_smooth = annual_add_full.rolling(5, center=True, min_periods=1).mean()

# -----------------------------
# 4) Effective capacity after sedimentation (detailed rates)
# Eff(t) = sum_i C_i * (1 - r_i)^(t - year_i), for year_i <= t
# Annual loss(t) = sum_i Eff_i(t-1) * r_i
# -----------------------------
yrs = d["year"].to_numpy(dtype=int)
caps = d["cap_km3"].to_numpy(dtype=float)
rates = d["r"].to_numpy(dtype=float)

eff = pd.Series(index=all_years, dtype=float)
loss = pd.Series(index=all_years, dtype=float)

for t in all_years:
    active = yrs <= t
    if not np.any(active):
        eff.loc[t] = 0.0
        loss.loc[t] = 0.0
        continue

    age = (t - yrs[active]).astype(int)
    surv = np.power(1.0 - rates[active], age, dtype=float)
    eff_t = np.sum(caps[active] * surv)
    eff.loc[t] = eff_t

    if t == all_years[0]:
        loss.loc[t] = 0.0
    else:
        active_prev = yrs <= (t - 1)
        age_prev = ((t - 1) - yrs[active_prev]).astype(int)
        surv_prev = np.power(1.0 - rates[active_prev], age_prev, dtype=float)
        eff_prev_by_res = caps[active_prev] * surv_prev
        loss.loc[t] = float(np.sum(eff_prev_by_res * rates[active_prev]))

# -----------------------------
# 5) Sand & gravel extraction (km³/yr): interpolate + smooth
# -----------------------------
sand_points = pd.DataFrame({
    "year": [1900, 1920, 1940, 1960, 1980, 2000, 2020],
    "sand_km3": [0.4, 0.7, 1.3, 2.8, 5.6, 8.4, 11.0],
})

sand = (
    sand_points.set_index("year")["sand_km3"]
    .reindex(all_years)
    .interpolate(method="index")  # no extrapolation beyond endpoints
)
sand_smooth = sand.rolling(11, center=True, min_periods=1).mean()

# -----------------------------
# Plot styling (print-safe hierarchy)
# -----------------------------
nominal_style = dict(color="black", linewidth=2.8, solid_capstyle="round", solid_joinstyle="round")
effective_style = dict(color="0.35", linewidth=2.4, solid_capstyle="round", solid_joinstyle="round")
sand_style = dict(color="red", linestyle="--", linewidth=2.2, alpha=0.65,
                  solid_capstyle="round", solid_joinstyle="round")

panel_box = dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1.5)

# -----------------------------
# 6) Plot A+B: one figure with two linked panels
# IMPORTANT CHANGE: remove the red sand line from panel (a)
# -----------------------------
fig, (axA, axB) = plt.subplots(
    2, 1, sharex=True, figsize=(8.8, 7.8),
    gridspec_kw={"height_ratios": [3, 1.6]}
)

# Panel (a): full scale (capacity only)
axA.plot(nominal_cum.index, nominal_cum.values, label="Nominal cumulative capacity", **nominal_style)
axA.plot(eff.index, eff.values, label="Effective cumulative capacity after sedimentation", **effective_style)

axA.set_xlim(start_year, end_year)

# Light y-grid only + clean spines
axA.grid(True, axis="y", alpha=0.2)
axA.grid(False, axis="x")
axA.spines["top"].set_visible(False)
axA.spines["right"].set_visible(False)
axA.tick_params(direction="out", length=4, width=1)

# Format large numbers nicely (e.g., 1,000; 2,000; ...)
axA.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))

axA.set_ylabel("Reservoir capacity (km³)")

# Legend: only the two capacity curves
axA.legend(loc="upper left", bbox_to_anchor=(0.0, 0.90), frameon=False)

# Panel label
axA.text(0.01, 0.98, "(a)", transform=axA.transAxes, ha="left", va="top",
         fontsize=14, fontweight="bold", bbox=panel_box)

# Zoom box (kept commented as in your script)
zoom_ymin, zoom_ymax = 0, 12
zoom_xmin = max(1900, start_year)
zoom_xmax = end_year
# rect = Rectangle(
#     (zoom_xmin, zoom_ymin),
#     width=(zoom_xmax - zoom_xmin),
#     height=(zoom_ymax - zoom_ymin),
#     fill=False, linewidth=1.4, linestyle=":", alpha=0.9
# )
# axA.add_patch(rect)

# Panel (b): sand zoom
sand_plot = sand_smooth.dropna()
axB.plot(sand_plot.index, sand_plot.values, **sand_style)

axB.set_xlim(start_year, end_year)
axB.set_ylim(zoom_ymin, zoom_ymax)

axB.grid(True, axis="y", alpha=0.2)
axB.grid(False, axis="x")
axB.spines["top"].set_visible(False)
axB.spines["right"].set_visible(False)
axB.tick_params(direction="out", length=4, width=1)

axB.set_ylabel("Sand & gravel (km³ yr⁻¹)")
axB.text(0.01, 0.98, "(b)", transform=axB.transAxes, ha="left", va="top",
         fontsize=14, fontweight="bold", bbox=panel_box)

# Cleaner shared x ticks
axB.xaxis.set_major_locator(mticker.MultipleLocator(20))
axB.xaxis.set_minor_locator(mticker.MultipleLocator(10))

axB.set_xlabel("Year")

plt.tight_layout()

out_base = str(Path(out_dir) / f"historical_reservoir_capacity_GDM_vs_sand_extraction_linked_detailedRates_{today_str}")
plt.savefig(out_base + ".pdf", bbox_inches="tight")
plt.savefig(out_base + ".png", dpi=600, bbox_inches="tight")
plt.show()

# -----------------------------
# 7) Plot C: annual additions vs annual sedimentation losses
# -----------------------------
fig, ax = plt.subplots(figsize=(8.8, 4.9))

ax.plot(annual_add_smooth.index, annual_add_smooth.values,
        label="Annual additions (5-yr smooth)", **effective_style)

loss_style = dict(color="0.55", linestyle="--", linewidth=2.2,
                  solid_capstyle="round", solid_joinstyle="round")
ax.plot(loss.index, loss.values, label="Annual sedimentation loss", **loss_style)

ax.set_xlabel("Year")
ax.set_ylabel("km³ yr⁻¹")
ax.set_xlim(start_year, end_year)

ax.grid(True, axis="y", alpha=0.2)
ax.grid(False, axis="x")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(direction="out", length=4, width=1)
ax.legend(frameon=False)

plt.tight_layout()
plt.show()

# -----------------------------
# 8) Summary stats
# -----------------------------
end_nominal = float(nominal_cum.iloc[-1])
end_eff = float(eff.iloc[-1])
pct_remaining = end_eff / end_nominal * 100

# =============================
# 9) Global storage + sediment time series
# =============================

global_nominal_km3 = nominal_cum.copy()   # km³ (no sedimentation)
global_effective_km3 = eff.copy()         # km³ (after sedimentation)
global_sediment_stock_km3 = global_nominal_km3 - global_effective_km3  # km³ lost capacity

# Annual sedimentation loss is already 'loss' (km³/yr)
global_annual_sed_loss_km3yr = loss.copy()

# Optional: cumulative sediment derived from annual loss (km³)
global_sediment_cum_from_loss_km3 = global_annual_sed_loss_km3yr.cumsum()

# Optional sanity check (they should be very close; tiny differences can come from indexing/start-year handling)
max_abs_gap = (global_sediment_stock_km3 - global_sediment_cum_from_loss_km3).abs().max()
print(f"Max abs gap between (nominal-eff) and cumsum(loss): {max_abs_gap:.6f} km³")

# Pack into one table and export
global_ts = pd.DataFrame({
    "nominal_capacity_km3": global_nominal_km3,
    "effective_capacity_km3": global_effective_km3,
    "annual_sedimentation_loss_km3yr": global_annual_sed_loss_km3yr,
    "cumulative_sediment_km3": global_sediment_stock_km3,
    "cumulative_sediment_from_loss_km3": global_sediment_cum_from_loss_km3,
})

out_csv = Path(out_dir) / f"global_storage_and_sediment_timeseries_{today_str}.csv"
global_ts.to_csv(out_csv, index_label="year")
print("Saved:", out_csv)


print(f"End-year (data-faithful): {end_year}")
print(f"Nominal cumulative capacity (km³): {end_nominal:,.1f}")
print(f"Effective capacity (km³) (detailed {rate_col}): {end_eff:,.1f}")
print(f"Effective / nominal (%): {pct_remaining:.2f}%")
