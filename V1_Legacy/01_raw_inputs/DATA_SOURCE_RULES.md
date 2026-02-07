# Data Source 1: Helium 10 Cerebro (Traffic Data)

02_data_engine/
├── main.py                  # The "Manager" (Runs everything)
├── config.py                # The "Settings" (Paths & Constants)
├── utils.py                 # The "Tools" (Shared functions like loading CSVs)
└── processors/              # The "Workers"
    ├── __init__.py
    └── source_1_cerebro.py  # SPECIFIC logic for H10 Cerebro

## 1. Objective: The "Strategy Menu"
**Goal:** We do NOT want the code to blindly select keywords. 
**Task:** The code must process the raw data and output a **"Candidate Report"** containing the **Top 10 Scored Keywords** for each of the 6 Dimensions.
**Human Role:** The human will review this report and select the final 4-5 "Seeds" for content generation.

## 2. File Location & Structure
* **Path:** `C:\Users\john\PycharmProjects\PythonProject\008-Auto-Pilot\data_sample\data_source_1_keyword_data_h10_cerebro\US_AMAZON_cerebro_B0F2HVR99F_2025-12-23.csv


`
* **Key Columns:** `Keyword Phrase`, `Search Volume`, `Search Volume Trend`, `Keyword Sales`, `Competing Products`, `Title Density`.

## 3. The Sorting Logic (How to pick the Top 10)
*For each dimension, apply the "Smart Sort" to find the best 10 candidates.*

| Dimension | Filter Condition (The Gate) | Ranking Metric ( The Score) |
| :--- | :--- | :--- |
| **1. Precision** | Organic Rank < 40 OR Sales > 10 | **Sort by:** `Keyword Sales` (High to Low) |
| **2. Hierarchy** | Search Volume > 2,000 | **Sort by:** `Search Volume` (High to Low) |
| **3. Contextual** | **Titan Protocol:** Competitor Brand Names OR High Relevance | **Sort by:** `Title Density` (Low to High) - *Finds gaps.* |
| **4. Occasion** | Trend > 10% (Green Trend) | **Sort by:** `Search Volume Trend` % (High to Low) |
| **5. Discovery** | Cerebro IQ Score > 1,000 | **Sort by:** `Cerebro IQ Score` (High to Low) |
| **6. Expansion** | Word Count > 3 (Long Tail) | **Sort by:** `Competing Products` (Low to High) |

## 4. The "Titan Protocol" (Competitor Handling)
*How to handle Big Brands (Nike, Lego) in the Menu.*
* **Do not delete** big competitors.
* **Tag them** as `Dimension 3: Contextual (Competitor)`.
* **Report:** Include them in the "Contextual" list so the human can decide: *"Do we want to attack Nike today?"*

## 5. Output Requirement
The Python script must generate a file named **`strategy_candidates.md`** with this exact format:

### 1. Precision Candidates (Top 10)
* [ ] **nightgown for women** (Vol: 50k, Sales: 200)
* [ ] **cotton sleep shirt** (Vol: 12k, Sales: 85)
...

### 3. Contextual/Competitor Candidates (Top 10)
* [ ] **vs pajamas** (Competitor: Victoria's Secret) - *Opportunity Score: High*
* [ ] **nursing friendly** (Scenario)
...