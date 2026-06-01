# ============================================================
#   SkyRoute AI-Based Smart Drone Delivery Optimization System
#   Module: weather.py
#   Purpose: Probabilistic weather system. Rain/wind/storm/fog
#            probabilities shift over time and affect routing.
# ============================================================

import random
from constants import *


class WeatherSystem:

    def __init__(self, city_map):
        self.city_map   = city_map
        self.tick       = 0
        self.rain_prob  = random.uniform(0.1, 0.4)
        self.storm_prob = random.uniform(0.05, 0.2)
        self.wind_prob  = random.uniform(0.1, 0.35)
        self.fog_prob   = random.uniform(0.05, 0.25)
        self.summary    = ""
        self._update_summary()

    def update(self):
        self.tick += 1
        if self.tick % WEATHER_CHANGE_INTERVAL == 0:
            self._shift()
            self.city_map.refresh_weather()
            self._update_summary()
            print(f"{ANSI_PURPLE}[WEATHER] Conditions shifted → {self.summary}{ANSI_RESET}")

    def _shift(self):
        def clamp(v):
            return max(0.0, min(1.0, v))
        self.rain_prob  = clamp(self.rain_prob  + random.uniform(-0.1,  0.15))
        self.storm_prob = clamp(self.storm_prob + random.uniform(-0.05, 0.10))
        self.wind_prob  = clamp(self.wind_prob  + random.uniform(-0.1,  0.10))
        self.fog_prob   = clamp(self.fog_prob   + random.uniform(-0.08, 0.10))

    def _update_summary(self):
        parts = []
        if self.rain_prob  > 0.3: parts.append("RAIN")
        if self.storm_prob > 0.2: parts.append("STORM")
        if self.wind_prob  > 0.3: parts.append("WIND")
        if self.fog_prob   > 0.2: parts.append("FOG")
        self.summary = ", ".join(parts) if parts else "CLEAR"

    def get_risk_score(self, path):
        if not path:
            return 0.0
        rain_c = 0
        storm_c = 0
        wind_c = 0
        fog_c = 0
        for (col, row) in path:
            ct = self.city_map.get_cell(col, row)
            if ct == CELL_RAIN:  rain_c  += 1
            if ct == CELL_STORM: storm_c += 1
            if ct == CELL_WIND:  wind_c  += 1
            if ct == CELL_FOG:   fog_c   += 1
        n = len(path)
        risk = (
            (rain_c  / n) * 0.30 * self.rain_prob  +
            (storm_c / n) * 1.00 * self.storm_prob +
            (wind_c  / n) * 0.50 * self.wind_prob  +
            (fog_c   / n) * 0.20 * self.fog_prob
        )
        global_risk = (
            self.rain_prob  * 0.05 +
            self.storm_prob * 0.15 +
            self.wind_prob  * 0.05 +
            self.fog_prob   * 0.03
        )
        return round(min(1.0, risk + global_risk), 3)

    def risk_label(self, score):
        if score < 0.15: return "LOW"
        if score < 0.40: return "MODERATE"
        if score < 0.65: return "HIGH"
        return "SEVERE"

    def battery_modifier(self, col, row):
        ct = self.city_map.get_cell(col, row)
        if ct == CELL_RAIN: return BATTERY_RAIN_PENALTY
        if ct == CELL_WIND: return BATTERY_WIND_PENALTY
        if ct == CELL_FOG:  return BATTERY_FOG_PENALTY
        return 0.0

    def print_report(self):
        print(f"{ANSI_PURPLE}{'='*60}")
        print(f"  SkyRoute AI — Weather Report")
        print(f"  Rain  : {self.rain_prob:.0%}   |   Storm : {self.storm_prob:.0%}")
        print(f"  Wind  : {self.wind_prob:.0%}   |   Fog   : {self.fog_prob:.0%}")
        print(f"  Active Conditions : {self.summary}")
        print(f"{'='*60}{ANSI_RESET}")
