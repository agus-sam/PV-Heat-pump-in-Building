"""
Time Series Data
================

Loads and validates hourly PV generation, electricity demand,
and heat pump load profiles (8760 hourly values per year).

The total_demand property computes base load + heat pump electricity
once, and is reused by both the MILP model and the visualizer.
"""

import numpy as np
import pandas as pd

from src.constants import HOURS_PER_YEAR, HP_COP, HP_KW_PER_M2


class TimeSeriesData:
    """
    Load and validate hourly time series profiles.

    The total_demand property (base load + HP electricity) is the single
    source of truth used by both the MILP model and the visualizer.
    """

    def __init__(self, setup):
        self.setup              = setup
        self.pv_generation      = None
        self.heatpump_load      = None
        self.electricity_demand = None
        self._total_demand      = None

    def _load_csv(self, filepath, label):
        """Load a single-column CSV and validate length, NaN, and sign."""
        df  = pd.read_csv(filepath)
        arr = df.iloc[:, 0].astype(float).values
        if len(arr) != HOURS_PER_YEAR:
            raise ValueError(f"{label}: expected {HOURS_PER_YEAR} rows, got {len(arr)}.")
        if np.isnan(arr).any():
            raise ValueError(f"{label}: contains NaN values.")
        if (arr < 0).any():
            raise ValueError(f"{label}: contains negative values.")
        print(f"  {label}: {len(arr)} hourly values loaded.")
        return arr

    def upload_generation(self):
        if "Solar PV" in self.setup.selected_technologies:
            self.pv_generation = self._load_csv("data/pv_generation.csv", "PV generation profile")

    def upload_demand(self):
        self.electricity_demand = self._load_csv("data/electricity_demand.csv", "Electricity demand")

    def upload_heatpump(self):
        if "Heat Pump" in self.setup.selected_technologies:
            self.heatpump_load = self._load_csv("data/heatpump_load.csv", "Heat pump load profile")

    @property
    def total_demand(self):
        """Base electricity demand + heat pump electricity. Computed once and cached."""
        if self._total_demand is not None:
            return self._total_demand
        base = np.array(self.electricity_demand)
        if "Heat Pump" in self.setup.selected_technologies and self.heatpump_load is not None:
            hp_kw   = self.setup.living_space * HP_KW_PER_M2
            hp_elec = self.heatpump_load * hp_kw / HP_COP
            print(f"  Heat pump: {hp_kw:.1f} kW thermal, COP = {HP_COP}")
            self._total_demand = base + hp_elec
        else:
            self._total_demand = base
        return self._total_demand
