# ============================================================
#   SkyRoute AI-Based Smart Drone Delivery Optimization System
#   Module: main.py
#   Purpose: Main simulation window — 2 drones, clean controls,
#            on-screen key guide, sidebar info panel.
#
#   CONTROLS:
#       SPACE  →  Start / unpause simulation
#       E      →  Send Emergency Medicine delivery
#       F      →  Send Food delivery
#       S      →  Send Shopping delivery
#       Q      →  Quit
# ============================================================

import pygame
import sys
import time
import random

from constants import *
from map import CityMap
from drone import Drone
from delivery import Delivery, TYPE_MEDICINE, TYPE_FOOD, TYPE_SHOPPING
from queue_manager import QueueManager
from weather import WeatherSystem


# ============================================================
# Small drawing helpers
# ============================================================

def txt(surface, text, x, y, font, color=COLOR_TEXT):
    """Draw text with a 1-pixel dark shadow for readability."""
    surface.blit(font.render(text, True, (0, 0, 0)), (x + 1, y + 1))
    surface.blit(font.render(text, True, color),     (x,     y    ))


def battery_bar(surface, x, y, w, h, pct):
    """Draw a colored battery percentage bar."""
    pygame.draw.rect(surface, (30, 35, 55), (x, y, w, h))
    fill  = int(w * max(0.0, min(1.0, pct / 100.0)))
    color = COLOR_GREEN if pct > 60 else COLOR_YELLOW if pct > 25 else COLOR_RED
    if fill > 0:
        pygame.draw.rect(surface, color, (x, y, fill, h))
    pygame.draw.rect(surface, (60, 70, 100), (x, y, w, h), 1)


# ============================================================
# ON-SCREEN CONTROLS GUIDE  (bottom of the map area)
# ============================================================

def draw_controls(surface, font, sim_started):
    """
    Draw a controls bar at the very bottom of the map.
    Shows all keyboard shortcuts so the teacher can see them clearly.
    """
    bar_y = MAP_HEIGHT - 28
    # Semi-transparent dark bar
    bar   = pygame.Surface((MAP_WIDTH, 28), pygame.SRCALPHA)
    bar.fill((10, 12, 25, 200))
    surface.blit(bar, (0, bar_y))

    # Divider line above bar
    pygame.draw.line(surface, (40, 55, 90), (0, bar_y), (MAP_WIDTH, bar_y), 1)

    # Key labels
    keys = [
        ("[SPACE]", "Start",     COLOR_GREEN  if not sim_started else COLOR_TEXT_DIM),
        ("[E]",     "Emergency", COLOR_RED),
        ("[F]",     "Food",      COLOR_GREEN),
        ("[S]",     "Shopping",  COLOR_ACCENT),
        ("[Q]",     "Quit",      COLOR_YELLOW),
    ]
    x = 10
    for key, label, color in keys:
        txt(surface, key,   x,      bar_y + 4,  font, color)
        txt(surface, label, x + 56, bar_y + 4,  font, COLOR_TEXT_DIM)
        x += 140


# ============================================================
# SIDEBAR  (right panel — all info)
# ============================================================

def draw_sidebar(screen, fonts, drones, qm, weather, tick, sim_started, messages):
    """
    Draw the full right-side information panel.
    Shows: title, weather, drone cards, queue, stats, log.
    """
    sx = MAP_WIDTH          # sidebar starts here
    sw = SIDEBAR_WIDTH
    sh = WINDOW_HEIGHT

    ft = fonts['title']
    fb = fonts['body']
    fs = fonts['small']

    # Background + border line
    pygame.draw.rect(screen, COLOR_SIDEBAR_BG, (sx, 0, sw, sh))
    pygame.draw.line(screen, (40, 50, 80), (sx, 0), (sx, sh), 2)

    y = 8

    # --- Project title ---
    txt(screen, "SkyRoute AI", sx + 10, y, ft, COLOR_ACCENT)
    y += 20
    txt(screen, "Drone Delivery System", sx + 10, y, fs, COLOR_TEXT_DIM)
    y += 14

    # Sim time
    sim_sec = tick // FPS
    txt(screen, f"Time: {sim_sec // 60:02d}:{sim_sec % 60:02d}",
        sx + 10, y, fs, COLOR_TEXT_DIM)
    y += 14

    # Start hint if not started yet
    if not sim_started:
        txt(screen, "Press SPACE to start!", sx + 10, y, fb, COLOR_YELLOW)
        y += 16

    pygame.draw.line(screen, (40, 55, 90), (sx + 5, y), (sx + sw - 5, y), 1)
    y += 6

    # --- Weather ---
    pygame.draw.rect(screen, COLOR_PANEL_BG,
                     (sx + 5, y, sw - 10, 46), border_radius=4)
    txt(screen, "WEATHER", sx + 10, y + 3, fb, COLOR_ACCENT)
    wc = COLOR_RED if "STORM" in weather.summary else \
         COLOR_YELLOW if weather.summary != "CLEAR" else COLOR_GREEN
    txt(screen, weather.summary, sx + 10, y + 18, fs, wc)

    # Rain probability bar
    rw = int((sw - 30) * weather.rain_prob)
    pygame.draw.rect(screen, (30, 50, 90),   (sx + 10, y + 34, sw - 30, 6))
    if rw > 0:
        pygame.draw.rect(screen, (60, 120, 200), (sx + 10, y + 34, rw,     6))
    txt(screen, f"Rain {weather.rain_prob:.0%}", sx + sw - 72, y + 31, fs, COLOR_TEXT_DIM)
    y += 54

    pygame.draw.line(screen, (40, 55, 90), (sx + 5, y), (sx + sw - 5, y), 1)
    y += 6

    # --- Drone cards ---
    txt(screen, "DRONES", sx + 10, y, fb, COLOR_ACCENT)
    y += 16

    state_colors = {
        "IDLE":             COLOR_TEXT_DIM,
        "HEADING_PICKUP":   COLOR_YELLOW,
        "HEADING_DROPOFF":  COLOR_ORANGE,
        "CHARGING":         COLOR_GREEN,
    }

    for drone in drones:
        s = drone.get_status()
        pygame.draw.rect(screen, COLOR_PANEL_BG,
                         (sx + 5, y, sw - 10, 72), border_radius=4)

        # Color dot + name
        pygame.draw.circle(screen, s['color'], (sx + 16, y + 12), 6)
        txt(screen, f"DRONE  #{s['id']}", sx + 28, y + 5, fb, COLOR_TEXT)

        # State
        sc = state_colors.get(s['state'], COLOR_TEXT_DIM)
        txt(screen, s['state'], sx + 28, y + 20, fs, sc)

        # Battery bar
        battery_bar(screen, sx + 10, y + 36, sw - 80, 9, s['battery'])
        bc = COLOR_RED if s['battery'] < 25 else COLOR_TEXT
        txt(screen, f"{s['battery']:.0f}%", sx + sw - 65, y + 33, fs, bc)

        # Status message + deliveries done
        mc = COLOR_GREEN if s['eco'] else COLOR_TEXT_DIM
        txt(screen, s['msg'][:26],           sx + 10,      y + 52, fs, mc)
        txt(screen, f"done: {s['done']}",    sx + sw - 75, y + 52, fs, COLOR_GREEN)
        y += 76

    pygame.draw.line(screen, (40, 55, 90), (sx + 5, y), (sx + sw - 5, y), 1)
    y += 6

    # --- Queue ---
    items = qm.get_queue_list()
    txt(screen, f"QUEUE  ({len(items)})", sx + 10, y, fb, COLOR_ACCENT)
    y += 16

    tc_map = {
        TYPE_MEDICINE: COLOR_RED,
        TYPE_FOOD:     COLOR_GREEN,
        TYPE_SHOPPING: COLOR_ACCENT,
    }
    for item in items[:3]:
        em = "★ " if item['emergency'] else "• "
        c  = tc_map.get(item['type'], COLOR_TEXT_DIM)
        txt(screen,
            f"{em}#{item['id']}  {item['type'][:4].upper()}  {item['age']:.0f}s",
            sx + 10, y, fs, c)
        y += 13
    if len(items) > 3:
        txt(screen, f"  + {len(items)-3} more...", sx + 10, y, fs, COLOR_TEXT_DIM)
        y += 13

    pygame.draw.line(screen, (40, 55, 90), (sx + 5, y), (sx + sw - 5, y), 1)
    y += 6

    # --- Stats ---
    st = qm.get_stats()
    txt(screen, "STATS", sx + 10, y, fb, COLOR_ACCENT)
    y += 16
    for line, lc in [
        (f"Requests  : {st['total']}",   COLOR_TEXT),
        (f"Accepted  : {st['accepted']}", COLOR_GREEN),
        (f"Rejected  : {st['rejected']}", COLOR_RED),
        (f"In Queue  : {st['queued']}",   COLOR_YELLOW),
        (f"ECO Saves : {st['eco']}",      COLOR_GREEN),
    ]:
        txt(screen, line, sx + 10, y, fs, lc)
        y += 13

    pygame.draw.line(screen, (40, 55, 90), (sx + 5, y), (sx + sw - 5, y), 1)
    y += 6

    # --- Map legend ---
    txt(screen, "MAP LEGEND", sx + 10, y, fb, COLOR_ACCENT)
    y += 16
    for lc, name in [
        (COLOR_CHARGING,      "Charging Station"),
        (COLOR_PICKUP,        "Pickup Point"),
        (COLOR_DROPOFF,       "Drop-off Point"),
        (COLOR_NOFLY,         "No-Fly Zone"),
        (COLOR_WEATHER_STORM, "Storm Zone"),
        (COLOR_WEATHER_RAIN,  "Rain Zone"),
    ]:
        pygame.draw.rect(screen, lc, (sx + 10, y + 2, 10, 10))
        txt(screen, name, sx + 26, y, fs, COLOR_TEXT_DIM)
        y += 13

    pygame.draw.line(screen, (40, 55, 90), (sx + 5, y), (sx + sw - 5, y), 1)
    y += 6

    # --- Recent event log (last 5 messages) ---
    txt(screen, "EVENT LOG", sx + 10, y, fb, COLOR_ACCENT)
    y += 16
    for msg, color in messages[-5:]:
        txt(screen, msg[:30], sx + 10, y, fs, color)
        y += 13


# ============================================================
# MAIN
# ============================================================

def make_delivery(dtype, city_map, is_emergency=False):
    """Helper: create and return a Delivery of the given type."""
    pickup  = city_map.get_random_pickup()
    dropoff = city_map.get_random_dropoff()
    while dropoff == pickup:
        dropoff = city_map.get_random_dropoff()
    weight = random.uniform(0.5, 5.0)
    d = Delivery(dtype, pickup, dropoff, weight=weight, is_emergency=is_emergency)
    d.print_request()
    return d


def main():
    # ---- Startup banner ----
    print(f"\n{ANSI_BOLD}{ANSI_INFO}")
    print("=" * 60)
    print(f"   {PROJECT_NAME}")
    print(f"   {PROJECT_VERSION}  |  {PROJECT_AUTHOR}")
    print("=" * 60)
    print(f"{ANSI_RESET}")
    print(f"{ANSI_INFO}  CONTROLS:")
    print(f"    SPACE  →  Start simulation")
    print(f"    E      →  Emergency Medicine delivery")
    print(f"    F      →  Food delivery")
    print(f"    S      →  Shopping delivery")
    print(f"    Q      →  Quit{ANSI_RESET}\n")

    # ---- Pygame setup ----
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(PROJECT_NAME)
    clock  = pygame.time.Clock()

    fonts = {
        'title': pygame.font.SysFont("consolas", 14, bold=True),
        'body':  pygame.font.SysFont("consolas", 12, bold=True),
        'small': pygame.font.SysFont("consolas", 10),
    }

    # ---- Build world ----
    city_map = CityMap()
    weather  = WeatherSystem(city_map)
    weather.print_report()

    # ---- 2 Drones only ----
    drones = [
        Drone(1, (2,  10), DRONE_COLORS[0], city_map, weather),   # cyan
        Drone(2, (24, 10), DRONE_COLORS[1], city_map, weather),   # mint
    ]

    qm = QueueManager(city_map, weather, drones)

    # ---- Surface for map (redrawn each frame) ----
    map_surf = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))

    # ---- State ----
    tick        = 0
    sim_started = False          # waits for SPACE before auto-deliveries
    last_auto   = time.time()
    AUTO_INTERVAL = 12.0         # seconds between auto deliveries once started

    # Event log: list of (short_string, color)
    messages = [("SkyRoute AI ready!", COLOR_ACCENT)]

    # ---- Game loop ----
    running = True
    while running:
        dt    = clock.tick(FPS) / 1000.0
        tick += 1

        # ---- Events ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_q:
                    running = False

                elif event.key == pygame.K_SPACE:
                    if not sim_started:
                        sim_started = True
                        print(f"{ANSI_OK}[SYSTEM] Simulation STARTED!{ANSI_RESET}")
                        messages.append(("Simulation started!", COLOR_GREEN))
                        # Kick off with one delivery of each type
                        for dtype in [TYPE_MEDICINE, TYPE_FOOD, TYPE_SHOPPING]:
                            d = make_delivery(dtype, city_map)
                            qm.process_request(d)

                elif event.key == pygame.K_e:
                    # Emergency Medicine
                    d = make_delivery(TYPE_MEDICINE, city_map, is_emergency=True)
                    qm.process_request(d)
                    messages.append(("EMERGENCY medicine sent!", COLOR_RED))

                elif event.key == pygame.K_f:
                    # Food delivery
                    d = make_delivery(TYPE_FOOD, city_map)
                    qm.process_request(d)
                    messages.append(("Food delivery added", COLOR_GREEN))

                elif event.key == pygame.K_s:
                    # Shopping delivery
                    d = make_delivery(TYPE_SHOPPING, city_map)
                    qm.process_request(d)
                    messages.append(("Shopping delivery added", COLOR_ACCENT))

        # ---- Auto deliveries after sim started ----
        if sim_started and time.time() - last_auto > AUTO_INTERVAL:
            dtype = random.choice([TYPE_MEDICINE, TYPE_FOOD, TYPE_SHOPPING])
            d     = make_delivery(dtype, city_map)
            qm.process_request(d)
            messages.append((f"Auto: {dtype} delivery", COLOR_TEXT_DIM))
            last_auto = time.time()

        # ---- Update (only when started) ----
        if sim_started:
            weather.update()
            for drone in drones:
                drone.update(dt)
            qm.tick()

        # ---- Draw ----
        city_map.draw(map_surf)
        for drone in drones:
            drone.draw(map_surf)

        # Controls bar at bottom of map
        draw_controls(map_surf, fonts['small'], sim_started)

        # Drone ID labels directly on map
        lf = fonts['small']
        for drone in drones:
            lx = int(drone.pixel_x) - 10
            ly = int(drone.pixel_y) - 20
            txt(map_surf, f"D{drone.id}", lx, ly, lf, drone.color)

        screen.fill(COLOR_BG)
        screen.blit(map_surf, (0, 0))
        draw_sidebar(screen, fonts, drones, qm, weather, tick,
                     sim_started, messages)
        pygame.display.flip()

    # ---- End ----
    pygame.quit()
    print(f"\n{ANSI_BOLD}{'='*60}")
    print(f"  SkyRoute AI — Simulation Ended")
    print(f"{'='*60}{ANSI_RESET}")
    s = qm.get_stats()
    print(f"  Total Requests : {s['total']}")
    print(f"  Accepted       : {s['accepted']}")
    print(f"  Rejected       : {s['rejected']}")
    print(f"  ECO Merges     : {s['eco']}")
    print(f"  Delivered      : {sum(d.deliveries_done for d in drones)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
