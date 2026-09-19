# Figure Repository Quick Start Guide

## Initial Setup

1. **Clone or download this repository**
   ```bash
   cd /path/to/your/research/
   ```

2. **Update base path in setup_paths.py**
   ```python
   # Edit line 16 in setup_paths.py:
   BASE_DIR = Path(r"YOUR_LOCAL_PATH")
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   # Or with conda:
   conda create -n sand_paper python=3.10
   conda activate sand_paper
   pip install -r requirements.txt
   ```

4. **Validate paths**
   ```bash
   python setup_paths.py
   ```

## Obtaining External Data

### Required Large Files

1. **GREI sand trapping dataset** (already included)
   - File: `data/GREI_sand_trapping_v1.csv` (136 MB)
   - Status: ✓ Included in repository

2. **GDW database**
   - Download: https://doi.org/10.6084/m9.figshare.24808665
   - Place in: `../data/GDW/GDW_reservoirs_v1_0.csv`

3. **GHSL built-up surface**
   - Download: https://ghsl.jrc.ec.europa.eu/download.php
   - Dataset: GHS-BUILT-S R2023A
   - Place in: `../data/GHSL/`

4. **Construction demand raster**
   - Contact: [Author for data sharing]
   - File: `sand-demand-2023-2025-BAU-50km.tif`
   - Place in: `../data/`

5. **USACE dredging contracts**
   - Download: https://ndc.ops.usace.army.mil/dis/reports
   - Place in: `../data/cost/contract/`

## Generating Figures

### Main Text Figures

```bash
cd scripts/main_figures/

# Figure 2: Capacity and extraction trends
python fig2_capacity_extraction_trends.py

# Figure 3a: Global map with demand overlay
python fig3a_map_v2.py

# Figure 3c: Regional comparison
python fig3c_scatter_v5.py

# Figure 4: Dredging costs
python fig4_dredge_cost_v3.py
```

### Supplementary Figures

```bash
cd scripts/SI_figures/

# Figure S1: Framework diagram
python figS1_framework_v3.py

# Figure S2: GHSL overlay
python figS2_GHSL_overlay_v2.py

# Figure S3: Lorenz curves
python figS3_lorenz_concentration.py

# Figure S4: Top 10% map
python figS4_map_top10pct_v3.py

# Figure S5: Distance CDF
python figS5_cdf_distance_v2.py

# Figure S6: Sensitivity analysis
python figS6_demand_sensitivity_v1.py
```

## Outputs

All generated figures will be saved to `outputs/` directory with timestamped filenames.

Default formats:
- PNG (600 dpi for publication)
- PDF (vector format where applicable)

## Troubleshooting

### Common Issues

**1. Path errors**
```python
FileNotFoundError: [Errno 2] No such file or directory: '...'
```
→ Update `BASE_DIR` in `setup_paths.py`

**2. Missing external data**
```python
FileNotFoundError: GREI_sand_trapping_v1.csv not found
```
→ Download required external data (see above)

**3. Memory errors with large CSV**
```python
MemoryError: Unable to allocate array
```
→ Use chunked reading:
```python
df = pd.read_csv(path, chunksize=50000)
```

**4. Coordinate transformation issues**
```python
ValueError: Cannot transform naive geometries
```
→ Check CRS definitions in GeoDataFrames

### Getting Help

- Check MANIFEST.txt for detailed figure specifications
- See DATA_INVENTORY.md for data file descriptions
- Contact authors for data access questions

## Repository Structure

```
figure_repository/
├── README.md                  # Main documentation
├── QUICKSTART.md             # This file
├── MANIFEST.txt              # Detailed figure specifications
├── requirements.txt          # Python dependencies
├── setup_paths.py            # Path configuration
│
├── data/                     # Source data
│   ├── DATA_INVENTORY.md     # Data file descriptions
│   ├── GREI_sand_trapping_v1.csv (136 MB)
│   ├── global_reservoir_sediment_database_Yi.csv
│   ├── source_data_*.csv
│   └── ...
│
├── scripts/                  # Figure generation scripts
│   ├── main_figures/         # Fig 1-4
│   └── SI_figures/           # Fig S1-S6
│
└── outputs/                  # Generated figures (not tracked)
```

## Reproducibility Checklist

Before submitting manuscript:

- [ ] All external data downloaded and placed correctly
- [ ] Paths updated in setup_paths.py
- [ ] All figure scripts run without errors
- [ ] Output figures match manuscript versions
- [ ] Key numbers verified against manuscript text
- [ ] Data citations added to manuscript
- [ ] Repository archived (Zenodo/Figshare)

## Key Numbers Verification

Run this after generating all figures to verify against manuscript:

```python
import pandas as pd
from setup_paths import PATHS

# Load GREI data
df = pd.read_csv(PATHS['grei_csv'])

# Global totals
total_reservoirs = len(df)  # Should be 555,960
total_trapping = df['sand_trapping_Mt_yr'].sum() / 1000  # Should be ~11.6 Gt/yr

print(f"Total reservoirs: {total_reservoirs:,}")
print(f"Annual trapping: {total_trapping:.1f} Gt/yr")

# Top 1% and 10%
df_sorted = df.sort_values('capacity_MCM', ascending=False)
top1_pct = df_sorted.iloc[:int(0.01*len(df))]['sand_trapping_Mt_yr'].sum() / df['sand_trapping_Mt_yr'].sum()
top10_pct = df_sorted.iloc[:int(0.10*len(df))]['sand_trapping_Mt_yr'].sum() / df['sand_trapping_Mt_yr'].sum()

print(f"Top 1% contribution: {top1_pct*100:.0f}%")  # Should be ~89%
print(f"Top 10% contribution: {top10_pct*100:.0f}%")  # Should be ~98%

# Distance statistics
print(f"Median distance to demand: {df['distance_to_demand_km'].median():.0f} km")  # Should be ~22 km
```

## License

[To be determined - typically CC-BY 4.0 for data, MIT for code]

## Updates

Last updated: 2026-09-19
Version: 1.0 (manuscript submission)
