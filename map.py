# ============================================================
#   SkyRoute AI-Based Smart Drone Delivery Optimization System
#   Module: map.py
#   Purpose: Builds the 2D city grid and draws it on screen.
# ============================================================

import pygame
import random
from constants import *


class CityMap:

    def __init__(self):
        self.grid = [[CELL_ROAD] * GRID_COLS for _ in range(GRID_ROWS)]
        self.charging_stations = []
        self.pickup_points     = []
        self.dropoff_points    = []
        self._build_city()

    def _build_city(self):
        building_rects = [
            (1,1,4,4),   (6,1,9,4),   (11,1,14,4),
            (16,1,19,4), (21,1,24,4), (26,1,29,4),
            (1,6,5,9),   (7,6,11,9),  (13,6,17,9),
            (19,6,23,9), (25,6,29,9),
            (1,12,4,15), (6,12,10,15),(12,12,16,15),
            (18,12,22,15),(24,12,28,15),
            (1,17,5,20), (7,17,11,20),(13,17,17,20),
            (19,17,23,20),(25,17,29,20),
        ]
        for (c1, r1, c2, r2) in building_rects:
            for r in range(r1, r2+1):
                for c in range(c1, c2+1):
                    if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                        self.grid[r][c] = CELL_BUILDING

        nofly_zones = [
            (20,10,23,13),
            (3,16,5,19),
        ]
        for (c1, r1, c2, r2) in nofly_zones:
            for r in range(r1, r2+1):
                for c in range(c1, c2+1):
                    if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                        self.grid[r][c] = CELL_NOFLY

        for (c, r) in [(5,5),(15,5),(25,10),(10,16),(20,16)]:
            if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                self.grid[r][c] = CELL_CHARGING
                self.charging_stations.append((c, r))

        for (c, r) in [(5,10),(15,10),(10,5),(25,5),(5,20)]:
            if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                self.grid[r][c] = CELL_PICKUP
                self.pickup_points.append((c, r))

        for (c, r) in [(10,20),(20,20),(25,15),(15,20),(28,10)]:
            if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                self.grid[r][c] = CELL_DROPOFF
                self.dropoff_points.append((c, r))

        self._place_weather(CELL_RAIN,  8)
        self._place_weather(CELL_WIND,  6)
        self._place_weather(CELL_FOG,   5)
        self._place_weather(CELL_STORM, 3)

    def _place_weather(self, weather_type, count):
        placed, attempts = 0, 0
        while placed < count and attempts < 500:
            r = random.randint(0, GRID_ROWS - 1)
            c = random.randint(0, GRID_COLS - 1)
            if self.grid[r][c] == CELL_ROAD:
                self.grid[r][c] = weather_type
                placed += 1
            attempts += 1

    def refresh_weather(self):
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid[r][c] in (CELL_RAIN, CELL_WIND, CELL_STORM, CELL_FOG):
                    self.grid[r][c] = CELL_ROAD
        self._place_weather(CELL_RAIN,  random.randint(4, 10))
        self._place_weather(CELL_WIND,  random.randint(3, 8))
        self._place_weather(CELL_FOG,   random.randint(2, 7))
        self._place_weather(CELL_STORM, random.randint(1, 4))

    def get_cell(self, col, row):
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            return self.grid[row][col]
        return CELL_BUILDING

    def is_walkable(self, col, row):
        return self.get_cell(col, row) not in (CELL_BUILDING, CELL_NOFLY, CELL_STORM)

    def movement_cost(self, col, row):
        costs = {
            CELL_ROAD:     1.0,
            CELL_RAIN:     1.5,
            CELL_WIND:     1.8,
            CELL_FOG:      1.2,
            CELL_CHARGING: 1.0,
            CELL_PICKUP:   1.0,
            CELL_DROPOFF:  1.0,
        }
        return costs.get(self.get_cell(col, row), 1.0)

    def get_nearest_charging(self, col, row):
        best, best_dist = None, float('inf')
        for (sc, sr) in self.charging_stations:
            d = abs(sc - col) + abs(sr - row)
            if d < best_dist:
                best_dist = d
                best = (sc, sr)
        return best

    def get_random_pickup(self):
        return random.choice(self.pickup_points)

    def get_random_dropoff(self):
        return random.choice(self.dropoff_points)

    def draw(self, surface):
        cell_colors = {
            CELL_ROAD:         COLOR_ROAD,
            CELL_BUILDING:     COLOR_BUILDING,
            CELL_NOFLY:        COLOR_NOFLY,
            CELL_CHARGING:     COLOR_CHARGING,
            CELL_PICKUP:       COLOR_PICKUP,
            CELL_DROPOFF:      COLOR_DROPOFF,
            CELL_RAIN:         COLOR_WEATHER_RAIN,
            CELL_WIND:         COLOR_WEATHER_WIND,
            CELL_STORM:        COLOR_WEATHER_STORM,
            CELL_FOG:          COLOR_WEATHER_FOG,
        }
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                ct    = self.grid[r][c]
                color = cell_colors.get(ct, COLOR_ROAD)
                rect  = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, color, rect)
                if ct in (CELL_ROAD, CELL_RAIN, CELL_WIND, CELL_FOG):
                    lc = (
                        min(255, color[0] + 8),
                        min(255, color[1] + 8),
                        min(255, color[2] + 8),
                    )
                    pygame.draw.rect(surface, lc, rect, 1)
                self._draw_icon(surface, c, r, ct)

    def _draw_icon(self, surface, c, r, ct):
        cx = c * CELL_SIZE + CELL_SIZE // 2
        cy = r * CELL_SIZE + CELL_SIZE // 2
        sz = CELL_SIZE // 4

        if ct == CELL_CHARGING:
            pygame.draw.circle(surface, (0, 255, 180), (cx, cy), sz)

        elif ct == CELL_PICKUP:
            pts = [(cx, cy - sz), (cx + sz, cy), (cx, cy + sz), (cx - sz, cy)]
            pygame.draw.polygon(surface, (80, 160, 255), pts)

        elif ct == CELL_DROPOFF:
            pygame.draw.rect(surface, (255, 160, 60),
                             (cx - sz, cy - sz, sz * 2, sz * 2))

        elif ct == CELL_NOFLY:
            pygame.draw.line(surface, (255, 60, 60),
                             (cx - sz, cy - sz), (cx + sz, cy + sz), 2)
            pygame.draw.line(surface, (255, 60, 60),
                             (cx + sz, cy - sz), (cx - sz, cy + sz), 2)

        elif ct == CELL_STORM:
            pygame.draw.circle(surface, (180, 60, 255), (cx, cy), sz - 1)

        elif ct == CELL_RAIN:
            pygame.draw.circle(surface, (60, 120, 200), (cx - 4, cy), 2)
            pygame.draw.circle(surface, (60, 120, 200), (cx + 4, cy), 2)

        elif ct == CELL_BUILDING:
            pygame.draw.rect(surface, (55, 62, 90),
                             (c * CELL_SIZE + 3,
                              r * CELL_SIZE + 3,
                              CELL_SIZE - 6,
                              CELL_SIZE - 6))
