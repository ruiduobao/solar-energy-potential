"""Tests for the --qa sidecar summary (Phase 5 optimization)."""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Load the script module
HERE = Path(__file__).parent
SCRIPT_PATH = HERE.parent / "scripts" / "solar-energy-potential.py"
spec = importlib.util.spec_from_file_location("solar_energy_potential", SCRIPT_PATH)
sep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sep)


class TestWriteQASummary(unittest.TestCase):
    """Tests for the write_qa_summary helper."""

    def test_writes_json_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            qa_path = os.path.join(td, "run.qa.json")
            args = mock.Mock()
            args.lat = 39.9
            args.lon = 116.4
            args.place = None
            args.year = 2023
            args.efficiency = 0.18
            args.performance_ratio = 0.80
            args.capacity = 1.0
            args.cost_per_kwp = 1000.0
            args.electricity_price = 0.10
            args.input = None
            args.lat_col = "lat"
            args.lon_col = "lon"
            args.no_nominatim = False
            args.output = None
            args.json = False
            sep.write_qa_summary(
                qa_path,
                skill="solar-energy-potential",
                command="assess",
                args=args,
                payload={"annual_ghi_kwh_m2": 1500.0},
            )
            self.assertTrue(os.path.exists(qa_path))
            data = json.loads(Path(qa_path).read_text(encoding="utf-8"))
            self.assertEqual(data["skill"], "solar-energy-potential")
            self.assertEqual(data["command"], "assess")
            self.assertEqual(data["lat"], 39.9)
            self.assertEqual(data["lon"], 116.4)
            self.assertEqual(data["year"], 2023)
            self.assertEqual(data["annual_ghi_kwh_m2"], 1500.0)
            self.assertIn("timestamp", data)
            self.assertIn("version", data)

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            qa_path = os.path.join(td, "nested", "subdir", "run.qa.json")
            args = mock.Mock(spec=[])
            sep.write_qa_summary(
                qa_path,
                skill="solar-energy-potential",
                command="assess",
                args=args,
                payload={"x": 1},
            )
            self.assertTrue(os.path.exists(qa_path))


class TestParserQAFlag(unittest.TestCase):
    """The CLI parsers should accept --qa on each subcommand."""

    def setUp(self):
        self.parser = sep.build_parser()

    def test_assess_accepts_qa(self):
        ns = self.parser.parse_args(
            ["assess", "--lat", "39.9", "--lon", "116.4", "--qa", "out.qa.json"]
        )
        self.assertEqual(ns.qa, "out.qa.json")
        self.assertEqual(ns.lat, 39.9)
        self.assertEqual(ns.command, "assess")

    def test_batch_accepts_qa(self):
        ns = self.parser.parse_args(
            ["batch", "-i", "input.csv", "--qa", "batch.qa.json"]
        )
        self.assertEqual(ns.qa, "batch.qa.json")
        self.assertEqual(ns.input, "input.csv")
        self.assertEqual(ns.command, "batch")

    def test_economic_accepts_qa(self):
        ns = self.parser.parse_args(
            ["economic", "--lat", "39.9", "--lon", "116.4", "--qa", "econ.qa.json"]
        )
        self.assertEqual(ns.qa, "econ.qa.json")
        self.assertEqual(ns.command, "economic")


class TestCmdAssessQA(unittest.TestCase):
    """End-to-end: cmd_assess with --qa should write a sidecar (no network)."""

    def test_writes_sidecar_with_qa(self):
        with tempfile.TemporaryDirectory() as td:
            qa_path = os.path.join(td, "out.qa.json")
            args = mock.Mock()
            args.lat = 39.9
            args.lon = 116.4
            args.place = None
            args.year = 2023
            args.efficiency = 0.18
            args.performance_ratio = 0.80
            args.output = None
            args.qa = qa_path
            args.json = False
            # Mock the network call to return 365 days of GHI
            fake_daily = [3.5] * 365
            fake_raw = {
                "properties": {
                    "parameter": {
                        "ALLSKY_SFC_SW_DWN": {f"2023{i:04d}": v for i, v in enumerate(fake_daily)},
                        "DIFF": {f"2023{i:04d}": 1.0 for i in range(365)},
                    }
                }
            }
            with mock.patch.object(sep, "fetch_nasa_power", return_value=fake_raw):
                sep.cmd_assess(args)
            self.assertTrue(os.path.exists(qa_path))
            data = json.loads(Path(qa_path).read_text(encoding="utf-8"))
            self.assertEqual(data["command"], "assess")
            self.assertEqual(data["lat"], 39.9)
            self.assertEqual(data["lon"], 116.4)
            self.assertIn("annual_ghi_kwh_m2", data)


if __name__ == "__main__":
    unittest.main()
