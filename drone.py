# ============================================================
#   SkyRoute AI-Based Smart Drone Delivery Optimization System
#   Module: drone.py
#   Purpose: Drone intelligent agent — 2 drones only.
#            Movement, battery, charging, delivery state machine.
# ============================================================

import pygame
import math
from constants import *
from pathfinding import a_star, estimate_battery_cost


class Drone:

    def __init__(self, drone_id, start_pos, color, city_map, weather):
        self.id           = drone_id
        self.color        = color
        self.city_map     = city_map
        self.weather      = weather

        # Grid position (integer cell)
        self.grid_col     = start_pos[0]
        self.grid_row     = start_pos[1]

        # Pixel position (float, for smooth animation)
        self.pixel_x      = float(start_pos[0] * CELL_SIZE + CELL_SIZE // 2)
        self.pixel_y      = float(start_pos[1] * CELL_SIZE + CELL_SIZE // 2)

        # Battery
        self.battery      = BATTERY_FULL

        # Cargo
        self.current_load = 0.0
        self.max_weight   = DRONE_MAX_WEIGHT

        # State: IDLE / HEADING_PICKUP / HEADING_DROPOFF / CHARGING
        self.state        = "IDLE"

        # Delivery assigned to this drone
        self.current_delivery = None
        self._saved_delivery  = None    # saved while charging

        # Path (list of (col,row) waypoints from A*)
        self.path         = []
        self.path_index   = 0

        # Speed in pixels per second
        self.speed        = DRONE_SPEED_NORMAL * CELL_SIZE

        # Status message shown in sidebar
        self.status_msg   = "IDLE"
        self.eco_mode     = False

        # Stats
        self.deliveries_done = 0

        # Animation helpers
        self.anim_angle   = 0.0
        self.blink_timer  = 0.0

        print(f"{ANSI_OK}[DRONE] Drone #{self.id} ready at {start_pos} "
              f"| Battery: {self.battery:.0f}%{ANSI_RESET}")

    # ----------------------------------------------------------
    def assign_delivery(self, delivery, eco_mode=False):
        """Give this drone a delivery to complete."""
        self.current_delivery = delivery
        self.eco_mode         = eco_mode
        delivery.drone_id     = self.id
        delivery.status       = "IN_PROGRESS"

        if delivery.is_emergency:
            self.status_msg = "EMERGENCY DELIVERY"
            print(f"{ANSI_ERR}[DRONE] #{self.id} EMERGENCY MODE!{ANSI_RESET}")
        elif eco_mode:
            self.status_msg = "ECO MODE ACTIVE"
        else:
            self.status_msg = f"PICKING UP {delivery.delivery_type.upper()}"

        self._plan_to(delivery.pickup)
        self.state = "HEADING_PICKUP"

    def go_charge(self):
        """Navigate to nearest charging station."""
        pos     = (self.grid_col, self.grid_row)
        charger = self.city_map.get_nearest_charging(pos[0], pos[1])
        if not charger:
            return
        print(f"{ANSI_WARN}[DRONE] #{self.id} LOW BATTERY "
              f"({self.battery:.0f}%) → charging at {charger}{ANSI_RESET}")
        self._plan_to(charger)
        self.state      = "CHARGING"
        self.status_msg = "LOW BATTERY → CHARGING"

    def _plan_to(self, goal):
        """Run A* from current grid pos to goal."""
        start = (self.grid_col, self.grid_row)
        path, _ = a_star(self.city_map, start, goal)
        self.path       = path
        self.path_index = 0

    # ----------------------------------------------------------
    def update(self, dt):
        """Called every frame. Moves drone, drains battery, handles states."""
        self.anim_angle  = (self.anim_angle + 180 * dt) % 360
        self.blink_timer += dt

        # Charging while stationary
        if self.state == "CHARGING" and not self.path:
            self._do_charge(dt)
            return

        # Move along path
        if self.path and self.path_index < len(self.path):
            self._move(dt)
        else:
            self._on_arrival()

    def _move(self, dt):
        """Smoothly move towards the next waypoint."""
        if self.path_index >= len(self.path):
            return
        target = self.path[self.path_index]
        tx = target[0] * CELL_SIZE + CELL_SIZE // 2
        ty = target[1] * CELL_SIZE + CELL_SIZE // 2

        # Slow down in wind cells
        spd = self.speed
        if self.city_map.get_cell(target[0], target[1]) == CELL_WIND:
            spd = DRONE_SPEED_WIND * CELL_SIZE

        dx   = tx - self.pixel_x
        dy   = ty - self.pixel_y
        dist = math.sqrt(dx * dx + dy * dy)
        move = spd * dt

        if dist <= move or dist < 1.0:
            # Snap to waypoint
            self.pixel_x  = float(tx)
            self.pixel_y  = float(ty)
            self.grid_col = target[0]
            self.grid_row = target[1]
            self._drain(target[0], target[1])
            self.path_index += 1

            # Battery warnings
            if self.battery <= BATTERY_LOW_WARNING and self.state != "CHARGING":
                print(f"{ANSI_WARN}[WARN] Drone #{self.id} battery LOW: "
                      f"{self.battery:.0f}%{ANSI_RESET}")
            if self.battery <= BATTERY_SAFE_THRESHOLD and self.state != "CHARGING":
                print(f"{ANSI_ERR}[CRIT] Drone #{self.id} CRITICAL BATTERY! "
                      f"Rerouting to charger.{ANSI_RESET}")
                self._saved_delivery = self.current_delivery
                self.go_charge()
        else:
            self.pixel_x += (dx / dist) * move
            self.pixel_y += (dy / dist) * move

    def _drain(self, col, row):
        """Drain battery for one cell of movement."""
        drain  = BATTERY_DRAIN_PER_CELL
        drain += self.current_load * BATTERY_WEIGHT_PENALTY
        drain += self.weather.battery_modifier(col, row)
        self.battery = max(0.0, self.battery - drain)

    def _do_charge(self, dt):
        """Charge battery gradually at station."""
        if self.battery < BATTERY_FULL:
            self.battery    = min(BATTERY_FULL,
                                  self.battery + BATTERY_CHARGE_RATE * dt)
            self.status_msg = f"CHARGING... {self.battery:.0f}%"
        else:
            self.battery = BATTERY_FULL
            print(f"{ANSI_OK}[DRONE] #{self.id} Fully charged! Resuming.{ANSI_RESET}")
            saved = self._saved_delivery
            if saved and saved.status == "IN_PROGRESS":
                self.assign_delivery(saved)
                self._saved_delivery = None
            else:
                self.state            = "IDLE"
                self.status_msg       = "IDLE"
                self.current_delivery = None

    def _on_arrival(self):
        """Handle state transitions when drone reaches its destination."""
        if self.state == "HEADING_PICKUP" and self.current_delivery:
            d = self.current_delivery
            self.current_load = d.weight
            print(f"{ANSI_OK}[DRONE] #{self.id} Picked up at {d.pickup} "
                  f"| Load: {self.current_load:.1f}kg{ANSI_RESET}")
            self._plan_to(d.dropoff)
            self.state      = "HEADING_DROPOFF"
            self.status_msg = f"DELIVERING {d.delivery_type.upper()}"

        elif self.state == "HEADING_DROPOFF" and self.current_delivery:
            d = self.current_delivery
            d.status = "DONE"
            self.deliveries_done += 1
            self.current_load    = 0.0
            print(f"{ANSI_OK}[DRONE] #{self.id} ✓ DELIVERED "
                  f"#{d.id} {d.delivery_type}{ANSI_RESET}")
            self.current_delivery = None
            self.eco_mode         = False
            self.state            = "IDLE"
            self.status_msg       = "IDLE"
            self.path             = []

        elif self.state == "CHARGING":
            self.path = []   # arrived — now charge in place

        else:
            self.path = []

    # ----------------------------------------------------------
    def draw(self, surface):
        """Draw drone with rotors, glow, route line."""
        x, y = int(self.pixel_x), int(self.pixel_y)

        # Body color depends on battery level
        if self.battery > 60:
            body = self.color
        elif self.battery > 30:
            body = COLOR_YELLOW
        else:
            body = COLOR_RED

        # Soft glow behind drone
        glow  = pygame.Surface((40, 40), pygame.SRCALPHA)
        alpha = 60 + int(30 * math.sin(self.blink_timer * 4))
        pygame.draw.circle(glow, (*body, alpha), (20, 20), 18)
        surface.blit(glow, (x - 20, y - 20))

        # Body circle
        pygame.draw.circle(surface, (20, 24, 40), (x, y), 9)
        pygame.draw.circle(surface, body,         (x, y), 7)

        # Spinning rotors (4 arms)
        for offset in [0, 90, 180, 270]:
            rad = math.radians(self.anim_angle + offset)
            ex  = x + int(8 * math.cos(rad))
            ey  = y + int(8 * math.sin(rad))
            pygame.draw.line(surface, (160, 180, 220), (x, y), (ex, ey), 1)
            pygame.draw.circle(surface, (200, 220, 255), (ex, ey), 2)

        # Green ring when ECO mode
        if self.eco_mode:
            pygame.draw.circle(surface, COLOR_GREEN, (x, y), 11, 2)

        # Pulsing red ring when emergency
        if self.current_delivery and self.current_delivery.is_emergency:
            r = 4 + int(2 * math.sin(self.blink_timer * 10))
            pygame.draw.circle(surface, COLOR_RED, (x, y), 13 + r, 2)

        # Draw the planned route as a faint line
        if len(self.path) > self.path_index + 1:
            pts = [
                (p[0] * CELL_SIZE + CELL_SIZE // 2,
                 p[1] * CELL_SIZE + CELL_SIZE // 2)
                for p in self.path[self.path_index:]
            ]
            if len(pts) >= 2:
                lc = COLOR_GREEN if self.eco_mode else body
                pygame.draw.lines(surface, (*lc, 120), False, pts, 1)

        # Drone label
        # (drawn in main.py sidebar instead to keep map clean)

    def get_status(self):
        """Return status dict for sidebar UI."""
        return {
            "id":      self.id,
            "state":   self.state,
            "battery": self.battery,
            "load":    self.current_load,
            "msg":     self.status_msg,
            "eco":     self.eco_mode,
            "done":    self.deliveries_done,
            "color":   self.color,
        }
