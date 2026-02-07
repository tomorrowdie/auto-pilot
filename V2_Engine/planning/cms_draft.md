# 🚀 Autopilot GEO Program - Architecture & CMS Strategy Note
**Date:** 2026-02-07
**Status:** Decided & Planned

## 1. Core CMS Decision: Directus
We have selected **Directus** as our centralized Headless CMS for the production phase.
* **Role:** Acts as the "SaaS Backend" & "Data Dashboard" for users.
* **Benefit:** Provides instant API-ready database, built-in user authentication/permissions, and a modern UI without custom frontend coding.
* **Integration:** Will serve as the bridge between the n8n Engine and the user interface.

## 2. Development Roadmap

### Phase 1: Engine Validation (Current)
* **Frontend:** **Streamlit** (Python).
* **Goal:** Rapidly test the n8n/Python logic (Sitemap parsing, Cluster analysis).
* **Focus:** Functionality over looks. Validate that the "Engine" correctly identifies gaps in Shopify/WordPress sitemaps.

### Phase 2: Production & UI/UX Enhancement (March Target)
* **Backend:** Migrate validated logic to feed into **Directus**.
* **UI/UX Layer:** Transition from Streamlit to a polished interface.
    * *Potential Tools:* UIUXPROMAX, Google Stitch, or Pencil (for prototyping/low-code frontend).
* **Workflow:**
    1.  User inputs domain in UI.
    2.  **Webhook** triggers n8n Engine.
    3.  Engine processes data & pushes JSON results to **Directus**.
    4.  User views "Content Gaps" & "Business Cases" inside the Directus Dashboard.

## 3. Why this Stack?
* **Speed:** Streamlit allows us to verify the "Autopilot" logic immediately without waiting for UI design.
* **Scalability:** Directus handles the heavy lifting of user management and data display, giving the program a professional SaaS feel with minimal dev time.