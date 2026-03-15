# Result Directory

This folder stores generated outputs from the optimization notebook.

When you run the visualization cell with `save_dir="result"`, all charts
are automatically saved here as numbered `.png` files:

| File | Chart |
|------|-------|
| `01_kpi_dashboard.png` | KPI gauge dashboard |
| `02_energy_mix.png` | Energy supply donut |
| `03_battery_sources.png` | Battery charging sources |
| `04_monthly_balance.png` | Monthly energy balance |
| `05_heatmap.png` | Hourly surplus/deficit heatmap |
| `06_cost_comparison.png` | Annual cost comparison |
| `07_capex_waterfall.png` | CAPEX waterfall |
| `08_dispatch.png` | Hourly dispatch stacked area |
| `09_soc.png` | Battery state of charge |
| `10_energy_sankey.png` | Energy flow Sankey |

> **Note:** Generated files (`.png`, `.csv`) are excluded from git via `.gitignore`.
> Only this `README.md` is tracked.
