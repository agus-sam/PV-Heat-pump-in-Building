"""
Model Constants
===============

All techno-economic assumptions are defined here as named constants.
This is the **only place** where assumptions need to be changed.

Import in the notebook or other modules:
    from src.constants import *
"""

# ── Time resolution ───────────────────────────────────────────────────────────
HOURS_PER_YEAR        = 8760    # Full year hourly resolution

# ── Battery parameters ────────────────────────────────────────────────────────
BATTERY_EFFICIENCY    = 0.90    # Round-trip efficiency
SOC_MIN_FRACTION      = 0.20    # Minimum state-of-charge (avoids deep discharge)
BATTERY_C_RATE        = 3       # Max power = energy capacity / 3
BATTERY_CYCLE_LIFE    = 4000    # Li-ion cycle life at 80 % DoD

# ── Technology lifetimes ──────────────────────────────────────────────────────
PV_LIFETIME_YRS       = 25      # IEA standard
BATTERY_LIFETIME_YRS  = 15      # Typical Li-ion warranty period

# ── Heat pump ─────────────────────────────────────────────────────────────────
HP_COP                = 3.0     # Coefficient of Performance (air-source, moderate climate)
HP_KW_PER_M2          = 0.06    # Sizing rule: 60 W per m² floor area

# ── PV O&M ────────────────────────────────────────────────────────────────────
PV_OPEX_FRACTION      = 0.02    # Annual O&M as fraction of CAPEX
