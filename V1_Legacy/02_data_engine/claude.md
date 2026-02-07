# Omni Traffic System (Auto Pilot)

## Project Overview
- **Lead Developer:** John
- **Goal:** Build an "Auto Pilot" SaaS for Amazon Sellers (similar to Helium 10 tools).
- **Architecture Strategy:** Transitioning from Monolith (mixed files) to Micro-Services (V2_Engine).

## Architecture Vision
- **V1_Legacy:** Current working code (Streamlit + Scripts). Treat as READ-ONLY reference.
- **V2_Engine:** New production modular code.
    - **Source 1:** Traffic (Cerebro)
    - **Source 2:** Reviews (Happy/Defect)
    - **Source 3:** Rufus (Adversarial Defense)
    - **Source 4:** Catalog (Market Data)
    - **Source 5:** Webmaster (GSC/Bing)
    - **Source 6:** SEO Writer (Topic Clusters)

## Coding Rules
- **Language:** Python 3.11+
- **Encoding:** UTF-8
- **Constraint:** Do NOT modify existing files without explicit permission.
- **Reporting:** Always save large outputs to `.md` files, do not print full text to console.
- **Environment:** Windows 11, PyCharm.

## Workspace Path
`C:\Users\john\PycharmProjects\PythonProject\008-Auto-Pilot`