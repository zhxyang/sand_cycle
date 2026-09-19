"""
Example: Generate Figure 3a using setup_paths
Demonstrates how to use the path configuration module
"""

# Import path configuration
import sys
from pathlib import Path

# Add repository root to Python path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from setup_paths import PATHS, get_output_path

# Now use PATHS throughout the script instead of hardcoded paths
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

# Load data using configured paths
print("Loading GREI data...")
df_grei = pd.read_csv(PATHS['grei_csv'])

print(f"Loaded {len(df_grei):,} reservoirs")
print(f"Total annual sand trapping: {df_grei['sand_trapping_Mt_yr'].sum()/1000:.1f} Gt/yr")

# Your figure generation code here...

# Save output using convenience function
output_file = get_output_path('fig3a_example.png', subdir='main_figures')
# plt.savefig(output_file, dpi=600, bbox_inches='tight')
print(f"Figure saved to: {output_file}")
