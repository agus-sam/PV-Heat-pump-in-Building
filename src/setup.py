"""
System Configuration
====================

Interactive ipywidgets interface for technology selection,
economic parameters, and building parameters.
"""

try:
    import ipywidgets as widgets
    from IPython.display import display
except ImportError:
    raise ImportError(
        "ipywidgets and IPython are required for the interactive setup. "
        "Install them with: pip install ipywidgets jupyterlab"
    )


class SetupOptions:
    """Interactive system configuration widget."""

    def __init__(self):
        self.selected_technologies = []
        self.currency_used         = ""
        self.electricity_price     = None
        self.pv_capex              = None
        self.battery_capex         = None
        self.hp_capex              = None
        self.discount_rate         = None
        self.living_space          = None
        self.annual_heating_cost   = None

    def _row(self, widget, unit):
        return widgets.HBox([widget, widgets.Label(unit)])

    def display(self):
        style = {"description_width": "200px"}

        self.tech_boxes = [
            widgets.Checkbox(description="Solar PV",        value=True),
            widgets.Checkbox(description="Battery Storage", value=True),
            widgets.Checkbox(description="Heat Pump",       value=False),
            widgets.Checkbox(description="Grid Backup",     value=True),
        ]
        self.currency_input            = widgets.Text(     value="EUR",  description="Currency",            style=style)
        self.electricity_price_input   = widgets.FloatText(value=0.30,   description="Electricity price",   style=style)
        self.pv_capex_input            = widgets.FloatText(value=1200,   description="PV CAPEX",            style=style)
        self.battery_capex_input       = widgets.FloatText(value=500,    description="Battery CAPEX",       style=style)
        self.hp_capex_input            = widgets.FloatText(value=900,    description="Heat Pump CAPEX",     style=style)
        self.discount_rate_input       = widgets.FloatText(value=0.05,   description="Discount rate",       style=style)
        self.annual_heating_cost_input = widgets.FloatText(value=1500,   description="Annual heating cost", style=style)
        self.living_space_input        = widgets.FloatText(value=120,    description="Living space",        style=style)

        btn    = widgets.Button(description="Confirm Setup", button_style="success")
        output = widgets.Output()

        print("Technology Selection")
        for cb in self.tech_boxes:
            display(cb)
        print("\nEconomic Parameters")
        display(self.currency_input)
        display(self._row(self.electricity_price_input,   "/kWh"))
        display(self._row(self.pv_capex_input,            "/kW"))
        display(self._row(self.battery_capex_input,       "/kWh"))
        display(self._row(self.hp_capex_input,            "/kW"))
        display(self._row(self.discount_rate_input,       ""))
        display(self._row(self.annual_heating_cost_input, "/year"))
        print("\nBuilding Parameters")
        display(self._row(self.living_space_input, "m²"))
        display(btn)
        display(output)

        def confirm(_):
            self.selected_technologies = [cb.description for cb in self.tech_boxes if cb.value]
            self.currency_used         = self.currency_input.value
            self.electricity_price     = self.electricity_price_input.value
            self.pv_capex              = self.pv_capex_input.value
            self.battery_capex         = self.battery_capex_input.value
            self.hp_capex              = self.hp_capex_input.value
            self.discount_rate         = self.discount_rate_input.value
            self.living_space          = self.living_space_input.value
            self.annual_heating_cost   = self.annual_heating_cost_input.value
            with output:
                output.clear_output()
                print("Setup confirmed.")
                print(f"  Technologies      : {self.selected_technologies}")
                print(f"  Currency          : {self.currency_used}")
                print(f"  Electricity price : {self.electricity_price} {self.currency_used}/kWh")
                print(f"  PV CAPEX          : {self.pv_capex} {self.currency_used}/kW")
                print(f"  Battery CAPEX     : {self.battery_capex} {self.currency_used}/kWh")
                print(f"  Discount rate     : {self.discount_rate:.1%}")
                print(f"  Living space      : {self.living_space} m²")
        btn.on_click(confirm)
