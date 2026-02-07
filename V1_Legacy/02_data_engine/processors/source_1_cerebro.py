import pandas as pd
import numpy as np
import re
import config  # Imports from your sibling config.py

def classify_dimension(row):
    """
    Assigns the '6 Dimensions' tag based on rules.
    This tells the AI 'How to write' (e.g. Scenario vs Gift).
    """
    text = str(row.get('Keyword Phrase', '')).lower()
    
    # 1. Titan Protocol (Competitors)
    if row.get('Competing Products', 0) > config.TITAN_MAX_COMPETITORS:
        return '3. Contextual (Competitor)'

    # 2. Regex Rules (Can be expanded with external CSV later)
    if re.search(r'\b(gift|christmas|valentine|birthday)\b', text): return '4. Occasion'
    if re.search(r'\b(nursing|travel|hospital|winter|summer)\b', text): return '3. Contextual'
    if re.search(r'\b(compatible|fits|suitable)\b', text): return '3. Contextual'
    if re.search(r'\b(nightgown|pajama|shirt|dress)\b', text): return '1. Precision'
    
    # 3. Metric Rules
    # If it has high IQ score but low sales, it's Discovery
    if row.get('Cerebro IQ Score', 0) > 1000: return '5. Discovery'
    
    # Default Fallback
    return '2. Hierarchy'

def assign_volume_group(vol):
    """Maps search volume to Battle Groups A, B, or C."""
    if vol >= config.VOLUME_GROUPS['C']['min']: return 'C'
    if vol >= config.VOLUME_GROUPS['B']['min']: return 'B'
    if vol >= config.VOLUME_GROUPS['A']['min']: return 'A'
    return 'Skip' # Too small (< 2000)

def process_cerebro_data(file_path):
    print(f"   [Source 1] Loading: {file_path}")
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"   [Error] File not found. Check path in config.py")
        return {}

    # 1. Normalize Columns (Clean "$", ",", "-")
    numeric_cols = ['Search Volume', 'Keyword Sales', 'Competing Products', 'Cerebro IQ Score', 'Search Volume Trend']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d-]', '', regex=True), errors='coerce').fillna(0)

    # 2. Apply Logic Tags
    df['Dimension_Label'] = df.apply(classify_dimension, axis=1)
    df['Vol_Group'] = df['Search Volume'].apply(assign_volume_group)

    # 3. Sort & Select per Group
    # User Request: "Discovery" sorted by Sales. 
    # Global Sort: We generally want High Sales within each Volume Group.
    df = df.sort_values(by='Keyword Sales', ascending=False)

    report_data = {}
    
    # Iterate through Groups C, B, A
    for group_key in ['C', 'B', 'A']:
        group_def = config.VOLUME_GROUPS[group_key]
        
        # Filter dataframe for this group
        subset = df[df['Vol_Group'] == group_key].head(10) # Top 10 Winners
        
        if not subset.empty:
            report_data[group_def['label']] = subset
            
    return report_data

def generate_report_section(report_data):
    lines = []
    lines.append("## 📊 Source 1: Helium 10 Traffic Menu")
    lines.append("> **Instructions:** Select your 'Battlefield'. Pick 3-5 keywords from a Group to start your content mission.\n")

    for group_name, df in report_data.items():
        lines.append(f"### 🏆 {group_name}")
        lines.append(f"| Select | Keyword | Vol | Sales | Strategy Tag |")
        lines.append(f"| :--- | :--- | :--- | :--- | :--- |")
        
        for _, row in df.iterrows():
            phrase = row.get('Keyword Phrase', 'N/A')
            vol = int(row.get('Search Volume', 0))
            sales = int(row.get('Keyword Sales', 0))
            dim = row.get('Dimension_Label', 'N/A')
            
            # Markdown Checkbox Row
            lines.append(f"| [ ] | **{phrase}** | {vol:,} | {sales} | `{dim}` |")
        
        lines.append("\n")
        
    return "\n".join(lines)