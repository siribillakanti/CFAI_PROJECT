# ============================================================
#   SkyRoute AI-Based Smart Drone Delivery Optimization System
#   Module: constants.py
#   Purpose: Central configuration — all values, colors, and
#            labels used across every module live here.
#            Change a value here and it updates everywhere.
# ============================================================

# ------------------------------------------------------------
# WINDOW & GRID SETTINGS
# ------------------------------------------------------------
WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 720

GRID_COLS = 30
GRID_ROWS = 22
CELL_SIZE  = 32

SIDEBAR_WIDTH = 340

MAP_WIDTH  = GRID_COLS * CELL_SIZE
MAP_HEIGHT = GRID_ROWS * CELL_SIZE

# ------------------------------------------------------------
# COLORS  (Red, Green, Blue)
# ------------------------------------------------------------
COLOR_BG         = (10,  12,  20)
COLOR_SIDEBAR_BG = (15,  18,  30)
COLOR_PANEL_BG   = (20,  24,  40)
COLOR_TEXT       = (220, 230, 255)
COLOR_TEXT_DIM   = (100, 110, 140)
COLOR_ACCENT     = (0,   200, 255)
COLOR_GREEN      = (0,   220, 120)
COLOR_RED        = (255,  70,  70)
COLOR_YELLOW     = (255, 220,  50)
COLOR_ORANGE     = (255, 140,   0)
COLOR_PURPLE     = (160,  80, 255)
COLOR_WHITE      = (255, 255, 255)

COLOR_ROAD           = (30,  34,  52)
COLOR_BUILDING       = (45,  50,  75)
COLOR_NOFLY          = (80,  20,  20)
COLOR_CHARGING       = (20,  80,  60)
COLOR_PICKUP         = (20,  60, 100)
COLOR_DROPOFF        = (80,  50,  20)
COLOR_WEATHER_RAIN   = (30,  50,  80)
COLOR_WEATHER_WIND   = (40,  60,  50)
COLOR_WEATHER_STORM  = (60,  20,  60)
COLOR_WEATHER_FOG    = (60,  60,  70)

# ------------------------------------------------------------
# CELL TYPE IDs
# ------------------------------------------------------------
CELL_ROAD     = 0
CELL_BUILDING = 1
CELL_NOFLY    = 2
CELL_CHARGING = 3
CELL_PICKUP   = 4
CELL_DROPOFF  = 5
CELL_RAIN     = 6
CELL_WIND     = 7
CELL_STORM    = 8
CELL_FOG      = 9

CELL_NAMES = {
    CELL_ROAD:     "Road",
    CELL_BUILDING: "Building",
    CELL_NOFLY:    "No-Fly Zone",
    CELL_CHARGING: "Charging Station",
    CELL_PICKUP:   "Pickup Point",
    CELL_DROPOFF:  "Drop-off Point",
    CELL_RAIN:     "Rain Zone",
    CELL_WIND:     "Wind Zone",
    CELL_STORM:    "Storm Zone",
    CELL_FOG:      "Fog Zone",
}

# ------------------------------------------------------------
# DELIVERY TYPES
# ------------------------------------------------------------
TYPE_MEDICINE = "Medicine"
TYPE_FOOD     = "Food"
TYPE_SHOPPING = "Shopping"

PRIORITY_EMERGENCY = 0
PRIORITY_MEDICINE  = 1
PRIORITY_FOOD      = 2
PRIORITY_SHOPPING  = 3

DELIVERY_PRIORITY = {
    TYPE_MEDICINE: PRIORITY_MEDICINE,
    TYPE_FOOD:     PRIORITY_FOOD,
    TYPE_SHOPPING: PRIORITY_SHOPPING,
}

TIME_WINDOW = {
    TYPE_MEDICINE: 60,
    TYPE_FOOD:     120,
    TYPE_SHOPPING: 300,
}

DELIVERY_COLORS = {
    TYPE_MEDICINE: (220,  80,  80),
    TYPE_FOOD:     ( 80, 200, 100),
    TYPE_SHOPPING: ( 80, 140, 220),
}

# ------------------------------------------------------------
# BATTERY SETTINGS
# ------------------------------------------------------------
BATTERY_DRAIN_PER_CELL  = 0.8
BATTERY_WEIGHT_PENALTY  = 0.15
BATTERY_RAIN_PENALTY    = 0.4
BATTERY_WIND_PENALTY    = 0.3
BATTERY_STORM_PENALTY   = 0.8
BATTERY_FOG_PENALTY     = 0.2
BATTERY_CHARGE_RATE     = 1.5
BATTERY_SAFE_THRESHOLD  = 15.0
BATTERY_LOW_WARNING     = 25.0
BATTERY_FULL            = 100.0

# ------------------------------------------------------------
# DRONE SETTINGS
# ------------------------------------------------------------
DRONE_SPEED_NORMAL = 2.5
DRONE_SPEED_WIND   = 1.5
DRONE_MAX_WEIGHT   = 10.0

DRONE_COLORS = [
    (  0, 200, 255),
    (  0, 255, 160),
    (255, 180,   0),
    (200,  80, 255),
]

# ------------------------------------------------------------
# ECO-MERGE SETTINGS
# ------------------------------------------------------------
ECO_DETOUR_LIMIT  = 4
ECO_WEIGHT_BUFFER = 2.0

# ------------------------------------------------------------
# WEATHER SETTINGS
# ------------------------------------------------------------
WEATHER_CHANGE_INTERVAL = 400

# ------------------------------------------------------------
# SIMULATION SETTINGS
# ------------------------------------------------------------
FPS       = 30
SIM_SPEED = 1.0

# ------------------------------------------------------------
# CONSOLE LOG COLORS
# ------------------------------------------------------------
ANSI_RESET  = "\033[0m"
ANSI_INFO   = "\033[36m"
ANSI_OK     = "\033[32m"
ANSI_WARN   = "\033[33m"
ANSI_ERR    = "\033[31m"
ANSI_BOLD   = "\033[1m"
ANSI_PURPLE = "\033[35m"

# ------------------------------------------------------------
# PROJECT IDENTITY
# ------------------------------------------------------------
PROJECT_NAME    = "SkyRoute AI-Based Smart Drone Delivery Optimization System"
PROJECT_VERSION = "v1.0"
PROJECT_AUTHOR  = "SkyRoute Simulation Engine"
