# Repository
This repository contains all source data, analysis scripts, and figure generation code.

## Repository Structure

```
figure_repository/
├── data/                   # Source data files
│   ├── GREI_sand_trapping_v1.csv
│   ├── source_data_fig3_time_series_nominal.csv
│   ├── source_data_cost_scale_curves.csv
│   └── ...
├── scripts/                # Figure generation scripts
│   ├── main_figures/       # Main text figures (Fig 1-4)
│   └── SI_figures/         # Supplementary figures (Fig S1-S6)
├── outputs/                # Generated figures (not tracked)
└── README.md              # This file
```

## Main Text Figures

### Figure 1: The journey of sand from uplands to coasts and cities
- **Type**: Conceptual diagram
- **Script**: `scripts/main_figures/fig1_sand_journey_conceptual.py` (or created externally)
- **Data**: None (conceptual)

### Figure 2: Global reservoir storage capacity and sand-and-gravel extraction
- **Script**: `scripts/main_figures/fig2_capacity_extraction_trends.py`
- **Data**:
  - `data/source_data_fig3_time_series_nominal.csv` (time series data)
  - Cumulative capacity trends from literature compilation

### Figure 3: Global reservoir sand trapping and construction-sand demand
- **Panel a (Map)**: `scripts/main_figures/fig3a_map_v2.py`
- **Panel b**: Part of combined figure
- **Panel c (Regional comparison)**: `scripts/main_figures/fig3c_scatter_v5.py`
- **Data**:
  - `data/GREI_sand_trapping_v1.csv` (555,960 reservoirs)
  - `data/sand-demand-2023-2025-BAU-50km.tif` (gridded demand raster)

### Figure 4: Dredging unit costs by dredging quantity and fiscal year
- **Script**: `scripts/main_figures/fig4_dredge_cost_vs_time_v3_20260620.py`
- **Data**:
  - `data/cost/contract/*.csv` (USACE DIS contract records)
  - `data/source_data_cost_scale_curves.csv`

## Supplementary Figures

### Figure S1: Flow diagram of systematic literature review and calculation framework
- **Script**: `scripts/SI_figures/figS1_framework_v3.py`
- **Data**: None (conceptual workflow diagram)

### Figure S2: Reservoir sand trapping overlaid on GHSL built-up areas
- **Script**: `scripts/SI_figures/figS2_GHSL_overlay_v2.py`
- **Data**:
  - `data/GREI_sand_trapping_v1.csv`
  - GHSL built-up surface product (external, from JRC)

### Figure S3: Lorenz concentration curves for annual reservoir sand trapping
- **Script**: `scripts/SI_figures/figS3_lorenz_concentration.py`
- **Data**: `data/GREI_sand_trapping_v1.csv`

### Figure S4: Spatial distribution of annual sand trapping for largest 10% reservoirs
- **Script**: `scripts/SI_figures/figS4_map_top10pct_v3.py`
- **Data**: `data/GREI_sand_trapping_v1.csv`

### Figure S5: Trapping-weighted proximity to built-up areas and construction demand
- **Script**: `scripts/SI_figures/figS5_cdf_distance_v2.py`
- **Data**:
  - `data/GREI_sand_trapping_v1.csv`
  - Distance calculations (pre-computed in analysis)

### Figure S6: Sensitivity of global annual reservoir sand trapping estimates
- **Script**: `scripts/SI_figures/figS6_demand_sensitivity_v1.py`
- **Data**:
  - Sensitivity analysis results
  - Sand fraction and sedimentation rate distributions

## Key Datasets

### Primary Data Sources

1. **GREI_sand_trapping_v1.csv** (555,960 reservoirs)
   - Columns: reservoir_id, lat, lon, capacity_MCM, annual_sed_km3_yr, sand_trapping_Mt_yr, ...
   - Source: GREI dataset (Liu et al. 2026) + sand fraction from literature

2. **GDW database** (35,295 large reservoirs)
   - Used for cross-validation
   - Source: Lehner et al. (2024)

3. **Construction demand raster** (50km grid, 2023-2025)
   - File: `sand-demand-2023-2025-BAU-50km.tif`
   - Source: IMAGINE-Concrete model (Wu et al.)

4. **Literature compilation** (508 reservoirs, 72 studies)
   - Sand fraction: median 20.1% (P10: 8.8%, P90: 43.0%)
   - Sedimentation rates and capacity loss
   - File: `global_reservoir_sediment_database_Yi.csv`

5. **USACE Dredging Information System**
   - Contract records: `data/cost/contract/*.csv`
   - Fiscal years, quantities, costs

## Software Requirements

```python
numpy >= 1.24
pandas >= 2.0
geopandas >= 0.13
matplotlib >= 3.7
scipy >= 1.10
rasterio >= 1.3
tifffile >= 2023.7
```

## Reproducibility Notes

- All scripts use absolute paths that need to be updated to local machine
- GHSL data requires separate download from JRC
- GDW data available from Global Dam Watch database
- GREI data available from Liu et al. (2026) publication

## Key Numbers (for verification)

- Total reservoirs (GREI): 555,960
- Annual sand trapping: ~11.6 Gt yr⁻¹ (central), 5-25 Gt yr⁻¹ (sensitivity)
- Global concrete-sand demand: ~10.5 Gt yr⁻¹ (central), 8.4-12.6 Gt yr⁻¹ (range)
- Trapping-weighted median distance to demand: 22 km
- 75% of trapped sand within: 32 km of demand
- Top 1% by capacity contribute: ~89% of trapping
- Top 10% by capacity contribute: ~98% of trapping
