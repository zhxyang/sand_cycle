# Data Files Inventory

## Included in Repository

### Source Data (CSV files)
- `source_data_fig3_time_series_nominal.csv` (3.5 KB)
  - Time series data for Fig 2
  - Columns: year, cumulative_capacity_km3, annual_extraction_Gt

- `source_data_cost_scale_curves.csv` (1.6 KB)
  - USACE contract data processed for Fig 4
  - Columns: contract_id, fiscal_year, quantity_m3, unit_cost_USD_m3, ...

- `source_data_fig1_cost_scale_curves.csv` (1.3 KB)
  - Alternative/legacy cost data

- `global_reservoir_sediment_database_Yi.csv` (65 KB)
  - Literature compilation: 508 reservoirs, 72 studies
  - Extracted parameters: sand_fraction, annual_sed_rate, capacity_loss_pct
  - Used for: parameterization and cross-validation

- `world.csv` (560 KB)
  - World boundaries/country codes for mapping

## Large Files (Managed Separately)

### GREI Sand Trapping Dataset
- **File**: `GREI_sand_trapping_v1.csv`
- **Size**: 136 MB (555,960 rows)
- **Source**: GREI dataset (Liu et al. 2026) + sand fraction assignments
- **Key columns**:
  - `reservoir_id`: Unique identifier
  - `lat`, `lon`: Geographic coordinates
  - `capacity_MCM`: Storage capacity (million cubic meters)
  - `annual_sed_km3_yr`: Annual sedimentation volume (km³/yr)
  - `sand_fraction_pct`: Assigned sand fraction (%)
  - `sand_trapping_Mt_yr`: Annual sand trapping (Mt/yr)
  - `region`: AR6 region code
  - `distance_to_demand_km`: Distance to nearest demand pixel
  - `distance_to_builtup_km`: Distance to nearest built-up area

- **Storage**: Recommend Git LFS or separate data archive
- **Download**: [To be provided upon publication]

## External Data (Not Included - Must Be Obtained)

### Global Dam Watch (GDW)
- **Source**: Lehner et al. (2024) Scientific Data
- **DOI**: 10.6084/m9.figshare.24808665
- **Files needed**: GDW_reservoirs_v1_0.csv (35,295 reservoirs)
- **Use**: Cross-validation of trapping estimates
- **License**: CC-BY 4.0

### GREI Dataset (Raw)
- **Source**: Liu et al. (2026) Nature Sustainability
- **DOI**: 10.1038/s41893-026-01859-y
- **Files needed**: GREI sedimentation estimates (555,960 reservoirs)
- **Use**: Primary sedimentation volume source
- **Note**: Annual sedimentation volumes with uncertainty (CV)

### GHSL Built-up Surface
- **Source**: European Commission Joint Research Centre
- **URL**: https://ghsl.jrc.ec.europa.eu/
- **Dataset**: GHS-BUILT-S (Global Human Settlement Layer)
- **Version**: GHS-BUILT-S R2023A
- **Resolution**: 1 km grid
- **Files**: GHS_BUILT_S_GLOBE_R2023A_*.tif
- **Use**: Built-up area proximity analysis (Fig S2, S5)
- **License**: CC-BY 4.0

### Construction Demand Raster
- **Source**: IMAGINE-Concrete model (Wu et al.)
- **File**: `sand-demand-2023-2025-BAU-50km.tif`
- **Resolution**: 50 km grid
- **Units**: Mt yr⁻¹ (sand demand for concrete)
- **Time period**: 2023-2025 average
- **Use**: Spatial coupling analysis (Fig 3a, S5)
- **Contact**: [Author contact for data sharing]

### GRanD v1.3 (Legacy)
- **Source**: Global Reservoirs and Dams Database
- **URL**: http://globaldamwatch.org/grand/
- **Files**: GRanD_reservoirs_v1_3.shp
- **Use**: Historical comparison only (now superseded by GDW)
- **License**: Free for non-commercial use

### USACE Dredging Information System
- **Source**: US Army Corps of Engineers
- **URL**: https://ndc.ops.usace.army.mil/dis/reports
- **Files**: Contract records (multiple CSV files by fiscal year)
- **Location**: `data/cost/contract/*.csv`
- **Use**: Dredging cost analysis (Fig 4)
- **Time range**: 1997-2023
- **License**: US Government public domain

## Data Processing Notes

1. **GREI enrichment**: Raw GREI sedimentation volumes were combined with:
   - Literature-derived sand fractions (hierarchical assignment)
   - Sediment bulk density (1.5 t/m³)
   - Distance calculations (GHSL, demand raster)

2. **Distance calculations**:
   - GHSL: Euclidean distance to nearest cell with built-up fraction ≥1%
   - Demand: Equirectangular distance to nearest non-zero demand pixel
   - Aggregation: 10 km aggregation for GHSL (1 km → 10 km grid)

3. **Regional aggregation**: AR6 regions assigned based on lat/lon

4. **Sand fraction assignment** (hierarchical):
   - Reservoir-specific (if available in literature)
   - Country median
   - Regional median
   - Global median (20.1%)
