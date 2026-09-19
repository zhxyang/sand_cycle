#!/usr/bin/env python3
"""
setup_paths.py
--------------
Configuration module for figure generation scripts.
Update BASE_DIR to match your local installation, then import this
module from all figure scripts to ensure consistent paths.

Usage in figure scripts:
    from setup_paths import PATHS
    grei_csv = PATHS['grei_csv']
"""

from pathlib import Path
import os

# ==============================================================================
# MODIFY THIS PATH TO MATCH YOUR LOCAL INSTALLATION
# ==============================================================================
BASE_DIR = Path(r"C:\path\to\sand_cycle")
# Alternative for Unix-like systems:
# BASE_DIR = Path.home() / "research" / "sand_dams_paper"

# Or use environment variable:
# BASE_DIR = Path(os.getenv('SAND_PAPER_DIR', '/default/path'))

# ==============================================================================
# DERIVED PATHS (do not modify unless repository structure changes)
# ==============================================================================
PATHS = {
    # Base directories
    'base': BASE_DIR,
    'data_dir': BASE_DIR / 'figure_repository' / 'data',
    'scripts_dir': BASE_DIR / 'figure_repository' / 'scripts',
    'output_dir': BASE_DIR / 'figure_repository' / 'outputs',

    # Main data files
    'grei_csv': BASE_DIR / 'figure_repository' / 'data' / 'GREI_sand_trapping_v1.csv',
    'literature_db': BASE_DIR / 'figure_repository' / 'data' / 'global_reservoir_sediment_database_Yi.csv',
    'timeseries_csv': BASE_DIR / 'figure_repository' / 'data' / 'source_data_fig3_time_series_nominal.csv',
    'cost_csv': BASE_DIR / 'figure_repository' / 'data' / 'source_data_cost_scale_curves.csv',
    'world_csv': BASE_DIR / 'figure_repository' / 'data' / 'world.csv',

    # External data (must be downloaded separately)
    'gdw_csv': BASE_DIR / 'data' / 'GDW' / 'GDW_reservoirs_v1_0.csv',
    'demand_tif': BASE_DIR / 'data' / 'sand-demand-2023-2025-BAU-50km.tif',
    'ghsl_tif': BASE_DIR / 'data' / 'GHSL' / 'GHS_BUILT_S_*.tif',  # wildcard
    'grand_shp': BASE_DIR / 'data' / 'GRanD_Version_1_3' / 'GRanD_reservoirs_v1_3.shp',
    'usace_contracts': BASE_DIR / 'data' / 'cost' / 'contract',
}

# Create output directory if it doesn't exist
PATHS['output_dir'].mkdir(parents=True, exist_ok=True)

# ==============================================================================
# VALIDATION
# ==============================================================================
def validate_paths(required_files=None):
    """
    Check that required data files exist.

    Parameters
    ----------
    required_files : list of str, optional
        Keys from PATHS dict to check. If None, checks all main data files.
    """
    if required_files is None:
        required_files = ['grei_csv', 'literature_db', 'timeseries_csv',
                         'cost_csv', 'world_csv']

    missing = []
    for key in required_files:
        if key not in PATHS:
            print(f"Warning: Unknown path key '{key}'")
            continue

        path = PATHS[key]
        if '*' in str(path):  # wildcard path
            continue

        if not path.exists():
            missing.append(f"{key}: {path}")

    if missing:
        print("WARNING: Missing required data files:")
        for m in missing:
            print(f"  - {m}")
        print("\nPlease download external data files or update paths in setup_paths.py")
        return False
    else:
        print("All required data files found.")
        return True

# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================
def get_output_path(filename, subdir=None):
    """
    Generate output file path with optional subdirectory.

    Parameters
    ----------
    filename : str
        Output filename (e.g., 'fig3a_map.png')
    subdir : str, optional
        Subdirectory under outputs/ (e.g., 'main_figures', 'SI_figures')

    Returns
    -------
    Path
        Full output path
    """
    if subdir:
        outdir = PATHS['output_dir'] / subdir
        outdir.mkdir(parents=True, exist_ok=True)
        return outdir / filename
    else:
        return PATHS['output_dir'] / filename

# ==============================================================================
# RUN VALIDATION ON IMPORT (optional, comment out if not desired)
# ==============================================================================
if __name__ == '__main__':
    print("="*70)
    print("SAND PAPER FIGURE REPOSITORY - PATH SETUP")
    print("="*70)
    print(f"\nBase directory: {BASE_DIR}")
    print(f"Output directory: {PATHS['output_dir']}")
    print("\nValidating paths...")
    validate_paths()
    print("\nTo use in figure scripts:")
    print("    from setup_paths import PATHS")
    print("    grei_csv = PATHS['grei_csv']")
    print("="*70)
