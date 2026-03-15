"""
Results Visualization
=====================

Professional charts and text summaries of MILP optimization results.
All charts share a consistent colour palette and matplotlib style.

Charts:
    1. KPI Dashboard          — key performance indicators at a glance
    2. Energy Supply Mix      — donut chart with self-sufficiency centre
    3. Battery Charging       — donut chart of PV vs grid charging
    4. Monthly Energy Balance — stacked bar by month
    5. Hourly Demand Heatmap  — 24h × 365d generation vs demand
    6. Annual Cost Comparison — stacked bar: baseline vs optimised
    7. CAPEX Waterfall        — investment breakdown waterfall
    8. Hourly Dispatch        — stacked area (configurable window)
    9. Battery SoC            — state of charge trace
   10. Energy Flow Sankey     — full source → storage → load → losses
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pyomo.environ as pyo

from src.constants import (
    BATTERY_EFFICIENCY,
    HP_COP,
    HP_KW_PER_M2,
    SOC_MIN_FRACTION,
    PV_LIFETIME_YRS,
    BATTERY_LIFETIME_YRS,
    PV_OPEX_FRACTION,
)
from src.model import BuildingEnergyMILP


class ResultsVisualization:
    """
    Professional visualisation of MILP optimization results.

    All charts share the global rcParams style set in the notebook.
    Every plot method accepts an optional save_path to export a .png file.
    """

    # ── Shared color palette ───────────────────────────────────────────────
    C = {
        "Solar":      "#F4B942",   # warm amber (PV to load)
        "SolarBatt":  "#E8851A",   # deep amber (PV to battery)
        "Battery":    "#4E9AF1",   # calm blue
        "Grid":       "#8C8C8C",   # neutral grey
        "Curtail":    "#E05C5C",   # muted red
        "Demand":     "#1A1A2E",   # near-black
        "Load":       "#3DAA5C",   # green
        "Losses":     "#C084FC",   # purple
        "HP":         "#F97316",   # orange for heat pump
    }

    def __init__(self, model, setup, ts):
        self.model    = model.model
        self.setup    = setup
        self.ts       = ts
        self.currency = setup.currency_used
        self._cache   = {}
        self._compute_all()

    # ── Pre-compute all hourly data once ──────────────────────────────────

    def _compute_all(self):
        """Extract all hourly arrays and annual totals into cache."""
        m   = self.model
        dem = self.ts.total_demand
        T   = list(m.T)
        n   = len(T)

        grid     = np.array([self._val(m.GridImport[t]) for t in T])
        charge   = np.array([self._val(m.Charge[t])     for t in T])
        discharge= np.array([self._val(m.Discharge[t])  for t in T])
        curtail  = np.array([self._val(m.PVCurtail[t])  for t in T])
        soc      = np.array([self._val(m.SOC[t])        for t in T])
        pv_cap   = self._val(m.PVCap)
        bat_cap  = self._val(m.BatteryEnergyCap)
        prof     = self.ts.pv_generation
        pv_gen   = np.array([pv_cap * (prof[t] if prof is not None else 0) for t in T])

        # Decompose PV flows
        pv_direct    = np.zeros(n)
        pv_to_batt   = np.zeros(n)
        grid_to_load = np.zeros(n)
        grid_to_batt = np.zeros(n)

        for i, t in enumerate(T):
            pv_used = max(0, pv_gen[i] - curtail[i])
            pv_b    = min(pv_used, charge[i])
            pv_d    = max(0, pv_used - pv_b)
            g_b     = max(0, charge[i] - pv_b)
            g_l     = max(0, grid[i] - g_b)
            pv_direct[i]    = pv_d
            pv_to_batt[i]   = pv_b
            grid_to_load[i] = g_l
            grid_to_batt[i] = g_b

        # Battery losses = energy charged minus energy discharged
        batt_losses = max(0, charge.sum() - discharge.sum())

        self._cache = {
            "grid": grid, "charge": charge, "discharge": discharge,
            "curtail": curtail, "soc": soc, "pv_gen": pv_gen,
            "pv_direct": pv_direct, "pv_to_batt": pv_to_batt,
            "grid_to_load": grid_to_load, "grid_to_batt": grid_to_batt,
            "demand": dem, "pv_cap": pv_cap, "bat_cap": bat_cap,
            "batt_losses": batt_losses,
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    def _val(self, var):
        """Safely extract Pyomo variable value; returns 0 if unavailable."""
        try:
            v = pyo.value(var)
            return v if v is not None else 0.0
        except Exception:
            return 0.0

    def _parse_hours(self, hours):
        """Accept (start, end) tuple or single int (returns 168-hour window)."""
        return hours if isinstance(hours, tuple) else (hours, hours + 168)

    @staticmethod
    def _style_ax(ax, title, xlabel="", ylabel="", legend=True):
        """Apply consistent finishing style to an axes object."""
        ax.set_title(title, pad=10)
        if xlabel: ax.set_xlabel(xlabel)
        if ylabel: ax.set_ylabel(ylabel)
        if legend:
            ax.legend(framealpha=0.9, edgecolor="#cccccc",
                      loc="upper left", fontsize=9)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
        )

    @staticmethod
    def _save(fig, save_path):
        if save_path:
            d = os.path.dirname(save_path)
            if d:
                os.makedirs(d, exist_ok=True)
            fig.savefig(save_path, dpi=200, bbox_inches="tight", facecolor="white")

    # ══════════════════════════════════════════════════════════════════════
    #  TEXT SUMMARIES
    # ══════════════════════════════════════════════════════════════════════

    def summary(self):
        d = self._cache
        print("\n" + "="*45)
        print(" OPTIMAL SYSTEM SIZING")
        print("="*45)
        print(f"  Solar PV capacity      : {d['pv_cap']:>8.2f}  kW")
        print(f"  Battery capacity       : {d['bat_cap']:>8.2f}  kWh")
        if "Heat Pump" in self.setup.selected_technologies:
            hp = self.setup.living_space * HP_KW_PER_M2
            print(f"  Heat pump size         : {hp:>8.2f}  kW  (COP = {HP_COP})")
        print("="*45)

    def capex(self):
        d = self._cache
        c = self.currency
        pv_inv   = d["pv_cap"]  * self.setup.pv_capex
        batt_inv = d["bat_cap"] * self.setup.battery_capex
        hp_inv   = 0
        if "Heat Pump" in self.setup.selected_technologies:
            hp_inv = self.setup.living_space * HP_KW_PER_M2 * self.setup.hp_capex
        total = pv_inv + batt_inv + hp_inv
        print("\n" + "="*45)
        print(" INVESTMENT CAPEX")
        print("="*45)
        print(f"  Solar PV               : {pv_inv:>10,.2f}  {c}")
        print(f"  Battery storage        : {batt_inv:>10,.2f}  {c}")
        if hp_inv:
            print(f"  Heat pump              : {hp_inv:>10,.2f}  {c}")
        print("-"*45)
        print(f"  Total investment       : {total:>10,.2f}  {c}")
        print("="*45)

    def annual_energy(self):
        d = self._cache
        mwh = lambda x: x / 1000
        total_dem = d["demand"].sum()
        pv_tot    = d["pv_gen"].sum()
        pv_dir    = d["pv_direct"].sum()
        pv_batt   = d["pv_to_batt"].sum()
        pv_curt   = d["curtail"].sum()
        grid_tot  = d["grid"].sum()
        batt_dis  = d["discharge"].sum()
        losses    = d["batt_losses"]
        print("\n" + "="*50)
        print(" ANNUAL ENERGY BALANCE")
        print("="*50)
        print(f"  Total demand           : {mwh(total_dem):>8.2f}  MWh")
        print(f"  Total PV generation    : {mwh(pv_tot):>8.2f}  MWh")
        print(f"  PV direct to load      : {mwh(pv_dir):>8.2f}  MWh")
        print(f"  PV via battery         : {mwh(pv_batt):>8.2f}  MWh")
        print(f"  PV curtailed           : {mwh(pv_curt):>8.2f}  MWh")
        print(f"  Grid import            : {mwh(grid_tot):>8.2f}  MWh")
        print(f"  Battery discharge      : {mwh(batt_dis):>8.2f}  MWh")
        print(f"  Battery losses         : {mwh(losses):>8.2f}  MWh")
        ss = (1 - grid_tot / total_dem) * 100 if total_dem > 0 else 0
        sc = (pv_dir + pv_batt) / pv_tot * 100 if pv_tot > 0 else 0
        print("-"*50)
        print(f"  Self-sufficiency       : {ss:>8.1f}  %")
        print(f"  Self-consumption       : {sc:>8.1f}  %")
        print("="*50)

    def economics(self):
        d          = self._cache
        c          = self.currency
        price      = self.setup.electricity_price
        r          = self.setup.discount_rate
        pv_capex   = self.setup.pv_capex
        batt_capex = self.setup.battery_capex
        pv_size    = d["pv_cap"]
        batt_size  = d["bat_cap"]
        total_dem  = d["demand"].sum()
        grid_e     = d["grid"].sum()
        baseline   = total_dem * price
        optimised  = grid_e    * price
        savings    = baseline - optimised
        sav_pct    = savings / baseline * 100 if baseline > 0 else 0
        pv_inv     = pv_size   * pv_capex
        batt_inv   = batt_size * batt_capex
        hp_inv     = 0
        if "Heat Pump" in self.setup.selected_technologies:
            hp_inv = self.setup.living_space * HP_KW_PER_M2 * self.setup.hp_capex
        total_inv  = pv_inv + batt_inv + hp_inv
        payback    = total_inv / savings if savings > 0 else float("inf")
        print("\n" + "="*55)
        print(" ECONOMIC RESULTS")
        print("="*55)
        print(f"  Baseline electricity cost  : {baseline:>10,.2f}  {c}/yr")
        print(f"  Optimised electricity cost : {optimised:>10,.2f}  {c}/yr")
        print(f"  Annual savings             : {savings:>10,.2f}  {c}  ({sav_pct:.1f}%)")
        print(f"  Simple payback period      : {payback:>10.1f}  years")
        if "Heat Pump" in self.setup.selected_technologies:
            base_hp  = baseline + self.setup.annual_heating_cost
            opt_hp   = optimised
            sav_hp   = base_hp - opt_hp
            sav_hp_p = sav_hp / base_hp * 100 if base_hp > 0 else 0
            pb_hp    = total_inv / sav_hp if sav_hp > 0 else float("inf")
            print("\n  [Heat pump replacing gas/oil heating]")
            print(f"  Baseline (elec + heating)  : {base_hp:>10,.2f}  {c}/yr")
            print(f"  Optimised (PV + batt + HP) : {opt_hp:>10,.2f}  {c}/yr")
            print(f"  Annual savings             : {sav_hp:>10,.2f}  {c}  ({sav_hp_p:.1f}%)")
            print(f"  Simple payback period      : {pb_hp:>10.1f}  years")
        crf_pv   = BuildingEnergyMILP._crf(r, PV_LIFETIME_YRS)
        crf_batt = BuildingEnergyMILP._crf(r, BATTERY_LIFETIME_YRS)
        pv_ann   = pv_size   * (pv_capex   * crf_pv   + pv_capex * PV_OPEX_FRACTION)
        batt_ann = batt_size * (batt_capex * crf_batt)
        sys_cost = grid_e * price + pv_ann + batt_ann
        bl_lcoe  = baseline  / total_dem if total_dem > 0 else 0
        op_lcoe  = sys_cost  / total_dem if total_dem > 0 else 0
        pv_tot   = d["pv_gen"].sum()
        batt_dis = d["discharge"].sum()
        print("\n  Levelized Cost of Electricity")
        print("-"*55)
        print(f"  Baseline LCOE              : {bl_lcoe:.4f}  {c}/kWh")
        print(f"  Optimised LCOE             : {op_lcoe:.4f}  {c}/kWh")
        if pv_tot  > 0: print(f"  PV LCOE                    : {pv_ann  / pv_tot:.4f}  {c}/kWh")
        if batt_dis> 0: print(f"  Battery LCOS               : {batt_ann/ batt_dis:.4f}  {c}/kWh")
        print("="*55)

    # ══════════════════════════════════════════════════════════════════════
    #  CHARTS
    # ══════════════════════════════════════════════════════════════════════

    # 1 ── KPI Dashboard ──────────────────────────────────────────────────

    def plot_kpi_dashboard(self, save_path=None):
        """4-panel KPI dashboard: key metrics at a glance."""
        d     = self._cache
        c     = self.currency
        price = self.setup.electricity_price
        r     = self.setup.discount_rate

        total_dem = d["demand"].sum()
        grid_tot  = d["grid"].sum()
        pv_tot    = d["pv_gen"].sum()
        pv_dir    = d["pv_direct"].sum()
        pv_batt   = d["pv_to_batt"].sum()

        self_suff = (1 - grid_tot / total_dem) * 100 if total_dem > 0 else 0
        self_cons = (pv_dir + pv_batt) / pv_tot * 100 if pv_tot > 0 else 0

        baseline = total_dem * price
        opt_cost = grid_tot * price
        crf_pv   = BuildingEnergyMILP._crf(r, PV_LIFETIME_YRS)
        crf_batt = BuildingEnergyMILP._crf(r, BATTERY_LIFETIME_YRS)
        pv_ann   = d["pv_cap"] * (self.setup.pv_capex * crf_pv + self.setup.pv_capex * PV_OPEX_FRACTION)
        batt_ann = d["bat_cap"] * self.setup.battery_capex * crf_batt
        sys_cost = opt_cost + pv_ann + batt_ann
        lcoe     = sys_cost / total_dem if total_dem > 0 else 0

        savings  = baseline - opt_cost
        total_inv = d["pv_cap"] * self.setup.pv_capex + d["bat_cap"] * self.setup.battery_capex
        payback  = total_inv / savings if savings > 0 else float("inf")

        fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))

        kpis = [
            ("Self-Sufficiency",  f"{self_suff:.1f}%",     self.C["Solar"],   self_suff / 100),
            ("Self-Consumption",  f"{self_cons:.1f}%",     self.C["Load"],    self_cons / 100),
            ("Optimised LCOE",    f"{lcoe:.3f}\n{c}/kWh", self.C["Battery"], min(1.0, 0.3 / lcoe) if lcoe > 0 else 0),
            ("Simple Payback",    f"{payback:.1f} yr",     self.C["Grid"],    min(1.0, 10 / payback) if payback < float("inf") else 0),
        ]

        for ax, (title, value, color, fill) in zip(axes, kpis):
            theta = np.linspace(0.75 * np.pi, 0.25 * np.pi, 100)
            ax.plot(np.cos(theta), np.sin(theta), color="#e0e0e0", linewidth=14, solid_capstyle="round")
            n_fill = max(1, int(fill * 100))
            theta_fill = np.linspace(0.75 * np.pi, 0.75 * np.pi - fill * 0.5 * 2 * np.pi, n_fill)
            ax.plot(np.cos(theta_fill), np.sin(theta_fill), color=color, linewidth=14, solid_capstyle="round")
            ax.text(0, -0.1, value, ha="center", va="center", fontsize=16, fontweight="bold", color="#1a1a2e")
            ax.text(0, -0.65, title, ha="center", va="center", fontsize=10, color="#666666")
            ax.set_xlim(-1.3, 1.3)
            ax.set_ylim(-0.9, 1.3)
            ax.set_aspect("equal")
            ax.axis("off")

        fig.suptitle("System Performance Overview", fontsize=14, fontweight="bold", y=1.02)
        plt.tight_layout()
        self._save(fig, save_path)
        plt.show()

    # 2 ── Energy Supply Mix ──────────────────────────────────────────────

    def plot_energy_mix(self, save_path=None):
        """Donut chart with self-sufficiency centre KPI."""
        d       = self._cache
        pv_used = d["pv_direct"].sum() + d["pv_to_batt"].sum()
        grid    = d["grid"].sum()
        batt    = d["discharge"].sum()
        total   = d["demand"].sum()
        self_suff = (1 - grid / total) * 100 if total > 0 else 0

        labels = ["Solar PV", "Grid", "Battery"]
        values = [pv_used, grid, batt]
        colors = [self.C["Solar"], self.C["Grid"], self.C["Battery"]]

        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors,
            autopct="%1.1f%%", startangle=90, pctdistance=0.75,
            wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5)
        )
        for at in autotexts:
            at.set_fontsize(10); at.set_fontweight("bold")
        ax.text(0, 0.06, f"{self_suff:.0f}%", ha="center", va="center",
                fontsize=28, fontweight="bold", color="#1a1a2e")
        ax.text(0, -0.16, "self-sufficient", ha="center", va="center",
                fontsize=9, color="#888888")
        ax.set_title("Annual Energy Supply Mix", pad=16, fontweight="bold")
        plt.tight_layout()
        self._save(fig, save_path)
        plt.show()

    # 3 ── Battery Charging Sources ───────────────────────────────────────

    def plot_battery_sources(self, save_path=None):
        """Donut chart: battery charging energy sources."""
        d        = self._cache
        pv_ch    = d["pv_to_batt"].sum()
        grid_ch  = d["grid_to_batt"].sum()
        total_ch = d["charge"].sum()
        if total_ch < 1e-6:
            print("No battery charging in this scenario.")
            return
        pv_mwh, grid_mwh = pv_ch / 1000, grid_ch / 1000
        pv_pct   = pv_ch / total_ch * 100
        grid_pct = grid_ch / total_ch * 100
        labels = [f"PV  {pv_mwh:.1f} MWh ({pv_pct:.0f}%)",
                  f"Grid  {grid_mwh:.1f} MWh ({grid_pct:.0f}%)"]
        colors = [self.C["Solar"], self.C["Grid"]]
        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, _ = ax.pie([pv_mwh, grid_mwh], colors=colors, startangle=90,
                           wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2.5))
        ax.legend(wedges, labels, loc="lower center",
                  bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False)
        ax.set_title("Battery Charging Sources", pad=16, fontweight="bold")
        plt.tight_layout()
        self._save(fig, save_path)
        plt.show()

    # 4 ── Monthly Energy Balance ─────────────────────────────────────────

    def plot_monthly_balance(self, save_path=None):
        """Stacked bar chart: monthly energy breakdown by source."""
        d = self._cache
        month_hours = [31*24, 28*24, 31*24, 30*24, 31*24, 30*24,
                       31*24, 31*24, 30*24, 31*24, 30*24, 31*24]
        month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]

        pv_m = []; grid_m = []; batt_m = []; dem_m = []; curt_m = []
        idx = 0
        for h in month_hours:
            sl = slice(idx, idx + h)
            pv_m.append(d["pv_direct"][sl].sum() / 1000)
            grid_m.append(d["grid"][sl].sum() / 1000)
            batt_m.append(d["discharge"][sl].sum() / 1000)
            dem_m.append(d["demand"][sl].sum() / 1000)
            curt_m.append(d["curtail"][sl].sum() / 1000)
            idx += h

        pv_m = np.array(pv_m); grid_m = np.array(grid_m)
        batt_m = np.array(batt_m); dem_m = np.array(dem_m); curt_m = np.array(curt_m)
        x = np.arange(12); w = 0.35

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.bar(x - w/2, pv_m,   w, label="PV direct",         color=self.C["Solar"],   alpha=0.85)
        ax.bar(x - w/2, batt_m, w, label="Battery discharge",  color=self.C["Battery"], alpha=0.85, bottom=pv_m)
        ax.bar(x - w/2, grid_m, w, label="Grid import",        color=self.C["Grid"],    alpha=0.85, bottom=pv_m + batt_m)
        ax.bar(x + w/2, dem_m,  w, label="Demand", color=self.C["Demand"], alpha=0.25,
               edgecolor=self.C["Demand"], linewidth=1.2)

        if curt_m.sum() > 0.01:
            ax.scatter(x - w/2, pv_m + batt_m + grid_m + curt_m * 0.5,
                       s=curt_m * 200 + 1, color=self.C["Curtail"], marker="v",
                       label="Curtailment", zorder=5, alpha=0.8)

        ax.set_xticks(x); ax.set_xticklabels(month_names)
        self._style_ax(ax, "Monthly Energy Balance", ylabel="Energy  (MWh)")
        ax.legend(loc="upper left", fontsize=9, framealpha=0.9, edgecolor="#cccccc", ncol=2)
        plt.tight_layout()
        self._save(fig, save_path)
        plt.show()

    # 5 ── Hourly Heatmap ─────────────────────────────────────────────────

    def plot_heatmap(self, save_path=None):
        """Heatmap: hourly net surplus/deficit (24h × 365d)."""
        d   = self._cache
        pv  = d["pv_gen"][:8760]
        dem = d["demand"][:8760]
        net = pv - dem
        n_days = 365
        mat = net[:n_days * 24].reshape(n_days, 24).T

        fig, ax = plt.subplots(figsize=(14, 4.5))
        vmax = max(abs(mat.min()), abs(mat.max()))
        im = ax.imshow(mat, aspect="auto", cmap="RdYlGn", vmin=-vmax, vmax=vmax,
                       interpolation="bilinear")

        month_starts = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        month_names  = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        ax.set_xticks(month_starts); ax.set_xticklabels(month_names, fontsize=9)
        ax.set_yticks([0, 6, 12, 18, 23])
        ax.set_yticklabels(["00:00", "06:00", "12:00", "18:00", "23:00"])

        cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
        cbar.set_label("Net Surplus / Deficit  (kW)", fontsize=10)

        ax.set_title("Hourly PV Generation vs. Demand  (green = surplus, red = deficit)",
                      pad=10, fontweight="bold")
        ax.set_ylabel("Hour of Day")
        plt.tight_layout()
        self._save(fig, save_path)
        plt.show()

    # 6 ── Annual Cost Comparison ─────────────────────────────────────────

    def plot_economics(self, save_path=None):
        """Stacked bar chart: baseline vs optimised annual cost."""
        d = self._cache; c = self.currency; price = self.setup.electricity_price
        r = self.setup.discount_rate
        grid_e   = d["grid"].sum()
        baseline = d["demand"].sum() * price
        opt_grid = grid_e * price
        crf_pv   = BuildingEnergyMILP._crf(r, PV_LIFETIME_YRS)
        crf_batt = BuildingEnergyMILP._crf(r, BATTERY_LIFETIME_YRS)
        pv_ann   = d["pv_cap"]  * (self.setup.pv_capex * crf_pv + self.setup.pv_capex * PV_OPEX_FRACTION)
        batt_ann = d["bat_cap"] * self.setup.battery_capex * crf_batt
        categories  = ["Baseline\n(grid only)", "Optimised\n(PV + battery)"]
        grid_costs  = [baseline, opt_grid]
        capex_costs = [0, pv_ann + batt_ann]
        x = np.arange(2); w = 0.5

        fig, ax = plt.subplots(figsize=(7, 5))
        b1 = ax.bar(x, grid_costs,  w, label="Grid electricity cost",  color=self.C["Grid"],    alpha=0.85)
        b2 = ax.bar(x, capex_costs, w, label="Annualised system CAPEX", color=self.C["Battery"], alpha=0.85, bottom=grid_costs)
        for bar, val in zip(b1, grid_costs):
            ax.text(bar.get_x() + bar.get_width()/2, val/2,
                    f"{val:,.0f}", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        for bar, bot, val in zip(b2, grid_costs, capex_costs):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bot + val/2,
                        f"{val:,.0f}", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        total_opt = opt_grid + pv_ann + batt_ann
        if baseline > total_opt:
            sav = baseline - total_opt
            ax.annotate(f"  Savings\n  {sav:,.0f} {c}/yr",
                        xy=(1, total_opt), xytext=(1.45, baseline * 0.7),
                        fontsize=9, fontweight="bold", color=self.C["Load"],
                        arrowprops=dict(arrowstyle="->", color=self.C["Load"], lw=1.5))
        ax.set_xticks(x); ax.set_xticklabels(categories)
        self._style_ax(ax, title=f"Annual Cost Comparison  ({c}/yr)", ylabel=f"{c}/yr")
        plt.tight_layout()
        self._save(fig, save_path)
        plt.show()

    # 7 ── CAPEX Waterfall ────────────────────────────────────────────────

    def plot_capex_waterfall(self, save_path=None):
        """Waterfall chart: investment cost breakdown."""
        d = self._cache; c = self.currency
        pv_inv   = d["pv_cap"]  * self.setup.pv_capex
        batt_inv = d["bat_cap"] * self.setup.battery_capex
        hp_inv   = 0
        if "Heat Pump" in self.setup.selected_technologies:
            hp_inv = self.setup.living_space * HP_KW_PER_M2 * self.setup.hp_capex

        items = []; values = []; colors = []
        if pv_inv   > 0: items.append("Solar PV");  values.append(pv_inv);   colors.append(self.C["Solar"])
        if batt_inv > 0: items.append("Battery");   values.append(batt_inv); colors.append(self.C["Battery"])
        if hp_inv   > 0: items.append("Heat Pump"); values.append(hp_inv);   colors.append(self.C["HP"])
        total = sum(values)
        items.append("TOTAL"); values.append(total); colors.append(self.C["Demand"])

        bottoms = []; running = 0
        for i, v in enumerate(values):
            bottoms.append(running if i < len(values) - 1 else 0)
            if i < len(values) - 1: running += v

        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(items, values, bottom=bottoms, color=colors, width=0.5,
                       edgecolor="white", linewidth=1.5, alpha=0.88)
        for i in range(len(items) - 2):
            top = bottoms[i] + values[i]
            ax.plot([i + 0.25, i + 0.75], [top, top], color="#aaa", linewidth=1, linestyle="--")
        for bar, bot, val in zip(bars, bottoms, values):
            ax.text(bar.get_x() + bar.get_width()/2, bot + val/2,
                    f"{val:,.0f}", ha="center", va="center", fontsize=10, fontweight="bold", color="white")
        self._style_ax(ax, f"Investment Breakdown  ({c})", ylabel=c, legend=False)
        plt.tight_layout()
        self._save(fig, save_path)
        plt.show()

    # 8 ── Hourly Dispatch ────────────────────────────────────────────────

    def plot_dispatch(self, hours=(4032, 4200), save_path=None):
        """Stacked area dispatch chart with curtailment overlay."""
        d = self._cache; start, end = self._parse_hours(hours)
        T = list(range(start, end)); sl = slice(start, end)

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.stackplot(
            T, d["pv_direct"][sl], d["pv_to_batt"][sl], d["discharge"][sl], d["grid"][sl],
            labels=["PV → load", "PV → battery", "Battery discharge", "Grid"],
            colors=[self.C["Solar"], self.C["SolarBatt"], self.C["Battery"], self.C["Grid"]],
            alpha=0.88
        )
        curt = d["curtail"][sl]
        if curt.sum() > 0:
            top = d["pv_direct"][sl] + d["pv_to_batt"][sl] + d["discharge"][sl] + d["grid"][sl]
            ax.fill_between(T, top, top + curt, color=self.C["Curtail"],
                            alpha=0.55, hatch="//", label="Curtailment", linewidth=0)
        ax.plot(T, d["demand"][sl], color=self.C["Demand"], linewidth=2,
                linestyle="--", label="Demand", zorder=5)
        self._style_ax(ax, f"Hourly System Dispatch  (hours {start}–{end})",
                        xlabel="Hour of year", ylabel="Power  (kW)")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}"))
        plt.tight_layout()
        self._save(fig, save_path)
        plt.show()

    # 9 ── Battery SoC ────────────────────────────────────────────────────

    def plot_soc(self, hours=(4032, 4200), save_path=None):
        """Battery state of charge with capacity reference bands."""
        d = self._cache; start, end = self._parse_hours(hours)
        T = list(range(start, end)); soc = d["soc"][start:end]; cap = d["bat_cap"]

        fig, ax = plt.subplots(figsize=(14, 3.5))
        ax.fill_between(T, soc, alpha=0.35, color=self.C["Battery"])
        ax.plot(T, soc, color=self.C["Battery"], linewidth=2, label="SoC")
        ax.axhline(cap, color="#aaa", linestyle=":", linewidth=1.2, label=f"Capacity ({cap:.1f} kWh)")
        ax.axhline(cap * SOC_MIN_FRACTION, color=self.C["Curtail"], linestyle="--",
                    linewidth=1.2, label=f"Min SoC ({SOC_MIN_FRACTION:.0%})")
        self._style_ax(ax, f"Battery State of Charge  (hours {start}–{end})",
                        xlabel="Hour of year", ylabel="Energy  (kWh)")
        plt.tight_layout()
        self._save(fig, save_path)
        plt.show()

    # 10 ── Energy Flow Sankey ────────────────────────────────────────────

    def plot_energy_sankey(self, save_path=None):
        """
        Full energy-flow Sankey diagram (Plotly).

        Nodes:
            Generation:  Solar PV · Grid
            Storage:     Battery
            Consumption: Building Load
            Losses:      Curtailment · Battery Losses

        Flows:
            PV → Load (direct)          PV → Battery (charge)
            PV → Curtailment            Grid → Load (direct)
            Grid → Battery (charge)     Battery → Load (discharge)
            Battery → Losses (round-trip)
        """
        import plotly.graph_objects as go

        d = self._cache
        to_mwh = lambda x: round(x / 1000, 2)

        pv_direct    = to_mwh(d["pv_direct"].sum())
        pv_to_batt   = to_mwh(d["pv_to_batt"].sum())
        pv_curtail   = to_mwh(d["curtail"].sum())
        grid_to_load = to_mwh(d["grid_to_load"].sum())
        grid_to_batt = to_mwh(d["grid_to_batt"].sum())
        batt_to_load = to_mwh(d["discharge"].sum())
        batt_losses  = to_mwh(d["batt_losses"])

        # Node indices:  0=PV  1=Grid  2=Battery  3=Load  4=Curtailment  5=Losses
        node_labels = [
            f"Solar PV<br>{to_mwh(d['pv_gen'].sum())} MWh",
            f"Grid<br>{to_mwh(d['grid'].sum())} MWh",
            f"Battery<br>{d['bat_cap']:.1f} kWh",
            f"Building Load<br>{to_mwh(d['demand'].sum())} MWh",
            f"Curtailment<br>{pv_curtail} MWh",
            f"Losses<br>{batt_losses} MWh",
        ]
        node_colors = [self.C["Solar"], self.C["Grid"], self.C["Battery"],
                       self.C["Load"], self.C["Curtail"], self.C["Losses"]]

        sources = []; targets = []; values = []; labels = []; link_colors = []
        def add(s, t, v, col):
            if v > 0.001:
                sources.append(s); targets.append(t); values.append(v)
                labels.append(f"{v:.2f} MWh"); link_colors.append(col)

        add(0, 3, pv_direct,    "rgba(244,185,66,0.35)")    # PV → Load
        add(0, 2, pv_to_batt,   "rgba(232,133,26,0.35)")    # PV → Battery
        add(0, 4, pv_curtail,   "rgba(224,92,92,0.35)")     # PV → Curtailment
        add(1, 3, grid_to_load, "rgba(140,140,140,0.35)")   # Grid → Load
        add(1, 2, grid_to_batt, "rgba(140,140,140,0.25)")   # Grid → Battery
        add(2, 3, batt_to_load, "rgba(78,154,241,0.35)")    # Battery → Load
        add(2, 5, batt_losses,  "rgba(192,132,252,0.35)")   # Battery → Losses

        fig = go.Figure(go.Sankey(
            arrangement="snap",
            node=dict(pad=25, thickness=28, line=dict(color="#ffffff", width=1.5),
                      label=node_labels, color=node_colors),
            link=dict(source=sources, target=targets, value=values,
                      label=labels, color=link_colors)
        ))
        fig.update_layout(
            title=dict(text="Annual Energy Flow  (MWh)",
                       font=dict(size=16, family="DejaVu Sans"), x=0.5, xanchor="center"),
            font=dict(size=12, family="DejaVu Sans"),
            paper_bgcolor="white", plot_bgcolor="white",
            height=480, margin=dict(l=30, r=30, t=60, b=30),
        )
        fig.show()

    # ── Run all ──────────────────────────────────────────────────────────

    def plot_all(self, hours=(4032, 4200), save_dir=None):
        """Run every text summary and chart. Optionally save all to save_dir."""
        self.summary()
        self.capex()
        self.annual_energy()
        self.economics()

        sp = lambda name: os.path.join(save_dir, name) if save_dir else None
        self.plot_kpi_dashboard(    save_path=sp("01_kpi_dashboard.png"))
        self.plot_energy_mix(       save_path=sp("02_energy_mix.png"))
        self.plot_battery_sources(  save_path=sp("03_battery_sources.png"))
        self.plot_monthly_balance(  save_path=sp("04_monthly_balance.png"))
        self.plot_heatmap(          save_path=sp("05_heatmap.png"))
        self.plot_economics(        save_path=sp("06_cost_comparison.png"))
        self.plot_capex_waterfall(  save_path=sp("07_capex_waterfall.png"))
        self.plot_dispatch(hours,   save_path=sp("08_dispatch.png"))
        self.plot_soc(hours,        save_path=sp("09_soc.png"))
        self.plot_energy_sankey(    save_path=sp("10_energy_sankey.png"))

        if save_dir:
            print(f"\nAll figures saved to {save_dir}/")
