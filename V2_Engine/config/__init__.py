import os

# --- DYNAMIC PATH CONFIGURATION ---
# V2_Engine/config/__init__.py -> parent is config -> parent is V2_Engine -> parent is project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Archive reference (read-only)
V1_LEGACY_DIR = os.path.join(BASE_DIR, "V1_Legacy")

# V1 data paths (for reading old sample data during migration)
V1_DATA_SAMPLE = os.path.join(V1_LEGACY_DIR, "data_sample")
V1_RAW_INPUTS = os.path.join(V1_LEGACY_DIR, "01_raw_inputs")
V1_DATA_ENGINE = os.path.join(V1_LEGACY_DIR, "02_data_engine")
V1_LABELED_DATASET = os.path.join(V1_LEGACY_DIR, "03_labeled_dataset")

# --- V2 ENGINE PATHS ---
V2_ENGINE_DIR = os.path.join(BASE_DIR, "V2_Engine")
V2_PROCESSORS_DIR = os.path.join(V2_ENGINE_DIR, "processors")
V2_CONNECTORS_DIR = os.path.join(V2_ENGINE_DIR, "connectors")
V2_DATABASE_DIR = os.path.join(V2_ENGINE_DIR, "database")
V2_UTILS_DIR = os.path.join(V2_ENGINE_DIR, "utils")

# --- SOURCE DIRECTORIES ---
V2_SOURCE_0_DIR = os.path.join(V2_PROCESSORS_DIR, "source_0_market_data")
V2_SOURCE_4_DIR = os.path.join(V2_PROCESSORS_DIR, "source_4_reddit")

# --- OUTPUT ---
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORT_FILE = os.path.join(OUTPUT_DIR, "master_strategy_map.md")

# --- SETTINGS ---
FOCUS_ASIN = "B0F2HVR99F"
TITAN_MAX_COMPETITORS = 50000
VOLUME_GROUPS = {
    'C': {'min': 8001, 'max': 999999999, 'label': 'Group C (Whales > 8k)'},
    'B': {'min': 5001, 'max': 8000,      'label': 'Group B (Growth 5k-8k)'},
    'A': {'min': 2000, 'max': 5000,      'label': 'Group A (Easy Wins 2k-5k)'}
}
