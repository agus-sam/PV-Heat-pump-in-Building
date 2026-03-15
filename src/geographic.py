"""
Geographic Information
=====================

Loads and validates project site location from CSV.
Not used by the optimizer itself — provides context for project reporting.
"""

import pandas as pd

try:
    from IPython.display import display
except ImportError:
    display = print


class GeographicDescription:
    """Load and validate project geographic information."""

    REQUIRED_COLUMNS = {"Name", "Latitude", "Longitude"}

    def __init__(self):
        self.data = None

    def upload(self, filepath="data/geographic.csv"):
        """Load geographic CSV and validate required columns."""
        self.data = pd.read_csv(filepath)

        missing = self.REQUIRED_COLUMNS - set(self.data.columns)
        if missing:
            raise ValueError(f"Geographic file missing columns: {missing}")

        self.data["Latitude"]  = pd.to_numeric(self.data["Latitude"],  errors="coerce")
        self.data["Longitude"] = pd.to_numeric(self.data["Longitude"], errors="coerce")

        if self.data[["Latitude", "Longitude"]].isnull().any().any():
            raise ValueError("Non-numeric coordinates found in geographic file.")

        print("Geographic data loaded.")
        display(self.data)
