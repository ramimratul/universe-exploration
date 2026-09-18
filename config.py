# ============================== #
# config.py — Configuration file
# ============================== #

## Window & Display
WINDOW_TITLE  = "Universe Exploration"
SCREEN_WIDTH  = 1360
SCREEN_HEIGHT = 768
FPS           = 60

## Grid
CELL_SIZE     = 48
GRID_COLS     = 21    ### 21 * 48 = 1008px
GRID_ROWS     = 15    ### 15 * 48 = 720px

GRID_PADDING  = 8     ### padding from window edges
GRID_OFFSET_X = GRID_PADDING
GRID_OFFSET_Y = (SCREEN_HEIGHT - GRID_ROWS * CELL_SIZE) // 2  ### centred: (768-720)//2 = 24

## HUD
HUD_X     = GRID_OFFSET_X + GRID_COLS * CELL_SIZE + GRID_PADDING  ### 8 + 1008 + 8 = 1024
HUD_WIDTH = SCREEN_WIDTH - HUD_X - 4                               ### 1360 - 1024 - 4 = 332

## Colors
COLOR_BG          = (6, 8, 24)
COLOR_GRID_LINE   = (20, 28, 55)

COLOR_FOG         = (4, 5, 16)
COLOR_FOG_PARTIAL = (14, 22, 50)

COLOR_STAR        = (255, 240, 100)
COLOR_PLANET      = (80, 160, 220)
COLOR_EXOPLANET   = (140, 220, 180)
COLOR_SATELLITE   = (180, 180, 220)
COLOR_ASTEROID    = (160, 130, 90)
COLOR_COMET       = (160, 220, 255)

COLOR_RESOURCE_COMMON   = (100, 200, 100)
COLOR_RESOURCE_RARE     = (80, 160, 255)
COLOR_RESOURCE_EXOTIC   = (220, 80, 255)
COLOR_DISCOVERY         = (255, 200, 50)

COLOR_PLAYER    = (0, 230, 180)
COLOR_AI        = (255, 100, 80)
COLOR_HAZARD    = (220, 60, 60)

COLOR_HUD_BG     = (8, 12, 32)
COLOR_HUD_TEXT   = (235, 245, 255)
COLOR_HUD_ACCENT = (0, 230, 210)
COLOR_WHITE      = (255, 255, 255)
COLOR_DIMWHITE   = (195, 210, 235)

## Fonts
FONT_SIZE_LARGE  = 26
FONT_SIZE_MEDIUM = 18
FONT_SIZE_SMALL  = 13

## Fog states
FOG_HIDDEN   = 0
FOG_PARTIAL  = 1
FOG_REVEALED = 2

## Celestial Body Types
BODY_STAR       = "star"
BODY_PLANET     = "planet"
BODY_EXOPLANET  = "exoplanet"
BODY_SATELLITE  = "satellite"
BODY_ASTEROID   = "asteroid"
BODY_COMET      = "comet"
BODY_EMPTY      = "empty"

## Resource Types
RESOURCE_NONE      = "none"
RESOURCE_COMMON    = "common"
RESOURCE_RARE      = "rare"
RESOURCE_EXOTIC    = "exotic"
RESOURCE_DISCOVERY = "discovery"

RESOURCE_VALUES = {
    RESOURCE_NONE:      0,
    RESOURCE_COMMON:    10,
    RESOURCE_RARE:      40,
    RESOURCE_EXOTIC:    100,
    RESOURCE_DISCOVERY: 250,
}

## Fuel
PLAYER_START_FUEL = 150
AI_START_FUEL     = 150
FUEL_MOVE_COST    = 1
FUEL_SCAN_COST    = 2

## Scanner
SCAN_RADIUS         = 3
START_REVEAL_RADIUS = 2
AI_REVEAL_RADIUS    = 2

## Map Generation
BODY_SPAWN_CHANCE = 0.30

BODY_TYPE_WEIGHTS = {
    BODY_STAR:      0.08,
    BODY_PLANET:    0.22,
    BODY_EXOPLANET: 0.12,
    BODY_SATELLITE: 0.18,
    BODY_ASTEROID:  0.25,
    BODY_COMET:     0.15,
}

RESOURCE_SPAWN_CHANCE = 0.65

RESOURCE_TYPE_WEIGHTS = {
    RESOURCE_COMMON:    0.55,
    RESOURCE_RARE:      0.28,
    RESOURCE_EXOTIC:    0.12,
    RESOURCE_DISCOVERY: 0.05,
}

HAZARD_SPAWN_CHANCE = 0.08
HAZARD_EXTRA_FUEL   = 3

## Known, Unknown
KNOWN_COLS_FRACTION = 0.25

## Game States (** Don't change the states without my permission--RR)
STATE_START        = "start"
STATE_AI_INTRO     = "ai_intro"
STATE_AI_TURN      = "ai_turn"
STATE_PLAYER_INTRO = "player_intro"
STATE_PLAYER_TURN  = "player_turn"
STATE_GAME_OVER    = "game_over"
STATE_END          = "end"

TRANSITION_DURATION = 2500   ### ms