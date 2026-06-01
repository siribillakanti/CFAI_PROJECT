# ============================================================
#   SkyRoute AI-Based Smart Drone Delivery Optimization System
#   Module: queue_manager.py
#   Purpose: Smart delivery queue — ACCEPT / REJECT / QUEUE /
#            ECO-MERGE decisions using constraints + utility.
# ============================================================

import heapq
import time
from constants import *
from pathfinding import a_star, estimate_battery_cost


class QueueManager:

    def __init__(self, city_map, weather, drones):
        self.city_map = city_map
        self.weather  = weather
        self.drones   = drones
        self.queue    = []    # priority queue of pending deliveries
        self.history  = []    # all completed/rejected deliveries

        self.total_requests = 0
        self.total_accepted = 0
        self.total_rejected = 0
        self.total_eco      = 0

    # ----------------------------------------------------------
    def process_request(self, delivery):
        """
        Main decision pipeline for every incoming delivery:
        1. Find route with A*
        2. Check constraints
        3. Score drones with utility function
        4. ECO-merge check
        5. ACCEPT / REJECT / QUEUE
        """
        self.total_requests += 1
        print(f"\n{ANSI_INFO}[AGENT] SkyRoute AI evaluating delivery "
              f"#{delivery.id}...{ANSI_RESET}")

        # Step 1: Pathfinding
        print(f"{ANSI_INFO}[INFO] Running A* pathfinding...{ANSI_RESET}")
        path, _ = a_star(self.city_map, delivery.pickup,
                         delivery.dropoff, verbose=True)
        if not path:
            self._reject(delivery, ["No flyable route between pickup and dropoff"])
            return

        # Step 2: Constraint check
        ok, reasons = self._check_constraints(delivery, path)

        # Step 3: Weather risk
        risk  = self.weather.get_risk_score(path)
        label = self.weather.risk_label(risk)
        print(f"{ANSI_INFO}[INFO] Weather risk: {label} ({risk:.2f}){ANSI_RESET}")
        if risk > 0.7 and not delivery.is_emergency:
            reasons.append(f"Weather risk too severe ({label})")
            ok = False

        # Step 4: Find best drone
        best_drone = self._best_drone(delivery, path)

        if not ok or best_drone is None:
            if delivery.is_emergency or delivery.delivery_type == TYPE_SHOPPING:
                self._enqueue(delivery)
            elif reasons:
                self._reject(delivery, reasons)
            else:
                self._enqueue(delivery)
            return

        # Step 5: ECO-merge check
        eco_ok, eco_drone = self._eco_check(delivery)
        if eco_ok and eco_drone and not delivery.is_emergency:
            self._accept_eco(delivery, eco_drone)
        else:
            self._accept(delivery, best_drone)

    # ----------------------------------------------------------
    def _check_constraints(self, delivery, path):
        """Check battery, weight, and time window constraints."""
        reasons = []

        cost = estimate_battery_cost(path, delivery.weight, self.city_map)
        print(f"{ANSI_INFO}[INFO] Estimated battery needed : {cost:.1f}%{ANSI_RESET}")

        if delivery.weight > DRONE_MAX_WEIGHT:
            reasons.append(f"Package too heavy: {delivery.weight:.1f}kg "
                           f"(max {DRONE_MAX_WEIGHT}kg)")

        eta = len(path) / DRONE_SPEED_NORMAL
        print(f"{ANSI_INFO}[INFO] Estimated ETA : {eta:.0f}s "
              f"| Window : {delivery.time_window}s{ANSI_RESET}")
        if eta > delivery.time_window:
            reasons.append(f"ETA {eta:.0f}s exceeds window {delivery.time_window}s")

        return len(reasons) == 0, reasons

    # ----------------------------------------------------------
    def _best_drone(self, delivery, path):
        """Score every idle drone and return the best one."""
        print(f"{ANSI_INFO}[INFO] Scoring available drones...{ANSI_RESET}")
        cost = estimate_battery_cost(path, delivery.weight, self.city_map)
        best = None
        best_score = -1.0

        for drone in self.drones:
            if drone.state != "IDLE":
                continue
            available = drone.battery - BATTERY_SAFE_THRESHOLD
            if available < cost:
                print(f"{ANSI_INFO}[INFO]   Drone #{drone.id}: insufficient "
                      f"battery ({drone.battery:.0f}%){ANSI_RESET}")
                continue
            if drone.current_load + delivery.weight > drone.max_weight:
                continue

            bat_score  = drone.battery / 100.0
            dist       = (abs(drone.grid_col - delivery.pickup[0]) +
                          abs(drone.grid_row - delivery.pickup[1]))
            prox_score = 1.0 / (1 + dist * 0.1)
            pri_score  = (4 - delivery.priority) / 4.0
            w_score    = 1.0 - self.weather.get_risk_score(path)
            utility    = bat_score*0.3 + prox_score*0.25 + pri_score*0.3 + w_score*0.15

            print(f"{ANSI_INFO}[INFO]   Drone #{drone.id}: battery={drone.battery:.0f}% "
                  f"utility={utility:.3f}{ANSI_RESET}")
            if utility > best_score:
                best_score = utility
                best       = drone

        if best:
            print(f"{ANSI_OK}[INFO] Best drone: #{best.id} "
                  f"(score={best_score:.3f}){ANSI_RESET}")
        return best

    # ----------------------------------------------------------
    def _eco_check(self, delivery):
        """Check if a busy drone can merge this delivery into its route."""
        for drone in self.drones:
            if drone.state not in ("HEADING_PICKUP", "HEADING_DROPOFF"):
                continue
            if not drone.current_delivery or drone.current_delivery.is_emergency:
                continue
            spare = drone.max_weight - drone.current_load
            if delivery.weight > spare - ECO_WEIGHT_BUFFER:
                continue
            if not drone.path:
                continue
            min_detour = min(
                abs(delivery.pickup[0]-p[0]) + abs(delivery.pickup[1]-p[1])
                for p in drone.path
            )
            if min_detour <= ECO_DETOUR_LIMIT:
                return True, drone
        return False, None

    # ----------------------------------------------------------
    def _accept(self, delivery, drone):
        delivery.status = "ACCEPTED"
        self.total_accepted += 1
        print(f"\n{ANSI_OK}{ANSI_BOLD}"
              f"✓ DELIVERY ACCEPTED — Drone #{drone.id}{ANSI_RESET}")
        print(f"{ANSI_OK}{'='*50}{ANSI_RESET}\n")
        drone.assign_delivery(delivery, eco_mode=False)
        self.history.append(delivery)

    def _accept_eco(self, delivery, drone):
        delivery.status = "ACCEPTED"
        self.total_accepted += 1
        self.total_eco += 1
        print(f"\n{ANSI_OK}{ANSI_BOLD}"
              f"★ ECO MODE ACTIVATED — Merging with Drone #{drone.id}{ANSI_RESET}")
        print(f"{ANSI_OK}{'='*50}{ANSI_RESET}\n")
        drone.assign_delivery(delivery, eco_mode=True)
        self.history.append(delivery)

    def _reject(self, delivery, reasons):
        delivery.status         = "REJECTED"
        delivery.reject_reasons = reasons
        self.total_rejected    += 1
        print(f"\n{ANSI_ERR}{ANSI_BOLD}"
              f"✗ DELIVERY REJECTED — #{delivery.id}{ANSI_RESET}")
        for r in reasons:
            print(f"{ANSI_ERR}  • {r}{ANSI_RESET}")
        print(f"{ANSI_ERR}{'='*50}{ANSI_RESET}\n")
        self.history.append(delivery)

    def _enqueue(self, delivery):
        delivery.status = "QUEUED"
        heapq.heappush(self.queue, (delivery.priority, time.time(), delivery))
        print(f"\n{ANSI_WARN}⏸ DELIVERY QUEUED — #{delivery.id} "
              f"| Queue size: {len(self.queue)}{ANSI_RESET}\n")

    # ----------------------------------------------------------
    def tick(self):
        """Try to assign queued deliveries to newly idle drones."""
        if not self.queue:
            return
        if not any(d.state == "IDLE" for d in self.drones):
            return

        remaining = []
        assigned  = False
        while self.queue:
            pri, ts, delivery = heapq.heappop(self.queue)
            if delivery.is_expired() and not delivery.is_emergency:
                delivery.status = "REJECTED"
                delivery.reject_reasons = ["Expired while in queue"]
                self.total_rejected += 1
                self.history.append(delivery)
                continue
            if not assigned:
                path, _ = a_star(self.city_map, delivery.pickup,
                                 delivery.dropoff, verbose=False)
                drone = self._best_drone(delivery, path) if path else None
                if drone:
                    self._accept(delivery, drone)
                    assigned = True
                    continue
            remaining.append((pri, ts, delivery))

        for item in remaining:
            heapq.heappush(self.queue, item)

    # ----------------------------------------------------------
    def get_queue_list(self):
        return [{"id":d.id,"type":d.delivery_type,"age":d.age(),
                 "emergency":d.is_emergency}
                for (_,_,d) in sorted(self.queue)]

    def get_stats(self):
        return {
            "total":    self.total_requests,
            "accepted": self.total_accepted,
            "rejected": self.total_rejected,
            "queued":   len(self.queue),
            "eco":      self.total_eco,
        }
