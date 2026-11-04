"""Web endpoint for the circuit toolkit.

Vercel runs this file as a "serverless function": it wakes up when a request
arrives at /api/calculate, runs, and goes back to sleep. It has no job except
to take JSON in, call the right function from calc.py, and send JSON back.

Request:  POST /api/calculate
          {"tool": "voltage_divider", "inputs": {"vin": 5, "r1": 1000, "r2": 2000}}
Response: {"ok": true, "result": {...}}  or  {"ok": false, "error": "..."}
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Make the circuit_toolkit folder importable when running on Vercel.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from circuit_toolkit import calc  # noqa: E402


def run_tool(tool, inputs):
    """Look up the tool by name and call it. Raises ValueError on bad input."""
    if tool == "voltage_divider":
        return calc.voltage_divider(float(inputs["vin"]), float(inputs["r1"]), float(inputs["r2"]))
    if tool == "rc_filter":
        return calc.rc_filter(float(inputs["r"]), float(inputs["c"]), inputs.get("kind", "lowpass"))
    if tool == "resistor_colors":
        return calc.resistor_from_colors(inputs["bands"])
    if tool == "led_resistor":
        return calc.led_resistor(float(inputs["vsupply"]), float(inputs["vforward"]), float(inputs["current_ma"]))
    if tool == "ohms_law":
        def maybe(key):
            value = inputs.get(key)
            return None if value in (None, "") else float(value)
        return calc.ohms_law(maybe("voltage"), maybe("current"), maybe("resistance"))
    raise ValueError(f"Unknown tool: {tool}")


class handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, {"ok": True, "tools": [
            "voltage_divider", "rc_filter", "resistor_colors", "led_resistor", "ohms_law",
        ]})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            result = run_tool(data.get("tool"), data.get("inputs", {}))
            self._send(200, {"ok": True, "result": result})
        except (ValueError, KeyError, TypeError) as err:
            # KeyError means a required input was missing
            message = f"Missing input: {err}" if isinstance(err, KeyError) else str(err)
            self._send(400, {"ok": False, "error": message})
        except Exception:
            self._send(500, {"ok": False, "error": "Something went wrong on the server."})
