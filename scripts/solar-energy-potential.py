#!/usr/bin/env python3
"""
solar-energy-potential: Calculate solar PV energy potential from NASA POWER data.

Privacy Disclosure:
  - Latitude/longitude coordinates are sent to NASA POWER API.
  - NO personal data, cookies, or identifiers are transmitted.
  - NASA POWER is a public NASA service (public domain data).
  - For sensitive locations, consider using local data instead.

License: MIT-0 (Public Domain)
Data Source: NASA POWER API (https://power.larc.nasa.gov/api/temporal/daily/point)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import numpy as np
except ImportError:
    print("ERROR: numpy is required. Install with: pip install numpy>=1.21.0")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests is required. Install with: pip install requests>=2.28.0")
    sys.exit(1)


# ─── Constants ───────────────────────────────────────────────────────────────

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
DEFAULT_YEAR = 2023
DEFAULT_EFFICIENCY = 0.18
DEFAULT_PERFORMANCE_RATIO = 0.80
DEFAULT_CAPACITY_KWP = 1.0
DEFAULT_COST_PER_KWP = 1000.0
DEFAULT_ELECTRICITY_PRICE = 0.10


# ─── Utility functions ───────────────────────────────────────────────────────

def validate_latlon(lat: float, lon: float) -> tuple:
    """Validate latitude and longitude."""
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude {lat} out of range [-90, 90]")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude {lon} out of range [-180, 180]")
    return (lat, lon)


def validate_year(year: int) -> int:
    """Validate year for NASA POWER data."""
    if not (1984 <= year <= 2024):
        raise ValueError(f"Year {year} out of range [1984, 2024]")
    return year


def validate_efficiency(eff: float) -> float:
    """Validate PV panel efficiency."""
    if not (0.05 <= eff <= 0.50):
        raise ValueError(f"Efficiency {eff} out of range [0.05, 0.50]")
    return eff


def validate_performance_ratio(pr: float) -> float:
    """Validate performance ratio."""
    if not (0.50 <= pr <= 0.95):
        raise ValueError(f"Performance ratio {pr} out of range [0.50, 0.95]")
    return pr


# ─── NASA POWER API ──────────────────────────────────────────────────────────

def fetch_nasa_power(lat: float, lon: float, year: int,
                     parameters: str = "ALLSKY_SFC_SW_DWN,DIFF,DNI") -> dict:
    """
    Fetch solar radiation data from NASA POWER API.

    Returns dict with daily values for each parameter.
    """
    params = {
        "parameters": parameters,
        "community": "RE",  # Renewable Energy
        "longitude": lon,
        "latitude": lat,
        "start": f"{year}0101",
        "end": f"{year}1231",
        "format": "JSON",
        "time-standard": "utc",
    }

    try:
        response = requests.get(
            NASA_POWER_URL,
            params=params,
            timeout=60,
            headers={"User-Agent": "solar-energy-potential/0.1.0"},
        )

        if response.status_code != 200:
            print(f"ERROR: NASA POWER API returned status {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            sys.exit(1)

        data = response.json()

        # Check for API errors
        if "errors" in data and data["errors"]:
            print(f"ERROR: NASA POWER API error: {data['errors']}")
            sys.exit(1)

        return data

    except requests.exceptions.Timeout:
        print("ERROR: NASA POWER API request timed out. Try again later.")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to NASA POWER API. Check internet connection.")
        sys.exit(1)


def parse_nasa_power_data(raw_data: dict) -> dict:
    """Parse NASA POWER JSON response into usable arrays."""
    try:
        properties = raw_data.get("properties", {})
        parameter_data = properties.get("parameter", {})

        result = {}
        for param_name, daily_values in parameter_data.items():
            values = np.array(list(daily_values.values()), dtype=np.float64)
            # Replace fill values (-999) with NaN
            values[values == -999] = np.nan
            result[param_name] = values

        return result

    except Exception as e:
        print(f"ERROR: Failed to parse NASA POWER data: {e}")
        sys.exit(1)


# ─── Solar calculations ──────────────────────────────────────────────────────

def compute_annual_ghi(daily_ghi: np.ndarray) -> float:
    """Compute annual GHI from daily values (kWh/m²/day -> kWh/m²/year)."""
    valid = daily_ghi[~np.isnan(daily_ghi)]
    if len(valid) == 0:
        return 0.0
    return float(np.sum(valid))


def compute_optimal_tilt(lat: float) -> float:
    """
    Estimate optimal tilt angle for fixed PV panels.
    Rule of thumb: tilt ≈ latitude (adjusted for season).
    """
    # Simple approximation: tilt = latitude * 0.87 + 3.1 (for annual optimal)
    # Clamp to reasonable range
    tilt = abs(lat) * 0.87 + 3.1
    return min(tilt, 60.0)  # Cap at 60 degrees


def compute_pv_output(annual_ghi: float, performance_ratio: float = 0.80) -> float:
    """
    Estimate annual PV output.

    Annual output (kWh/kWp) = GHI_annual (kWh/m²/year) × performance_ratio
    """
    return annual_ghi * performance_ratio


def compute_capacity_factor(annual_output: float) -> float:
    """
    Compute capacity factor.

    CF = annual_output / (8760 hours * 1 kWp)
    """
    return annual_output / 8760.0


def compute_economics(
    annual_output: float,
    capacity_kwp: float,
    cost_per_kwp: float,
    electricity_price: float,
) -> dict:
    """Compute economic metrics."""
    total_cost = capacity_kwp * cost_per_kwp
    annual_energy = annual_output * capacity_kwp  # kWh/year
    annual_savings = annual_energy * electricity_price  # USD/year

    # Simple payback (years)
    payback = total_cost / annual_savings if annual_savings > 0 else float("inf")

    # LCOE (Levelized Cost of Energy) - simplified
    # LCOE = total_cost / (annual_energy * lifetime)
    lifetime = 25  # years
    total_energy = annual_energy * lifetime
    lcoe = total_cost / total_energy if total_energy > 0 else float("inf")

    return {
        "total_system_cost_usd": round(total_cost, 2),
        "annual_energy_kwh": round(annual_energy, 2),
        "annual_savings_usd": round(annual_savings, 2),
        "simple_payback_years": round(payback, 2),
        "lcoe_usd_per_kwh": round(lcoe, 4),
        "system_lifetime_years": lifetime,
    }


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_assess(args):
    """Handle assess subcommand."""
    lat, lon = validate_latlon(args.lat, args.lon)
    year = validate_year(args.year)
    efficiency = validate_efficiency(args.efficiency)
    pr = validate_performance_ratio(args.performance_ratio)

    print(f"Solar Energy Assessment")
    print(f"  Location: ({lat:.4f}, {lon:.4f})")
    print(f"  Year: {year}")
    print(f"  PV Efficiency: {efficiency*100:.1f}%")
    print(f"  Performance Ratio: {pr:.2f}")

    # Fetch data
    print(f"\nFetching NASA POWER data...")
    raw_data = fetch_nasa_power(lat, lon, year)
    parsed = parse_nasa_power_data(raw_data)

    # Compute metrics
    daily_ghi = parsed.get("ALLSKY_SFC_SW_DWN", np.array([]))
    daily_diff = parsed.get("DIFF", np.array([]))
    daily_dni = parsed.get("DNI", np.array([]))

    annual_ghi = compute_annual_ghi(daily_ghi)
    optimal_tilt = compute_optimal_tilt(lat)
    annual_output = compute_pv_output(annual_ghi, pr)
    capacity_factor = compute_capacity_factor(annual_output)

    # Monthly GHI
    valid_ghi = daily_ghi[~np.isnan(daily_ghi)]
    n_days = len(valid_ghi)
    daily_mean_ghi = float(np.mean(valid_ghi)) if n_days > 0 else 0.0

    result = {
        "location": {"lat": lat, "lon": lon},
        "year": year,
        "annual_ghi_kwh_m2": round(annual_ghi, 2),
        "daily_mean_ghi_kwh_m2_day": round(daily_mean_ghi, 2),
        "optimal_tilt_degrees": round(optimal_tilt, 1),
        "annual_pv_output_kwh_per_kwp": round(annual_output, 2),
        "capacity_factor_percent": round(capacity_factor * 100, 2),
        "n_valid_days": n_days,
        "system_efficiency": efficiency,
        "performance_ratio": pr,
    }

    # Diffuse fraction
    if len(daily_diff) > 0 and len(daily_ghi) > 0:
        valid_both = ~(np.isnan(daily_diff) | np.isnan(daily_ghi))
        if valid_both.sum() > 0:
            diffuse_fraction = float(np.mean(daily_diff[valid_both] / daily_ghi[valid_both]))
            result["diffuse_fraction"] = round(diffuse_fraction, 3)

    print(f"\nResults:")
    print(f"  Annual GHI: {annual_ghi:.1f} kWh/m²/year")
    print(f"  Daily mean GHI: {daily_mean_ghi:.2f} kWh/m²/day")
    print(f"  Optimal tilt: {optimal_tilt:.1f}°")
    print(f"  Annual PV output: {annual_output:.1f} kWh/kWp")
    print(f"  Capacity factor: {capacity_factor*100:.1f}%")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved: {args.output}")

    if args.json:
        print(json.dumps(result, indent=2))


def cmd_batch(args):
    """Handle batch subcommand — process multiple locations from CSV."""
    import csv

    if not os.path.isfile(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    year = validate_year(args.year)
    efficiency = validate_efficiency(args.efficiency)
    pr = validate_performance_ratio(args.performance_ratio)

    # Read CSV
    locations = []
    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if args.lat_col not in reader.fieldnames:
            print(f"ERROR: Latitude column '{args.lat_col}' not found. Available: {reader.fieldnames}")
            sys.exit(1)
        if args.lon_col not in reader.fieldnames:
            print(f"ERROR: Longitude column '{args.lon_col}' not found. Available: {reader.fieldnames}")
            sys.exit(1)

        for row in reader:
            try:
                lat = float(row[args.lat_col])
                lon = float(row[args.lon_col])
                name = row.get("name", f"loc_{len(locations)}")
                locations.append({"name": name, "lat": lat, "lon": lon})
            except (ValueError, KeyError) as e:
                print(f"WARNING: Skipping row: {e}")

    print(f"Processing {len(locations)} locations...")

    results = []
    for i, loc in enumerate(locations):
        print(f"\n[{i+1}/{len(locations)}] {loc['name']}: ({loc['lat']:.4f}, {loc['lon']:.4f})")

        try:
            raw_data = fetch_nasa_power(loc["lat"], loc["lon"], year)
            parsed = parse_nasa_power_data(raw_data)

            daily_ghi = parsed.get("ALLSKY_SFC_SW_DWN", np.array([]))
            annual_ghi = compute_annual_ghi(daily_ghi)
            optimal_tilt = compute_optimal_tilt(loc["lat"])
            annual_output = compute_pv_output(annual_ghi, pr)
            capacity_factor = compute_capacity_factor(annual_output)

            result = {
                "name": loc["name"],
                "lat": loc["lat"],
                "lon": loc["lon"],
                "annual_ghi_kwh_m2": round(annual_ghi, 2),
                "optimal_tilt_degrees": round(optimal_tilt, 1),
                "annual_pv_output_kwh_per_kwp": round(annual_output, 2),
                "capacity_factor_percent": round(capacity_factor * 100, 2),
            }
            results.append(result)
            print(f"  GHI: {annual_ghi:.1f} kWh/m²/yr, Output: {annual_output:.1f} kWh/kWp")

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"name": loc["name"], "error": str(e)})

        # Rate limiting
        if i < len(locations) - 1:
            time.sleep(1.0)

    # Summary
    valid_results = [r for r in results if "error" not in r]
    if valid_results:
        avg_ghi = np.mean([r["annual_ghi_kwh_m2"] for r in valid_results])
        avg_output = np.mean([r["annual_pv_output_kwh_per_kwp"] for r in valid_results])
        print(f"\nSummary:")
        print(f"  Locations processed: {len(valid_results)}/{len(locations)}")
        print(f"  Average GHI: {avg_ghi:.1f} kWh/m²/year")
        print(f"  Average output: {avg_output:.1f} kWh/kWp")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved: {args.output}")

    if args.json:
        print(json.dumps(results, indent=2))


def cmd_economic(args):
    """Handle economic subcommand."""
    lat, lon = validate_latlon(args.lat, args.lon)
    year = validate_year(args.year)
    efficiency = validate_efficiency(args.efficiency)
    pr = validate_performance_ratio(args.performance_ratio)

    print(f"Solar Economic Analysis")
    print(f"  Location: ({lat:.4f}, {lon:.4f})")
    print(f"  Year: {year}")
    print(f"  Capacity: {args.capacity} kWp")
    print(f"  Cost: ${args.cost_per_kwp}/kWp")
    print(f"  Electricity price: ${args.electricity_price}/kWh")

    # Fetch data
    print(f"\nFetching NASA POWER data...")
    raw_data = fetch_nasa_power(lat, lon, year)
    parsed = parse_nasa_power_data(raw_data)

    daily_ghi = parsed.get("ALLSKY_SFC_SW_DWN", np.array([]))
    annual_ghi = compute_annual_ghi(daily_ghi)
    annual_output = compute_pv_output(annual_ghi, pr)
    capacity_factor = compute_capacity_factor(annual_output)

    # Economics
    econ = compute_economics(annual_output, args.capacity, args.cost_per_kwp, args.electricity_price)

    result = {
        "location": {"lat": lat, "lon": lon},
        "year": year,
        "annual_ghi_kwh_m2": round(annual_ghi, 2),
        "annual_pv_output_kwh_per_kwp": round(annual_output, 2),
        "capacity_factor_percent": round(capacity_factor * 100, 2),
        "system_capacity_kwp": args.capacity,
        "economics": econ,
    }

    print(f"\nResults:")
    print(f"  Annual GHI: {annual_ghi:.1f} kWh/m²/year")
    print(f"  Annual PV output: {annual_output:.1f} kWh/kWp")
    print(f"  Total system cost: ${econ['total_system_cost_usd']:,.2f}")
    print(f"  Annual energy: {econ['annual_energy_kwh']:,.1f} kWh")
    print(f"  Annual savings: ${econ['annual_savings_usd']:,.2f}")
    print(f"  Simple payback: {econ['simple_payback_years']:.1f} years")
    print(f"  LCOE: ${econ['lcoe_usd_per_kwh']:.4f}/kWh")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved: {args.output}")

    if args.json:
        print(json.dumps(result, indent=2))


# ─── CLI Setup ───────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solar-energy-potential",
        description="Calculate solar PV energy potential from NASA POWER data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Privacy: Lat/lon coordinates are sent to NASA POWER API. No personal data is transmitted.

Examples:
  %(prog)s assess --lat 39.9 --lon 116.4 -o solar.json
  %(prog)s batch -i locations.csv --lat-col lat --lon-col lon -o batch.json
  %(prog)s economic --lat 39.9 --lon 116.4 --capacity 5.0 --cost-per-kwp 800
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── assess ──
    p_assess = subparsers.add_parser("assess", help="Assess solar potential for a location")
    p_assess.add_argument("--lat", type=float, required=True, help="Latitude (-90 to 90)")
    p_assess.add_argument("--lon", type=float, required=True, help="Longitude (-180 to 180)")
    p_assess.add_argument("-o", "--output", help="Output JSON file")
    p_assess.add_argument("--year", type=int, default=DEFAULT_YEAR, help="Year (1984-2024)")
    p_assess.add_argument("--efficiency", type=float, default=DEFAULT_EFFICIENCY,
                          help="PV panel efficiency (0.05-0.50)")
    p_assess.add_argument("--performance-ratio", type=float, default=DEFAULT_PERFORMANCE_RATIO,
                          help="Performance ratio (0.50-0.95)")
    p_assess.add_argument("--json", action="store_true", help="Output as JSON")
    p_assess.set_defaults(func=cmd_assess)

    # ── batch ──
    p_batch = subparsers.add_parser("batch", help="Batch process locations from CSV")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV file")
    p_batch.add_argument("--lat-col", default="lat", help="Latitude column name")
    p_batch.add_argument("--lon-col", default="lon", help="Longitude column name")
    p_batch.add_argument("-o", "--output", help="Output JSON file")
    p_batch.add_argument("--year", type=int, default=DEFAULT_YEAR, help="Year (1984-2024)")
    p_batch.add_argument("--efficiency", type=float, default=DEFAULT_EFFICIENCY,
                         help="PV panel efficiency")
    p_batch.add_argument("--performance-ratio", type=float, default=DEFAULT_PERFORMANCE_RATIO,
                         help="Performance ratio")
    p_batch.add_argument("--json", action="store_true", help="Output as JSON")
    p_batch.set_defaults(func=cmd_batch)

    # ── economic ──
    p_econ = subparsers.add_parser("economic", help="Economic analysis for a location")
    p_econ.add_argument("--lat", type=float, required=True, help="Latitude")
    p_econ.add_argument("--lon", type=float, required=True, help="Longitude")
    p_econ.add_argument("-o", "--output", help="Output JSON file")
    p_econ.add_argument("--year", type=int, default=DEFAULT_YEAR, help="Year")
    p_econ.add_argument("--capacity", type=float, default=DEFAULT_CAPACITY_KWP,
                        help="Installed capacity in kWp")
    p_econ.add_argument("--cost-per-kwp", type=float, default=DEFAULT_COST_PER_KWP,
                        help="System cost per kWp (USD)")
    p_econ.add_argument("--electricity-price", type=float, default=DEFAULT_ELECTRICITY_PRICE,
                        help="Electricity price (USD/kWh)")
    p_econ.add_argument("--efficiency", type=float, default=DEFAULT_EFFICIENCY,
                        help="PV panel efficiency")
    p_econ.add_argument("--performance-ratio", type=float, default=DEFAULT_PERFORMANCE_RATIO,
                        help="Performance ratio")
    p_econ.add_argument("--json", action="store_true", help="Output as JSON")
    p_econ.set_defaults(func=cmd_economic)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
