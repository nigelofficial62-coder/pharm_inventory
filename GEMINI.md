# SENTINEL - Outpatient Pharmacy Automation System (OPAS)

## Project Overview
SENTINEL is an enterprise-grade Streamlit multi-page dashboard designed to monitor and manage outpatient pharmacy automation systems. It currently tracks and calculates loading requirements for **iPTL Shelves** and the **ROWA Machine**.

## Architecture & File Structure
- `SENTINEL.py`: The main entry point and landing page. Includes global CSS rules and welcome text.
- `pages/1_iPTL_Shelves.py`: Manages the intelligent Pick-to-Light (iPTL) shelf capacities, buffer top-ups, and main store reordering. Renders a CSS grid of physical shelves and bins based on `master_config.csv`.
- `pages/2_ROWA.py`: Manages the ROWA automated storage and dispensing system. Computes loading requirements against PAR targets (from `rowa_master_config.csv`) and visualizes stock/expiry status using Plotly.
- `.streamlit/config.toml`: Contains the global Streamlit theme (colors, fonts).

## Data Ingestion & State Management
- **SSRS Reports**: Users upload raw SSRS CSV reports via a discreet `st.popover` in the header of each page.
- **Auto-Close Pattern**: To natively close the popover upon upload, the component conditionally swaps into an `st.button` ("🔄 Upload New Data") once data is successfully loaded into `st.session_state`.
- **Master Configs**: `master_config.csv` (iPTL) and `rowa_master_config.csv` (ROWA) are used via `pd.merge(how='left')` to catch "ghost items" (items with 0 stock that disappear from the SSRS report entirely).

## Design System & UI Rules
- **Color Palette**:
  - Primary: Deep Teal (`#097C87`)
  - Backgrounds: Off-white/slate (`#f8fafc`) for depth, solid white (`#ffffff`) for metric cards/Plotly backgrounds.
  - Sidebar: Dark Slate (`#0F172A`) with bright text (`#F8FAFC`).
  - Thresholds: 
    - Critical (< 33%): Red (`#FCA47C`)
    - Warning (33% - 66%): Yellow (`#F9D779`)
    - Healthy (67% - 100%): Green (`#A1CCA6`)
    - Overstocked (> 100%): Sky Blue (`#60A5FA`)
- **Typography**: Clean, neutral sans-serif (prioritizing `Inter`).
- **Charts (Plotly)**: Use `overflow: hidden !important;` on the parent container and `paper_bgcolor='rgba(0,0,0,0)'` / `plot_bgcolor='rgba(0,0,0,0)'` on the chart to prevent protruding scrollbars and CSS double-boxing.

## Future Roadmap (Notes for Agent)
- Integrating a Supabase PostgreSQL backend for persistent ML data retention and historical trend tracking.
- Expanding the dashboard into a larger "Superbrain" handling other pharmacy automation modules.
