# DEV.md — solar-energy-potential

## Goal
Calculate solar PV energy potential from NASA POWER solar radiation data.

## Data Source
NASA POWER API: https://power.larc.nasa.gov/api/temporal/daily/point

## Core Functions
1. **assess** — Assess solar potential for a single point
2. **batch** — Batch process from CSV input
3. **economic** — Economic analysis (payback, LCOE)

## Key Parameters
- ALLSKY_SFC_SW_DWN: All Sky Surface Shortwave Downward Irradiation (kWh/m²/day)
- DIFF, DNI: Diffuse and Direct Normal Irradiance

## PV Calculation
- System efficiency: 15-20% (configurable)
- Performance ratio: 0.75-0.85
- Annual output (kWh/kWp) = GHI_annual × performance_ratio

## Dependencies
- requests>=2.28.0, numpy

## Verification
1. `python scripts/solar-energy-potential.py --help` works
2. `assess` subcommand help works
