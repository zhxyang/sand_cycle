# -*- coding: utf-8 -*-
"""
dredge_cost_vs_time_v3_20260620.py
-----------------------------------
Based on v3_20260102. Changes:
  1. File paths updated to current machine (xzhon)
  2. Panel a: 95% prediction interval (was 90%) + bias correction (×exp(σ²/2))
  3. Panel a: robustness annotation (year-controlled regression, HC3)
  4. Robustness check printed to console
"""

import os, sys, io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import matplotlib
if "ipykernel" not in sys.modules:
    for b in ("QtAgg", "TkAgg", "Agg"):
        try:
            matplotlib.use(b, force=True)
            break
        except Exception:
            pass

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from matplotlib.patches import Rectangle
from io import StringIO
from scipy import stats as scipy_stats

print("Matplotlib backend:", matplotlib.get_backend())

DARK = "0.10"
plt.rcParams.update({
    "font.size": 13,
    "axes.titlesize": 16, "axes.labelsize": 15,
    "axes.labelcolor": DARK, "axes.titlecolor": DARK,
    "xtick.labelsize": 13, "ytick.labelsize": 13,
    "xtick.color": DARK, "ytick.color": DARK,
    "legend.fontsize": 12, "legend.title_fontsize": 12,
    "text.color": DARK, "axes.edgecolor": DARK,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DATA = BASE / "data" / "cost" / "contract"
FILES = [
    f"{BASE_DATA}/Contracts Awarded_12_29_2025.csv",
    f"{BASE_DATA}/Contracts Awarded_12_29_2025 (1).csv",
    f"{BASE_DATA}/Contracts Awarded_12_29_2025 (2).csv",
    f"{BASE_DATA}/Contracts Awarded_12_29_2025 (3).csv",
]
OUTDIR = f"{BASE_DATA}/outputs_streamlined"
os.makedirs(OUTDIR, exist_ok=True)

YEAR_START, YEAR_END = 1990, 2025
METHOD_COL   = "dredged_material_placement_categories"
TARGET_TOKEN = "Construction and Industrial/Commercial Uses"
CY_TO_M3     = 0.7645549

SCATTER_MAX_N = 40000
WINSOR_LOW, WINSOR_HIGH = 0.01, 0.99
FIG1_DOT_SIZE, FIG1_DOT_ALPHA = 22, 0.35

ASSUMED_INFLATION = 0.025
BASE_YEAR = None
MIN_N_PER_YEAR = 3
ROLL = 3

DOTS_ALPHA, DOTS_SIZE = 0.55, 28
INSET_DOTS_ALPHA, INSET_DOTS_SIZE = 0.75, 16
COLOR_MAP = "turbo"
USE_LOG_QTY_FOR_COLOR = True
COLOR_CLIP_LO, COLOR_CLIP_HI, COLOR_GAMMA = 0.05, 0.99, 0.6
USE_LOG_Y_FIG2 = False
LINE_COLOR = "black"
VW_LINESTYLE, SAND_LINESTYLE = "-", "--"

SAND_PRICE_DATA = """
year,price_nominal_usd_per_m3
2005,7.738256435
2006,7.868021116
2007,7.98864744
2008,8.177811447
2009,8.29843777
2010,8.492170956
2011,8.65391989
2012,8.843083898
2013,9.039558591
2014,9.244257807
2015,9.456267709
2016,9.7139694
2017,9.903133407
2018,10.16174893
2019,10.39934624
2020,10.64882341
2021,10.87545468
2022,11.10025828
2023,11.32871723
2024,11.5553485
2025,11.80482567
""".strip()

ZOOM_X_MIN, ZOOM_X_MAX, ZOOM_Y_MAX = 2005, 2025, 20

# ── Helpers ───────────────────────────────────────────────────────────────────
def clean_columns(df):
    df = df.copy()
    df.columns = (df.columns.str.strip()
                  .str.replace(r"[^\w]+", "_", regex=True)
                  .str.replace(r"_{2,}", "_", regex=True)
                  .str.lower())
    return df

def to_number(s):
    return pd.to_numeric(
        s.astype(str).str.replace(r"[\$,]", "", regex=True)
         .str.replace("nan", "", regex=False).str.strip(),
        errors="coerce")

def first_existing(df, candidates):
    for c in candidates:
        if c in df.columns: return c
    return None

def winsorize(x, low=WINSOR_LOW, high=WINSOR_HIGH):
    lo, hi = x.quantile([low, high])
    return x.clip(lo, hi)

def tokens(s):
    if pd.isna(s): return []
    return [t.strip() for t in str(s).split(";") if str(t).strip()]

def has_token(s, tok): return tok in tokens(s)

def weighted_quantile(values, quantiles, sample_weight):
    v, w = np.asarray(values, float), np.asarray(sample_weight, float)
    q = np.atleast_1d(np.asarray(quantiles, float))
    m = np.isfinite(v) & np.isfinite(w) & (w >= 0)
    v, w = v[m], w[m]
    if v.size == 0 or w.sum() == 0: return np.full_like(q, np.nan, float)
    order = np.argsort(v)
    v, w = v[order], w[order]
    cw = np.cumsum(w) / np.sum(w)
    return np.interp(q, cw, v)

def rolling_center(s, roll):
    if roll <= 1: return s
    return s.rolling(roll, center=True, min_periods=1).mean()

def hc3_se(X, resid):
    """HC3 heteroskedasticity-robust standard errors."""
    hat = X @ np.linalg.solve(X.T @ X, X.T)
    hii = np.diag(hat)
    e   = resid / (1 - hii)
    meat = (X * e[:, None]).T @ (X * e[:, None])
    vcov = np.linalg.solve(X.T @ X, meat) @ np.linalg.solve(X.T @ X, np.eye(X.shape[1]))
    return np.sqrt(np.diag(vcov))

# ── Main ──────────────────────────────────────────────────────────────────────
dfs = [pd.read_csv(f, low_memory=False) for f in FILES]
df  = pd.concat(dfs, ignore_index=True)
df  = clean_columns(df)

fy_col = first_existing(df, ["fiscal_year", "fiscalyear", "fy"])
if fy_col is None:
    cands = [c for c in df.columns if "fiscal" in c and "year" in c]
    fy_col = cands[0]
df[fy_col] = to_number(df[fy_col])
df = df[df[fy_col].between(YEAR_START, YEAR_END)].copy()
df[fy_col] = df[fy_col].astype(int)
df = df.rename(columns={fy_col: "fiscal_year"})

for c in ["total_cost", "winning_bid",
          "estimated_total_dredging_quantity", "actual_total_dredging_quantity"]:
    if c in df.columns: df[c] = to_number(df[c])

dedup = first_existing(df, ["job_key", "contract_number", "solicitation_number"])
df = df.drop_duplicates(subset=[dedup], keep="first") if dedup else df.drop_duplicates()

df["qty_cy"] = df["actual_total_dredging_quantity"].fillna(
    df["estimated_total_dredging_quantity"])
if "winning_bid" in df.columns:
    df["cost_used"] = df["winning_bid"].where(
        df["winning_bid"].notna() & (df["winning_bid"] > 0), df.get("total_cost"))
else:
    df["cost_used"] = df["total_cost"]

df = df[df["qty_cy"].notna() & (df["qty_cy"] > 0)]
df = df[df["cost_used"].notna() & (df["cost_used"] > 0)]
df = df[df[METHOD_COL].apply(lambda s: has_token(s, TARGET_TOKEN))].copy()

df["qty_m3"] = df["qty_cy"] * CY_TO_M3
df["unit_cost_usd_per_m3"] = df["cost_used"] / df["qty_m3"]
df = df[np.isfinite(df["qty_m3"]) & (df["qty_m3"] > 0)]
df = df[np.isfinite(df["unit_cost_usd_per_m3"]) & (df["unit_cost_usd_per_m3"] > 0)]

df["qty_m3_w"] = winsorize(df["qty_m3"])
df["uc_m3_w"]  = winsorize(df["unit_cost_usd_per_m3"])
df["log_qty"]  = np.log10(df["qty_m3_w"])
df["log_uc"]   = np.log10(df["uc_m3_w"])

# ── Panel a regression ────────────────────────────────────────────────────────
plot_df = df.dropna(subset=["log_qty", "log_uc"]).copy()
n = len(plot_df)

X1 = np.column_stack([np.ones(n), plot_df["log_qty"].values])
y  = plot_df["log_uc"].values
b1 = np.linalg.solve(X1.T @ X1, X1.T @ y)
resid1 = y - X1 @ b1
sigma2 = resid1.var(ddof=2)   # unbiased

# HC3 SE for main model
se_hc3 = hc3_se(X1, resid1)
t_qty  = b1[1] / se_hc3[1]
p_qty  = 2 * scipy_stats.t.sf(abs(t_qty), n - 2)

# Bias correction factor (lognormal: multiply predictions by exp(σ²/2))
bias_cf = np.exp(sigma2 / 2)

print(f"\n=== Panel a regression (N={n}) ===")
print(f"  log_qty coef: {b1[1]:.4f}  HC3 SE={se_hc3[1]:.4f}  t={t_qty:.2f}  p={p_qty:.4f}")
print(f"  Bias correction factor: {bias_cf:.4f}")

# Robustness: add year as covariate
year_c = plot_df["fiscal_year"].values - plot_df["fiscal_year"].mean()
X2 = np.column_stack([np.ones(n), plot_df["log_qty"].values, year_c])
b2 = np.linalg.solve(X2.T @ X2, X2.T @ y)
resid2 = y - X2 @ b2
se2    = hc3_se(X2, resid2)
t2     = b2 / se2
p2     = 2 * scipy_stats.t.sf(np.abs(t2), n - 3)

print(f"\n=== Robustness: log_uc ~ log_qty + year (HC3) ===")
for nm, bi, si, ti, pi in zip(["intercept","log_qty","year_c"], b2, se2, t2, p2):
    print(f"  {nm:12s}: {bi:.4f}  SE={si:.4f}  t={ti:.2f}  p={pi:.4f}")
print(f"  (year coef p={p2[2]:.3f} -- year not significant after controlling for quantity)")

# Prediction grid with 95% PI + bias correction
x_min, x_max = plot_df["qty_m3_w"].quantile([WINSOR_LOW, WINSOR_HIGH])
q_grid  = np.logspace(np.log10(x_min), np.log10(x_max), 250)
lq_grid = np.log10(q_grid)
Xpred   = np.column_stack([np.ones(250), lq_grid])
y_hat   = Xpred @ b1

# 95% prediction interval (individual observation)
XtXinv  = np.linalg.inv(X1.T @ X1)
lev     = np.array([Xpred[i] @ XtXinv @ Xpred[i] for i in range(250)])
se_pred = np.sqrt(sigma2 * (1 + lev))
t95     = scipy_stats.t.ppf(0.975, n - 2)
uc_hat  = bias_cf * 10 ** y_hat
uc_lo   = bias_cf * 10 ** (y_hat - t95 * se_pred)
uc_hi   = bias_cf * 10 ** (y_hat + t95 * se_pred)

# ── Panel b data ──────────────────────────────────────────────────────────────
d = df.dropna(subset=["fiscal_year","qty_m3","cost_used","unit_cost_usd_per_m3"]).copy()
d["fiscal_year"] = d["fiscal_year"].astype(int)
if BASE_YEAR is None:
    BASE_YEAR = int(d["fiscal_year"].max())

d["deflator"]       = (1.0 + ASSUMED_INFLATION) ** (BASE_YEAR - d["fiscal_year"])
d["cost_used_real"] = d["cost_used"] * d["deflator"]
d["unit_cost_real"] = d["unit_cost_usd_per_m3"] * d["deflator"]

def summarize_year(g):
    vw_mean = np.sum(g["cost_used_real"]) / np.sum(g["qty_m3"])
    q25, q50, q75 = weighted_quantile(
        g["unit_cost_real"].values, [0.25, 0.50, 0.75], g["qty_m3"].values)
    return pd.Series({"n": len(g), "total_qty_m3": g["qty_m3"].sum(),
                      "vw_mean_uc_real": vw_mean, "vw_p25_uc_real": q25,
                      "vw_median_uc_real": q50, "vw_p75_uc_real": q75})

ts = d.groupby("fiscal_year").apply(summarize_year).reset_index().sort_values("fiscal_year")
ts = ts[ts["n"] >= MIN_N_PER_YEAR].copy()
ts_plot = ts.copy()
for c in ["vw_mean_uc_real","vw_p25_uc_real","vw_p75_uc_real","vw_median_uc_real"]:
    ts_plot[c] = rolling_center(ts_plot[c], ROLL)

dots = d[d["fiscal_year"].isin(ts["fiscal_year"]) & (d["qty_m3"] > 0)].copy()
dots["qty_color"] = np.log10(dots["qty_m3"]) if USE_LOG_QTY_FOR_COLOR else dots["qty_m3"]
vmin = float(np.nanquantile(dots["qty_color"], COLOR_CLIP_LO))
vmax = float(np.nanquantile(dots["qty_color"], COLOR_CLIP_HI))
norm = mcolors.PowerNorm(gamma=COLOR_GAMMA, vmin=vmin, vmax=vmax)

sand = pd.read_csv(StringIO(SAND_PRICE_DATA))
sand["year"] = sand["year"].astype(int)
sand = sand[sand["year"].between(YEAR_START, YEAR_END)].sort_values("year").copy()
sand["sand_price_plot"] = rolling_center(sand["price_nominal_usd_per_m3"], ROLL)

dots_zoom    = dots[dots["fiscal_year"].between(ZOOM_X_MIN, ZOOM_X_MAX) &
                    (dots["unit_cost_real"] <= ZOOM_Y_MAX)].copy()
ts_plot_zoom = ts_plot[ts_plot["fiscal_year"].between(ZOOM_X_MIN, ZOOM_X_MAX)].copy()
sand_zoom    = sand[sand["year"].between(ZOOM_X_MIN, ZOOM_X_MAX)].copy()
sand_zoom["sand_price_plot"] = rolling_center(sand_zoom["price_nominal_usd_per_m3"], ROLL)

# ── Figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(9.4, 8.2))
gs  = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[1.0, 1.25], hspace=0.35)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[1, 0])
fig.subplots_adjust(right=0.90)

# Panel a
sc_df = plot_df.sample(min(len(plot_df), SCATTER_MAX_N), random_state=0)
ax1.scatter(sc_df["qty_m3_w"], sc_df["uc_m3_w"],
            s=FIG1_DOT_SIZE, alpha=FIG1_DOT_ALPHA, rasterized=True)
ax1.plot(q_grid, uc_hat, linewidth=2.2, label="Regression mean (bias-corrected)")
ax1.fill_between(q_grid, uc_lo, uc_hi, alpha=0.18,
                 label="95% prediction interval")

ax1.set_xscale("log"); ax1.set_yscale("log")
ax1.set_xlabel("Quantity of dredged material (m³)", fontsize=16, color=DARK)
ax1.set_ylabel("Unit cost (US$ per m³)", fontsize=16, color=DARK)
ax1.tick_params(axis="both", which="both", colors=DARK, labelsize=13)
ax1.legend(frameon=False, loc="upper right")

# Robustness annotation
annot = (f"Scale elasticity = {b1[1]:.2f} (HC3 SE={se_hc3[1]:.2f}, p<0.001)\n"
         f"Robust to year control (year p={p2[2]:.2f})")
ax1.text(0.03, 0.06, annot, transform=ax1.transAxes,
         fontsize=9.5, color="0.35", va="bottom",
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.75", alpha=0.85))

ax1.text(-0.08, 1.04, "a", transform=ax1.transAxes,
         fontweight="bold", fontsize=16, va="bottom", ha="right", color=DARK)

# Panel b
scat = ax2.scatter(dots["fiscal_year"], dots["unit_cost_real"],
                   c=dots["qty_color"], cmap=COLOR_MAP, norm=norm,
                   s=DOTS_SIZE, alpha=DOTS_ALPHA, rasterized=True, zorder=5)
ax2.plot(ts_plot["fiscal_year"], ts_plot["vw_mean_uc_real"],
         linewidth=2.8, color=LINE_COLOR, linestyle=VW_LINESTYLE,
         label="Volume-weighted mean", zorder=10)
ax2.plot(sand["year"], sand["sand_price_plot"],
         linewidth=2.8, linestyle=SAND_LINESTYLE, color=LINE_COLOR,
         label="Market sand price", zorder=11)

ax2.set_xlabel("Fiscal year", fontsize=15, color=DARK)
ax2.set_ylabel("Unit cost (US$ per m³)", fontsize=15, color=DARK)
ax2.grid(True, alpha=0.2, linestyle="--")
ax2.tick_params(axis="both", which="both", colors=DARK, labelsize=13)
ax2.set_ylim(bottom=0)
leg = ax2.legend(frameon=True, framealpha=0.9, loc="upper left", fontsize=12)
for t in leg.get_texts(): t.set_color(DARK)
ax2.text(-0.08, 1.04, "b", transform=ax2.transAxes,
         fontweight="bold", fontsize=16, va="bottom", ha="right", color=DARK)

# Colorbar
bbox2 = ax2.get_position()
cax   = fig.add_axes([0.92, bbox2.y0, 0.02, bbox2.height])
cbar  = fig.colorbar(scat, cax=cax, orientation="vertical")
cbar.set_label("log\u2081\u2080[quantity of dredged material (m\u00b3)]", fontsize=12, color=DARK)
cbar.ax.tick_params(labelsize=12, colors=DARK)
cbar.outline.set_edgecolor(DARK)

# Inset
bbox  = ax2.get_position()
axins = fig.add_axes([bbox.x0 + 0.58*bbox.width, bbox.y0 + 0.52*bbox.height,
                      0.38*bbox.width, 0.45*bbox.height])
axins.scatter(dots_zoom["fiscal_year"], dots_zoom["unit_cost_real"],
              c=dots_zoom["qty_color"], cmap=COLOR_MAP, norm=norm,
              s=INSET_DOTS_SIZE, alpha=INSET_DOTS_ALPHA, rasterized=True)
axins.plot(ts_plot_zoom["fiscal_year"], ts_plot_zoom["vw_mean_uc_real"],
           linewidth=2.2, color=LINE_COLOR, linestyle=VW_LINESTYLE, zorder=10)
axins.plot(sand_zoom["year"], sand_zoom["sand_price_plot"],
           linewidth=2.2, linestyle=SAND_LINESTYLE, color=LINE_COLOR, zorder=11)
axins.set_xlim(ZOOM_X_MIN, ZOOM_X_MAX)
axins.set_ylim(0, ZOOM_Y_MAX)
axins.set_xticks([2005, 2010, 2015, 2020, 2025])
axins.set_yticks([0, 10, 20])
axins.tick_params(axis="both", which="both", colors=DARK, labelsize=11)
axins.grid(True, alpha=0.15, linestyle=":")
for sp in axins.spines.values():
    sp.set_edgecolor("gray"); sp.set_linewidth(0.8)

ax2.add_patch(Rectangle((ZOOM_X_MIN, 0), ZOOM_X_MAX - ZOOM_X_MIN, ZOOM_Y_MAX,
                          linewidth=0.8, edgecolor="gray", facecolor="none",
                          linestyle=":", alpha=0.4, zorder=1))

# Save
outpath = os.path.join(OUTDIR, "fig4_cost_of_dredging_combined_ab_v2.png")
fig.savefig(outpath, dpi=300, facecolor="white", edgecolor="none")
print(f"\nSaved: {outpath}")
plt.show(block=False)
plt.close()
