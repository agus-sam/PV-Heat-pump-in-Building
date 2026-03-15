# Data Directory

Place your hourly time-series CSV files here before running the notebook.

## Required Files

| File                      | Rows  | Column | Unit    | Description                       |
|---------------------------|-------|--------|---------|-----------------------------------|
| `pv_generation.csv`       | 8 760 | 1      | kW/kWp  | Normalised PV output (0–1 range)  |
| `electricity_demand.csv`  | 8 760 | 1      | kW      | Hourly building electrical load   |
| `heatpump_load.csv`       | 8 760 | 1      | 0–1     | Normalised heating load profile   |
| `geographic.csv`          | ≥ 1   | 3      | —       | Site name, latitude, longitude    |

## Where to Get Data

- **[Renewables.ninja](https://www.renewables.ninja)** — PV and wind profiles
- **[PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/)** — European Commission PV tool
- **[Global Solar Atlas](https://globalsolaratlas.info)** — Solar irradiance
- **[DWD / Meteonorm](https://meteonorm.com)** — Measured meteorological data

## Example `geographic.csv`

```csv
Name,Latitude,Longitude
Berlin,52.52,13.41
```
