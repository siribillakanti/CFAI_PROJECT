# ============================================================
#   SkyRoute AI-Based Smart Drone Delivery Optimization System
#   Module: pathfinding.py
#   Purpose: A* Search Algorithm — finds the shortest safe
#            route between two grid points for drones.
# ============================================================

import heapq
from constants import *


def manhattan_distance(a, b):
    """Straight-line grid distance — the A* heuristic."""
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def a_star(city_map, start, goal, verbose=True):
    """
    A* Search Algorithm.
    Returns (path, stats)
      path  = list of (col,row) from start to goal
      stats = { nodes_explored, path_cost }
    Returns ([], stats) if no path exists.
    """
    if verbose:
        print(f"{ANSI_INFO}[A*] Searching: {start} → {goal}{ANSI_RESET}")

    # Priority queue entries: (f_score, g_score, position)
    open_set = []
    heapq.heappush(open_set, (manhattan_distance(start,goal), 0, start))

    g_score   = {start: 0}       # cheapest known cost to reach each node
    came_from = {}                # parent map for path reconstruction
    closed    = set()             # already fully processed nodes
    explored  = 0

    while open_set:
        f, g, current = heapq.heappop(open_set)

        if current == goal:
            path = _rebuild_path(came_from, current)
            cost = round(g_score[goal], 2)
            if verbose:
                print(f"{ANSI_OK}[A*] Path found | "
                      f"Nodes explored: {explored} | "
                      f"Length: {len(path)} cells | "
                      f"Cost: {cost}{ANSI_RESET}")
            return path, {"nodes_explored": explored, "path_cost": cost}

        if current in closed:
            continue
        closed.add(current)
        explored += 1

        for nb in _neighbors(city_map, current):
            if nb in closed:
                continue
            new_g = g_score[current] + city_map.movement_cost(nb[0], nb[1])
            if new_g < g_score.get(nb, float('inf')):
                came_from[nb] = current
                g_score[nb]   = new_g
                heapq.heappush(open_set,
                    (new_g + manhattan_distance(nb, goal), new_g, nb))

    if verbose:
        print(f"{ANSI_ERR}[A*] No path found! Nodes explored: {explored}{ANSI_RESET}")
    return [], {"nodes_explored": explored, "path_cost": float('inf')}


def _neighbors(city_map, pos):
    """Return walkable 4-directional neighbors of pos."""
    col, row = pos
    result = []
    for dc, dr in [(0,-1),(0,1),(-1,0),(1,0)]:
        nc, nr = col+dc, row+dr
        if city_map.is_walkable(nc, nr):
            result.append((nc, nr))
    return result


def _rebuild_path(came_from, current):
    """Walk back through came_from to get the full path."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def estimate_battery_cost(path, weight, city_map):
    """
    Estimate how much battery % a drone needs to travel this path
    carrying 'weight' kg. Accounts for weather cells.
    """
    if not path or len(path) < 2:
        return 0.0
    total = 0.0
    for (col, row) in path[1:]:
        cell   = city_map.get_cell(col, row)
        drain  = BATTERY_DRAIN_PER_CELL
        drain += weight * BATTERY_WEIGHT_PENALTY
        if cell == CELL_RAIN:  drain += BATTERY_RAIN_PENALTY
        if cell == CELL_WIND:  drain += BATTERY_WIND_PENALTY
        if cell == CELL_FOG:   drain += BATTERY_FOG_PENALTY
        total += drain
    return round(total, 2)
