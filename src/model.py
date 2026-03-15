"""
Optimization Model (MILP)
=========================

Mixed Integer Linear Programming formulation using Pyomo + GLPK.
Determines optimal PV capacity, battery capacity, and hourly dispatch
to minimise total annualised system cost.
"""

import pyomo.environ as pyo

from src.constants import (
    BATTERY_EFFICIENCY,
    SOC_MIN_FRACTION,
    BATTERY_C_RATE,
    BATTERY_CYCLE_LIFE,
    PV_LIFETIME_YRS,
    BATTERY_LIFETIME_YRS,
    PV_OPEX_FRACTION,
)


class BuildingEnergyMILP:
    """
    MILP investment + dispatch model for a hybrid building energy system.

    Uses ts.total_demand so heat pump electricity is computed once in
    TimeSeriesData and not duplicated here.
    """

    def __init__(self, setup, ts):
        self.setup = setup
        self.ts    = ts
        self.model = pyo.ConcreteModel()

    @staticmethod
    def _crf(rate, years):
        """Capital Recovery Factor: annualises CAPEX over asset lifetime."""
        r, n = rate, years
        return (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    def build(self):
        demand     = self.ts.total_demand
        pv_profile = self.ts.pv_generation
        T          = range(len(demand))
        T_last     = len(demand) - 1

        m = self.model
        m.T = pyo.Set(initialize=T)

        # ── Decision variables ─────────────────────────────────────────────
        m.PVCap            = pyo.Var(domain=pyo.NonNegativeReals)          # kW
        m.BatteryEnergyCap = pyo.Var(domain=pyo.NonNegativeReals)          # kWh
        m.GridImport       = pyo.Var(m.T, domain=pyo.NonNegativeReals)     # kW
        m.Charge           = pyo.Var(m.T, domain=pyo.NonNegativeReals)     # kW
        m.Discharge        = pyo.Var(m.T, domain=pyo.NonNegativeReals)     # kW
        m.SOC              = pyo.Var(m.T, domain=pyo.NonNegativeReals)     # kWh
        m.PVCurtail        = pyo.Var(m.T, domain=pyo.NonNegativeReals)     # kW

        if "Grid Backup" not in self.setup.selected_technologies:
            m.GridOff = pyo.Constraint(m.T, rule=lambda m, t: m.GridImport[t] == 0)
            print("Grid backup disabled (off-grid mode).")

        eta = BATTERY_EFFICIENCY

        # ── SoC dynamics (cyclic boundary condition) ───────────────────────
        def soc_rule(m, t):
            prev = T_last if t == 0 else t - 1
            return m.SOC[t] == m.SOC[prev] + m.Charge[t] * eta - m.Discharge[t] / eta
        m.SOC_dynamics   = pyo.Constraint(m.T, rule=soc_rule)

        # ── SoC limits ─────────────────────────────────────────────────────
        m.SOCMax         = pyo.Constraint(m.T, rule=lambda m, t: m.SOC[t] <= m.BatteryEnergyCap)
        m.SOCMin         = pyo.Constraint(m.T, rule=lambda m, t: m.SOC[t] >= SOC_MIN_FRACTION * m.BatteryEnergyCap)

        # ── C-rate limits ──────────────────────────────────────────────────
        m.ChargeLimit    = pyo.Constraint(m.T, rule=lambda m, t: m.Charge[t]    <= m.BatteryEnergyCap / BATTERY_C_RATE)
        m.DischargeLimit = pyo.Constraint(m.T, rule=lambda m, t: m.Discharge[t] <= m.BatteryEnergyCap / BATTERY_C_RATE)

        # ── Power balance ──────────────────────────────────────────────────
        def balance(m, t):
            pv_gen = m.PVCap * (pv_profile[t] if pv_profile is not None else 0)
            return pv_gen + m.GridImport[t] + m.Discharge[t] == demand[t] + m.Charge[t] + m.PVCurtail[t]
        m.Balance = pyo.Constraint(m.T, rule=balance)

        # ── Objective ──────────────────────────────────────────────────────
        price      = self.setup.electricity_price
        r          = self.setup.discount_rate
        pv_capex   = self.setup.pv_capex
        batt_capex = self.setup.battery_capex

        crf_pv      = self._crf(r, PV_LIFETIME_YRS)
        crf_batt    = self._crf(r, BATTERY_LIFETIME_YRS)
        pv_annual   = pv_capex   * crf_pv   + pv_capex * PV_OPEX_FRACTION
        batt_annual = batt_capex * crf_batt
        cycle_cost  = batt_capex / BATTERY_CYCLE_LIFE

        total_cost = (
            sum(m.GridImport[t] * price        for t in m.T)
            + sum(m.Discharge[t] * cycle_cost  for t in m.T)
            + m.PVCap            * pv_annual
            + m.BatteryEnergyCap * batt_annual
        )
        m.Obj = pyo.Objective(expr=total_cost, sense=pyo.minimize)

    def solve(self, tee=True):
        solver  = pyo.SolverFactory("glpk")
        results = solver.solve(self.model, tee=tee)
        status  = results.solver.termination_condition
        if status != pyo.TerminationCondition.optimal:
            raise RuntimeError(f"Solver status: {status}. Check model feasibility.")
        print(f"\nOptimal PV capacity      : {pyo.value(self.model.PVCap):.2f} kW")
        print(f"Optimal battery capacity : {pyo.value(self.model.BatteryEnergyCap):.2f} kWh")
