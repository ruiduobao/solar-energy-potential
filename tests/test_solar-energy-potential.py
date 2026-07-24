#!/usr/bin/env python3
"""Tests for solar-energy-potential."""

import sys
import os
import unittest
import json
import importlib.util

import numpy as np

# Load the script module
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "solar-energy-potential.py")
spec = importlib.util.spec_from_file_location("solar_energy_potential", SCRIPT_PATH)
sep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sep)


class TestValidation(unittest.TestCase):
    """Test input validation."""

    def test_validate_latlon_valid(self):
        result = sep.validate_latlon(39.9, 116.4)
        self.assertEqual(result, (39.9, 116.4))

    def test_validate_latlon_negative(self):
        result = sep.validate_latlon(-33.8, 151.2)
        self.assertEqual(result, (-33.8, 151.2))

    def test_validate_latlon_invalid_lat(self):
        with self.assertRaises(ValueError):
            sep.validate_latlon(91.0, 116.4)

    def test_validate_latlon_invalid_lon(self):
        with self.assertRaises(ValueError):
            sep.validate_latlon(39.9, 181.0)

    def test_validate_year_valid(self):
        self.assertEqual(sep.validate_year(2023), 2023)

    def test_validate_year_invalid(self):
        with self.assertRaises(ValueError):
            sep.validate_year(1970)

    def test_validate_efficiency_valid(self):
        self.assertEqual(sep.validate_efficiency(0.18), 0.18)

    def test_validate_efficiency_invalid(self):
        with self.assertRaises(ValueError):
            sep.validate_efficiency(0.60)

    def test_validate_performance_ratio_valid(self):
        self.assertEqual(sep.validate_performance_ratio(0.80), 0.80)

    def test_validate_performance_ratio_invalid(self):
        with self.assertRaises(ValueError):
            sep.validate_performance_ratio(0.30)


class TestSolarCalculations(unittest.TestCase):
    """Test solar calculation functions."""

    def test_annual_ghi(self):
        daily = np.array([4.0, 5.0, 6.0] * 100, dtype=np.float64)
        result = sep.compute_annual_ghi(daily)
        self.assertAlmostEqual(result, 1500.0, places=1)

    def test_annual_ghi_with_nan(self):
        daily = np.array([4.0, np.nan, 6.0], dtype=np.float64)
        result = sep.compute_annual_ghi(daily)
        self.assertAlmostEqual(result, 10.0, places=1)

    def test_annual_ghi_all_nan(self):
        daily = np.array([np.nan, np.nan], dtype=np.float64)
        result = sep.compute_annual_ghi(daily)
        self.assertEqual(result, 0.0)

    def test_optimal_tilt_equator(self):
        tilt = sep.compute_optimal_tilt(0.0)
        self.assertGreater(tilt, 0.0)
        self.assertLess(tilt, 10.0)

    def test_optimal_tilt_mid_lat(self):
        tilt = sep.compute_optimal_tilt(40.0)
        self.assertGreater(tilt, 30.0)
        self.assertLess(tilt, 40.0)

    def test_optimal_tilt_high_lat(self):
        tilt = sep.compute_optimal_tilt(60.0)
        self.assertLessEqual(tilt, 60.0)  # Capped at 60

    def test_pv_output(self):
        result = sep.compute_pv_output(1500.0, 0.80)
        self.assertAlmostEqual(result, 1200.0, places=1)

    def test_capacity_factor(self):
        # 1200 kWh/kWp / 8760 h = 0.137
        cf = sep.compute_capacity_factor(1200.0)
        self.assertAlmostEqual(cf, 0.137, places=2)


class TestEconomics(unittest.TestCase):
    """Test economic calculations."""

    def test_economics_basic(self):
        result = sep.compute_economics(
            annual_output=1200.0,
            capacity_kwp=5.0,
            cost_per_kwp=1000.0,
            electricity_price=0.10,
        )
        self.assertEqual(result["total_system_cost_usd"], 5000.0)
        self.assertEqual(result["annual_energy_kwh"], 6000.0)
        self.assertEqual(result["annual_savings_usd"], 600.0)
        self.assertAlmostEqual(result["simple_payback_years"], 8.33, places=1)

    def test_economics_zero_output(self):
        result = sep.compute_economics(
            annual_output=0.0,
            capacity_kwp=5.0,
            cost_per_kwp=1000.0,
            electricity_price=0.10,
        )
        self.assertEqual(result["simple_payback_years"], float("inf"))


class TestParseNasaPower(unittest.TestCase):
    """Test NASA POWER data parsing."""

    def test_parse_basic(self):
        raw = {
            "properties": {
                "parameter": {
                    "ALLSKY_SFC_SW_DWN": {
                        "20230101": 3.5, "20230102": 4.0, "20230103": -999
                    }
                }
            }
        }
        result = sep.parse_nasa_power_data(raw)
        self.assertIn("ALLSKY_SFC_SW_DWN", result)
        self.assertTrue(np.isnan(result["ALLSKY_SFC_SW_DWN"][-1]))  # -999 -> NaN


class TestCLI(unittest.TestCase):
    """Test CLI setup."""

    def test_parser_builds(self):
        parser = sep.build_parser()
        self.assertIsNotNone(parser)


if __name__ == "__main__":
    unittest.main()
