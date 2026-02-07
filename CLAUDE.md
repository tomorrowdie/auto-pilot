# Omni Traffic System (Auto Pilot)

## Project Overview
- **Lead Developer:** John
- **Goal:** Build an "Auto Pilot" SaaS for Amazon Sellers (similar to Helium 10 tools).
- **Architecture Strategy:** Transitioning from Monolith (mixed files) to Micro-Services (V2_Engine).

## Architecture Vision
- **V1_Legacy/** - Archived working code (Streamlit + Scripts). Treat as READ-ONLY reference.
- **V2_Engine/** - New production modular code.
    - **Source 0:** Market Data (H10 Xray Catalog) -- ported, operational
    - **Source 1:** Traffic (Cerebro)
    - **Source 2:** Reviews (Happy/Defect)
    - **Source 3:** Rufus (Adversarial Defense)
    - **Source 4:** Reddit Snipper (Social Listening) -- planned
    - **Source 5:** Webmaster (Sitemap Scanner) -- operational
    - **Source 6:** SEO Writer (Topic Clusters)

## Directory Structure
```
008-Auto-Pilot/
|-- CLAUDE.md              # This file (Project Handbook)
|-- Report_to_Gemini.md    # System Audit Report
|-- gemini_suggest.md      # Gemini Suggestions
|-- V1_Legacy/             # READ-ONLY archive of all old code & data
|-- V2_Engine/             # New modular engine (active development)
|-- backend/               # FastAPI SaaS backend (Shopify integration)
|-- frontend/              # React TypeScript frontend
|-- requirements.txt       # Python dependencies
|-- docker-compose.yml     # Container orchestration
```

## Coding Rules
- **Language:** Python 3.11+
- **Encoding:** UTF-8
- **Constraint:** Do NOT modify V1_Legacy files. All new work goes in V2_Engine.
- **Reporting:** Always save large outputs to `.md` files, do not print full text to console.
- **Environment:** Windows 11, PyCharm.
- **Paths:** Use `os.path` or `pathlib` with dynamic BASE_DIR. No hardcoded absolute paths.

## Workspace Path
`C:\Users\john\PycharmProjects\PythonProject\008-Auto-Pilot`
