"""Circuit calculator functions.

Every function here is plain Python: numbers in, numbers out. No web code.
That keeps the math easy to test on its own, and the web layer (api/calculate.py)
just calls these functions.
"""

import math

# ---------------------------------------------------------------------------
# Resistor color code
# ---------------------------------------------------------------------------

DIGITS = {
    "black": 0, "brown": 1, "red": 2, "orange": 3, "yellow": 4,
    "green": 5, "blue": 6, "violet": 7, "grey": 8, "white": 9,
}

# Multiplier band: value is 10 ** exponent
MULTIPLIERS = {**DIGITS, "gold": -1, "silver": -2}

# Tolerance band, in percent
TOLERANCES = {
    "brown": 1, "red": 2, "green": 0.5, "blue": 0.25,
    "violet": 0.1, "grey": 0.05, "gold": 5, "silver": 10,
}


def resistor_from_colors(bands):
    """Decode a 4-band or 5-band resistor.

    bands: list of color names, e.g. ["brown", "black", "red", "gold"]
    Returns the resistance in ohms and the tolerance in percent.
    """
    bands = [b.strip().lower() for b in bands]
    if len(bands) not in (4, 5):
        raise ValueError("Use 4 bands or 5 bands.")

    digit_bands = bands[:-2]   # all bands before multiplier + tolerance
    multiplier_band = bands[-2]
    tolerance_band = bands[-1]

    value = 0
    for color in digit_bands:
        if color not in DIGITS:
            raise ValueError(f"'{color}' can't be a digit band.")
        value = value * 10 + DIGITS[color]

    if multiplier_band not in MULTIPLIERS:
        raise ValueError(f"'{multiplier_band}' can't be a multiplier band.")
    if tolerance_band not in TOLERANCES:
        raise ValueError(f"'{tolerance_band}' can't be a tolerance band.")

    ohms = value * (10 ** MULTIPLIERS[multiplier_band])
    tol = TOLERANCES[tolerance_band]
    return {
        "ohms": ohms,
        "tolerance_percent": tol,
        "min_ohms": ohms * (1 - tol / 100),
        "max_ohms": ohms * (1 + tol / 100),
        "label": format_ohms(ohms),
    }


def format_ohms(ohms):
    """1500 -> '1.5 kΩ'."""
    if ohms >= 1e6:
        return f"{ohms / 1e6:g} MΩ"
    if ohms >= 1e3:
        return f"{ohms / 1e3:g} kΩ"
    return f"{ohms:g} Ω"


# ---------------------------------------------------------------------------
# Voltage divider
# ---------------------------------------------------------------------------

def voltage_divider(vin, r1, r2):
    """Two resistors in series, output taken across R2.

    vout = vin * r2 / (r1 + r2)
    """
    if r1 < 0 or r2 < 0 or (r1 + r2) == 0:
        raise ValueError("Resistors must be positive.")
    vout = vin * r2 / (r1 + r2)
    current = vin / (r1 + r2)
    return {
        "vout": vout,
        "current_a": current,
        "power_r1_w": current ** 2 * r1,
        "power_r2_w": current ** 2 * r2,
    }


# ---------------------------------------------------------------------------
# RC filters
# ---------------------------------------------------------------------------

def rc_filter(r, c, kind="lowpass", points=60):
    """First-order RC filter.

    r in ohms, c in farads. kind is 'lowpass' or 'highpass'.
    Returns the cutoff frequency, time constant, and a frequency-response
    curve (gain in dB) from a decade below the cutoff to a decade above.
    """
    if r <= 0 or c <= 0:
        raise ValueError("R and C must be greater than zero.")
    if kind not in ("lowpass", "highpass"):
        raise ValueError("kind must be 'lowpass' or 'highpass'.")

    tau = r * c
    fc = 1 / (2 * math.pi * tau)

    f_start = fc / 100
    f_end = fc * 100
    curve = []
    for i in range(points):
        # Log-spaced frequencies
        f = f_start * (f_end / f_start) ** (i / (points - 1))
        ratio = f / fc
        if kind == "lowpass":
            gain = 1 / math.sqrt(1 + ratio ** 2)
            phase = -math.degrees(math.atan(ratio))
        else:
            gain = ratio / math.sqrt(1 + ratio ** 2)
            phase = 90 - math.degrees(math.atan(ratio))
        curve.append({
            "freq_hz": f,
            "gain_db": 20 * math.log10(gain),
            "phase_deg": phase,
        })

    return {
        "cutoff_hz": fc,
        "tau_s": tau,
        "kind": kind,
        "curve": curve,
    }


# ---------------------------------------------------------------------------
# LED current-limiting resistor
# ---------------------------------------------------------------------------

# Standard E24 resistor values (one decade). Real parts come in these sizes.
E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
       3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]


def next_standard_resistor(ohms):
    """Smallest E24 value that is >= ohms (rounding up is the safe direction)."""
    if ohms <= 0:
        raise ValueError("Resistance must be positive.")
    decade = 10 ** math.floor(math.log10(ohms))
    for base in E24 + [10.0]:
        candidate = round(base * decade, 6)
        if candidate >= ohms - 1e-9:
            return candidate
    return 10 * decade


def led_resistor(vsupply, vforward, current_ma):
    """Resistor to limit LED current: R = (Vs - Vf) / I."""
    if current_ma <= 0:
        raise ValueError("Current must be greater than zero.")
    if vsupply <= vforward:
        raise ValueError("Supply voltage must be higher than the LED's forward voltage.")
    current = current_ma / 1000
    exact = (vsupply - vforward) / current
    standard = next_standard_resistor(exact)
    actual_current = (vsupply - vforward) / standard
    return {
        "exact_ohms": exact,
        "standard_ohms": standard,
        "standard_label": format_ohms(standard),
        "actual_current_ma": actual_current * 1000,
        "resistor_power_w": actual_current ** 2 * standard,
    }


# ---------------------------------------------------------------------------
# Ohm's law and power
# ---------------------------------------------------------------------------

def ohms_law(voltage=None, current=None, resistance=None):
    """Give any two of voltage, current, resistance. Returns all three plus power."""
    given = [x is not None for x in (voltage, current, resistance)]
    if sum(given) != 2:
        raise ValueError("Enter exactly two of: voltage, current, resistance.")

    if voltage is None:
        voltage = current * resistance
    elif current is None:
        if resistance == 0:
            raise ValueError("Resistance can't be zero here.")
        current = voltage / resistance
    else:
        if current == 0:
            raise ValueError("Current can't be zero here.")
        resistance = voltage / current

    return {
        "voltage_v": voltage,
        "current_a": current,
        "resistance_ohm": resistance,
        "power_w": voltage * current,
    }
