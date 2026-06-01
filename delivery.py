# ============================================================
#   SkyRoute AI-Based Smart Drone Delivery Optimization System
#   Module: delivery.py
#   Purpose: Delivery data model and random request generator.
# ============================================================

import random
import time
from constants import *


class Delivery:

    _id_counter = 0

    def __init__(self, delivery_type, pickup, dropoff,
                 weight=None, is_emergency=False):
        Delivery._id_counter += 1
        self.id            = Delivery._id_counter
        self.delivery_type = delivery_type
        self.pickup        = pickup
        self.dropoff       = dropoff
        self.weight        = weight if weight else random.uniform(0.5, 5.0)
        self.is_emergency  = is_emergency and (delivery_type == TYPE_MEDICINE)
        self.created_at    = time.time()
        self.time_window   = TIME_WINDOW[delivery_type]
        self.priority      = PRIORITY_EMERGENCY if self.is_emergency \
                             else DELIVERY_PRIORITY[delivery_type]
        self.status        = "PENDING"
        self.drone_id      = None
        self.reject_reasons = []

    def __lt__(self, other):
        return self.priority < other.priority

    def age(self):
        return time.time() - self.created_at

    def is_expired(self):
        return self.age() > self.time_window

    def print_request(self):
        em = " *** EMERGENCY ***" if self.is_emergency else ""
        tc = {TYPE_MEDICINE:ANSI_ERR, TYPE_FOOD:ANSI_OK,
              TYPE_SHOPPING:ANSI_INFO}.get(self.delivery_type, ANSI_INFO)
        print(f"\n{ANSI_BOLD}{'='*50}{ANSI_RESET}")
        print(f"{ANSI_BOLD}  SkyRoute AI — NEW DELIVERY REQUEST{ANSI_RESET}")
        print(f"  ID       : #{self.id}")
        print(f"{tc}  Type     : {self.delivery_type}{em}{ANSI_RESET}")
        print(f"  Pickup   : {self.pickup}")
        print(f"  Drop-off : {self.dropoff}")
        print(f"  Weight   : {self.weight:.1f} kg")
        print(f"  Priority : {self.priority}")
        print(f"  Window   : {self.time_window}s")
        print(f"{ANSI_BOLD}{'='*50}{ANSI_RESET}")


def generate_random_delivery(city_map):
    """Create a random delivery using map pickup/dropoff points."""
    dtype = random.choices(
        [TYPE_MEDICINE, TYPE_FOOD, TYPE_SHOPPING],
        weights=[25, 40, 35]
    )[0]
    pickup  = city_map.get_random_pickup()
    dropoff = city_map.get_random_dropoff()
    while dropoff == pickup:
        dropoff = city_map.get_random_dropoff()
    weight       = random.uniform(0.5, 8.0)
    is_emergency = (dtype == TYPE_MEDICINE) and (random.random() < 0.10)
    d = Delivery(dtype, pickup, dropoff, weight, is_emergency)
    d.print_request()
    return d
