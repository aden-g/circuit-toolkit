"""Tests for the circuit math. Run with:  python3 -m unittest discover tests"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from circuit_toolkit import calc


class TestResistorColors(unittest.TestCase):
    def test_four_band(self):
        r = calc.resistor_from_colors(["brown", "black", "red", "gold"])
        self.assertEqual(r["ohms"], 1000)
        self.assertEqual(r["tolerance_percent"], 5)

    def test_five_band(self):
        r = calc.resistor_from_colors(["yellow", "violet", "black", "red", "brown"])
        self.assertEqual(r["ohms"], 47000)
        self.assertEqual(r["tolerance_percent"], 1)

    def test_gold_multiplier(self):
        r = calc.resistor_from_colors(["brown", "black", "gold", "gold"])
        self.assertAlmostEqual(r["ohms"], 1.0)

    def test_bad_color(self):
        with self.assertRaises(ValueError):
            calc.resistor_from_colors(["pink", "black", "red", "gold"])

    def test_wrong_band_count(self):
        with self.assertRaises(ValueError):
            calc.resistor_from_colors(["brown", "black", "red"])


class TestVoltageDivider(unittest.TestCase):
    def test_equal_resistors_halve_voltage(self):
        self.assertAlmostEqual(calc.voltage_divider(10, 1000, 1000)["vout"], 5)

    def test_unequal(self):
        self.assertAlmostEqual(calc.voltage_divider(9, 1000, 2000)["vout"], 6)

    def test_zero_resistance_rejected(self):
        with self.assertRaises(ValueError):
            calc.voltage_divider(5, 0, 0)


class TestRCFilter(unittest.TestCase):
    def test_cutoff(self):
        # 1 kΩ and 1 µF -> about 159.15 Hz
        self.assertAlmostEqual(calc.rc_filter(1000, 1e-6)["cutoff_hz"], 159.1549, places=3)

    def test_gain_at_cutoff_is_minus_3db(self):
        curve = calc.rc_filter(1000, 1e-6, points=61)["curve"]
        middle = curve[30]  # log-centered on the cutoff
        self.assertAlmostEqual(middle["gain_db"], -3.0103, places=2)

    def test_highpass_blocks_low_frequencies(self):
        curve = calc.rc_filter(1000, 1e-6, "highpass")["curve"]
        self.assertLess(curve[0]["gain_db"], -35)
        self.assertGreater(curve[-1]["gain_db"], -0.1)

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            calc.rc_filter(0, 1e-6)


class TestLedResistor(unittest.TestCase):
    def test_exact_value(self):
        r = calc.led_resistor(5, 2, 20)
        self.assertAlmostEqual(r["exact_ohms"], 150)

    def test_rounds_up_to_standard_value(self):
        # (5 - 2) / 0.02 = 150 ohms exactly; 150 is an E24 value
        self.assertEqual(calc.led_resistor(5, 2, 20)["standard_ohms"], 150)
        # (3.3 - 2) / 0.02 = 65 ohms -> next standard value is 68
        self.assertEqual(calc.led_resistor(3.3, 2, 20)["standard_ohms"], 68)

    def test_current_never_exceeds_target(self):
        r = calc.led_resistor(3.3, 2, 20)
        self.assertLessEqual(r["actual_current_ma"], 20.0001)

    def test_supply_too_low(self):
        with self.assertRaises(ValueError):
            calc.led_resistor(1.5, 2, 20)


class TestOhmsLaw(unittest.TestCase):
    def test_find_current(self):
        r = calc.ohms_law(voltage=12, resistance=6)
        self.assertAlmostEqual(r["current_a"], 2)
        self.assertAlmostEqual(r["power_w"], 24)

    def test_find_voltage(self):
        self.assertAlmostEqual(calc.ohms_law(current=0.5, resistance=100)["voltage_v"], 50)

    def test_needs_exactly_two(self):
        with self.assertRaises(ValueError):
            calc.ohms_law(voltage=5)


if __name__ == "__main__":
    unittest.main()
