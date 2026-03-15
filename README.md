# PV + Heat Pump System Optimization (MILP)

A techno-economic **Mixed Integer Linear Programming (MILP)** model for optimizing the sizing and operation of a residential or commercial hybrid building energy system.

The model determines optimal **investment decisions** (installed capacities) and **hourly dispatch** of electricity supply technologies to meet building demand at minimum total cost, achieving the lowest possible **Levelized Cost of Electricity (LCOE)**.

---

## System Components

| Component | Description |
|---|---|
| **Solar PV** | On-site renewable generation; capacity optimized by the model |
| **Battery Storage** | Short-term energy buffer; shifts PV generation to periods of demand |
| **Heat Pump** | Optional electrification of building heating (replaces gas/oil boiler) |
| **Grid Connection** | Backup electricity supply; optional (off-grid mode available) |

---

## Model Features

- **Capacity expansion optimization** — simultaneous sizing of PV, battery, and heat pump
- **Hourly dispatch modeling** — 8760-hour full-year resolution
- **Battery state-of-charge tracking** — cyclic SoC with round-trip efficiency losses
- **PV curtailment** — modeled explicitly when surplus exceeds demand and storage capacity
- **Dual scenario analysis** — with and without heat pump replacing conventional heating
- **Economic outputs** — LCOE, LCOS, annual savings, self-sufficiency, and simple payback period

---

## Optimization Formulation

**Objective:** Minimise total annualised system cost

$$\min \; \text{Grid cost} + \text{Battery cycling cost} + \text{PV annualised CAPEX} + \text{Battery annualised CAPEX}$$

**Key constraints:**

| Constraint | Description |
|---|---|
| Power balance | PV + Grid + Discharge = Demand + Charge + Curtailment |
| SoC dynamics | Cyclic state-of-charge with efficiency losses |
| SoC limits | 20 % minimum, 100 % maximum of energy capacity |
| C-rate limits | Charge/discharge power ≤ energy capacity / 3 |

The **Capital Recovery Factor (CRF)** annualises investment cost over the technology lifetime at the given discount rate.

---

## Repository Structure

```
PV-Heat-Pump-Optimization/
│
├── PV_Heat_Pump_Optimization.ipynb   # Main notebook — run this
│
├── src/                              # Model logic (imported by notebook)
│   ├── constants.py                  #   Techno-economic assumptions
│   ├── geographic.py                 #   Project site metadata
│   ├── setup.py                      #   Interactive configuration (widgets)
│   ├── timeseries.py                 #   Load & validate 8760-hour profiles
│   ├── model.py                      #   Pyomo MILP formulation
│   └── visualization.py              #   Results summaries and charts
│
├── data/                             # Input time series
│   ├── geographic.csv                #   Project location
│   ├── electricity_demand.csv        #   Hourly building electricity demand (kW)
│   ├── pv_generation.csv             #   Normalised PV generation profile (kW/kWp)
│   └── heatpump_load.csv            #   Normalised heating load profile (0–1)
│
├── result/                           # Generated charts and reports
│
├── requirements.txt
└── LICENSE
```

All model logic resides in `src/` as separate Python modules.
The notebook imports these modules and serves as the execution and visualization interface.
Techno-economic assumptions are defined once in `src/constants.py` — no values are hard-coded elsewhere.

---

## Requirements

```bash
pip install -r requirements.txt
```

**GLPK Solver:**
```bash
# Ubuntu / Debian
sudo apt install glpk-utils

# macOS
brew install glpk

# Windows — https://winglpk.sourceforge.net/
```

---

## Usage

1. Prepare input CSV files in the `data/` folder
2. Open `PV_Heat_Pump_Optimization.ipynb`
3. Run cells sequentially:
   - Configure technologies and economic parameters (Step 3)
   - Load time series data (Step 4)
   - Build and solve the model (Step 5)
   - Analyse results (Step 6)

All charts are saved automatically to `result/` as numbered `.png` files.

**Time series data sources:**
- [Renewables.ninja](https://www.renewables.ninja) — PV and wind generation profiles
- [PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/) — European Commission PV estimation tool
- [Global Solar Atlas](https://globalsolaratlas.info) — Solar irradiance data

---

## Configuration

| Parameter | Location |
|---|---|
| Battery efficiency, cycle life, C-rate | `src/constants.py` |
| PV / battery lifetimes | `src/constants.py` |
| Heat pump COP, sizing rule | `src/constants.py` |
| PV O&M cost fraction | `src/constants.py` |
| CAPEX, electricity price, discount rate | Interactive widgets in notebook (Step 3) |

---

## Key Outputs

| Output | Description |
|---|---|
| Optimal PV capacity | kW — least-cost installed PV size |
| Optimal battery capacity | kWh — least-cost storage size |
| Annual energy balance | MWh breakdown by source, self-sufficiency, and self-consumption |
| Cost comparison | Baseline vs. optimised annual electricity cost |
| Simple payback period | Years to recover investment |
| LCOE / LCOS | Levelized cost of electricity and storage |
| KPI dashboard | Self-sufficiency, self-consumption, LCOE, and payback gauges |
| Energy supply mix | Annual supply breakdown (donut chart) |
| Monthly energy balance | Monthly generation vs. demand comparison |
| Hourly heatmap | 24 h × 365 d PV surplus/deficit map |
| CAPEX waterfall | Investment breakdown by technology |
| Dispatch charts | Hourly stacked generation with demand line |
| Battery SoC | State of charge with capacity reference bands |
| Energy flow Sankey | Annual energy routing: source → storage → load → losses |

---

## Disclaimer

Developed for educational and research purposes. Results should not be used as the sole basis for investment decisions. The author makes no guarantees regarding the completeness or accuracy of the model outputs.

---

## References

- Hart, W.E. et al. (2017). *Pyomo – Optimization Modeling in Python*. Springer.
- IRENA (2023). *Renewable Power Generation Costs 2023*. International Renewable Energy Agency.
- IEA (2023). *World Energy Outlook 2023*. International Energy Agency.
- Pfenninger, S. & Staffell, I. (2016). Long-term patterns of European PV output using 30 years of validated hourly reanalysis and satellite data. *Energy*, 114, 1251–1265.
- Staffell, I. & Pfenninger, S. (2016). Using bias-corrected reanalysis to simulate current and future wind power output. *Energy*, 114, 1224–1239.
- Anthropic (2025). *Claude AI Assistant* (claude.ai). Used to support model development, code review, and documentation.

---

*Author: Agus Samsudin — Energy Systems Modelling · Optimization · Renewable Energy*
