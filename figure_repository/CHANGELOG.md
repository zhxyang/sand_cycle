# Changelog

## Version 1.0 (2026-09-19) - Initial Release

### Repository Structure
- Created organized directory structure for manuscript figures
- Separated main text figures (Fig 1-4) from SI figures (Fig S1-S6)
- Established data inventory with external data requirements

### Scripts Included

**Main Text Figures:**
- `fig2_capacity_extraction_trends.py` - Reservoir capacity and extraction over time
- `fig3a_map_v2.py` - Global map of reservoir sand trapping with demand overlay
- `fig3c_scatter_v5.py` - Regional comparison scatter plot
- `fig4_dredge_cost_v3.py` - Dredging cost analysis with scale economies

**SI Figures:**
- `figS1_framework_v3.py` - Calculation framework diagram
- `figS2_GHSL_overlay_v2.py` - GHSL built-up area overlay
- `figS3_lorenz_concentration.py` - Lorenz concentration curves
- `figS4_map_top10pct_v3.py` - Top 10% reservoirs spatial distribution
- `figS5_cdf_distance_v2.py` - Proximity CDF curves
- `figS6_demand_sensitivity_v1.py` - Sensitivity analysis heatmap

### Data Files

**Included:**
- GREI_sand_trapping_v1.csv (136 MB, 555,960 reservoirs)
- global_reservoir_sediment_database_Yi.csv (64 KB, literature compilation)
- source_data_fig3_time_series_nominal.csv (time series)
- source_data_cost_scale_curves.csv (USACE contract data)

**External (documented):**
- GDW database (35,295 reservoirs)
- GHSL built-up surface (JRC)
- Construction demand raster (IMAGINE-Concrete)
- GRanD v1.3 (legacy)

### Key Numbers Verified
- Total reservoirs: 555,960 ✓
- Annual sand trapping: ~11.6 Gt yr⁻¹ ✓
- Construction demand: ~10.5 Gt yr⁻¹ ✓
- Median distance to demand: 22 km ✓
- 75% within: 32 km ✓
- Top 1% contribute: ~89% ✓
- Top 10% contribute: ~98% ✓

### Infrastructure
- setup_paths.py: Centralized path management
- requirements.txt: Python dependencies
- .gitignore: Exclude large files and outputs
- Documentation: README, QUICKSTART, MANIFEST, DATA_INVENTORY

### Notes
- All scripts tested on Windows 11
- Paths currently hardcoded, need update for distribution
- GREI large file included (consider Git LFS for version control)
- External data access documented with DOIs/URLs

---

## Future Updates

### Planned for v1.1 (Pre-publication)
- [ ] Convert all scripts to use setup_paths.py
- [ ] Add example notebooks for key analyses
- [ ] Create conda environment.yml
- [ ] Add unit tests for data validation
- [ ] Document Git LFS setup for large files
- [ ] Add license information

### Planned for v2.0 (Post-publication)
- [ ] Archive on Zenodo with DOI
- [ ] Add interactive visualization scripts
- [ ] Create Docker container for full reproducibility
- [ ] Add parallel processing for large analyses
- [ ] Extend to updated GREI/GDW versions

---

Last updated: 2026-09-19
