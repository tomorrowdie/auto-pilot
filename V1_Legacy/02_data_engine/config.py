import os

# BASE PROJECT PATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- INPUT CONFIGURATION ---
# 1. Traffic (Cerebro)
DATA_SOURCE_1_PATH = r"C:\Users\john\PycharmProjects\PythonProject\008-Auto-Pilot\data_sample\data_source_1_keyword_data_h10_cerebro\US_AMAZON_cerebro_B0F2HVR99F_2025-12-23.csv"

# 2. Reviews (Customer Voice)
DATA_SOURCE_2_HAPPY_PATH = r"C:\Users\john\PycharmProjects\PythonProject\008-Auto-Pilot\data_sample\data_source_2_reviews\02_review_analysis\happy_flow_output.txt"
DATA_SOURCE_2_DEFECT_PATH = r"C:\Users\john\PycharmProjects\PythonProject\008-Auto-Pilot\data_sample\data_source_2_reviews\02_review_analysis\defects_flow_output.txt"

# 3. Rufus Vision (The "Looking for specific info" Tags)
# [ACTION] You will need to create this simple JSON file
DATA_SOURCE_3_VISION_PATH = os.path.join(BASE_DIR, "01_raw_inputs", "rufus_vision_tags.json")

# 4. Market Catalog (Future Source 4)
DATA_SOURCE_4_PATH = os.path.join(BASE_DIR, "01_raw_inputs", "market_scan_xray.csv")

# --- OUTPUT CONFIGURATION ---
OUTPUT_DIR = os.path.join(BASE_DIR, "03_labeled_dataset")
REPORT_FILE = os.path.join(OUTPUT_DIR, "master_strategy_map.md")

# --- SETTINGS ---
FOCUS_ASIN = "B0F2HVR99F"
TITAN_MAX_COMPETITORS = 50000
VOLUME_GROUPS = {
    'C': {'min': 8001, 'max': 999999999, 'label': 'Group C (Whales > 8k)'},
    'B': {'min': 5001, 'max': 8000,      'label': 'Group B (Growth 5k-8k)'},
    'A': {'min': 2000, 'max': 5000,      'label': 'Group A (Easy Wins 2k-5k)'}
}