"""Global configuration: every tunable value of the game lives in this file."""

import pygame

MAP_FILE = "maps/farm_big.txt"
TILES_FILE = "data/tiles.json"
BUILDINGS_FILE = "data/buildings.json"
NPCS_FILE = "data/npcs.json"
DIALOGUES_FILE = "data/dialogues.json"
ITEMS_FILE = "data/items.json"

PLAYER_SPRITE = "assets/characters/player.png"
CHARACTERS_DIR = "assets/characters/"
ITEMS_DIR = "assets/items/"
CROPS_DIR = "assets/crops/"
SOIL_IMAGES = {False: "assets/tiles/soil.png", True: "assets/tiles/soil_wet.png"}

# ============================================================
# WINDOW
# ============================================================
WINDOW_TITLE = "Farm Mystery"
SCREEN_SIZE = (960, 544)
FULLSCREEN = True
FPS = 60
FONT_SIZE = 32
SMALL_FONT_SIZE = 22

# ============================================================
# WORLD AND CAMERA
# ============================================================
TILE_SIZE = 32
GROUND_TILE = "1"                 # tile drawn under tiles that have a transparent background
OUTSIDE_TILE = {"name": "outside", "color": [0, 0, 0], "solid": True}
UNKNOWN_TILE = {"name": "unknown", "color": [255, 0, 255], "solid": True}
AUTO_HITBOX_MIN_ALPHA = 128       # pixels fainter than this are ignored by "hitbox": "auto"
CAMERA_PADDING = (0, 0, 0, 64)    # how far the camera may go past the map: left, top, right, bottom (px)
CAMERA_OFFSET_Y = 20              # the camera aims this many pixels above the player's feet
CLICK_REACH = 1                   # tiles around the player that can be clicked (1 = the 3x3 around)
HOVER_COLOR = (255, 220, 60)      # outline of the tile under the mouse
HOVER_WIDTH = 2
MISSING_IMAGE_COLOR = (255, 0, 255)

# ============================================================
# TIME
# ============================================================
START_OF_DAY = 6 * 60             # minutes since midnight: the day starts at 6:00
END_OF_DAY = 24 * 60              # the day ends at midnight
DAY_LENGTH_SECONDS = 27           # real seconds from START_OF_DAY to END_OF_DAY
MINUTES_PER_SECOND = (END_OF_DAY - START_OF_DAY) / DAY_LENGTH_SECONDS
NIGHT_START = 18 * 60             # darkness begins at 18:00
MAX_DARKNESS = 150                # opacity of the night layer at midnight (0-255)
NIGHT_COLOR = (0, 0, 40)

# ============================================================
# ENERGY
# ============================================================
MAX_ENERGY = 100
SLEEP_ENERGY_FRACTION = 1.0       # energy after sleeping in bed (1.0 = full)
PASS_OUT_FRACTION = 0.8           # energy after staying up until midnight
LOW_ENERGY = 0.25                 # below this fraction the energy bar turns red
ENERGY_COSTS = {
    "till": 4,                    # shovel on grass
    "water": 2,                   # watering can on soil
    "plant": 1,                   # seeds on soil
    "harvest": 1,                 # picking a ripe crop or collecting honey
    "place_hive": 3,              # putting down a beehive
    "untill": 2,                  # shovel on empty soil (turns it back to grass)
    "pickup_hive": 1,             # shovel on a beehive that has no honey yet
    "milk": 1,                    # milking a cow
}

# ============================================================
# ECONOMY AND ITEMS
# ============================================================
START_GOLD = 100
STARTING_ITEMS = [("shovel", 1), ("pickaxe", 1), ("watering_can", 1), ("cauliflower_seeds", 5)]
SHOP_STOCK = ["cauliflower_seeds", "carrot_seeds", "pumpkin_seeds"]
SLOT_COUNT = 10                   # hotbar slots (keys 1 to 9, then 0)

# ============================================================
# CROPS
# ============================================================
RIPE_STAGE = 3                    # growth stage number of a ripe crop (stages 0 to 2 are growing)
CROPS = {                         # seed item -> what it grows into
    "cauliflower_seeds": {"growth_days": 4, "harvest": "cauliflower", "ripe_color": (230, 230, 240)},
    "carrot_seeds": {"growth_days": 3, "harvest": "carrot", "ripe_color": (240, 140, 40)},
    "pumpkin_seeds": {"growth_days": 6, "harvest": "pumpkin", "ripe_color": (230, 120, 30)},
}

SOIL_REVERT_DAYS = 3              # days an empty tilled tile can stay unused before it turns back to grass

# ============================================================
# COWS
# ============================================================
COW_START_TILES = [(6, 15), (9, 18), (11, 14)]   # where the cows start (inside the pen)
COW_PEN = (4, 13, 13, 21)         # the area they wander in: first column, first row, last column, last row (tiles)
COW_SPRITE = "assets/animals/cow.png"   # optional picture of the cow
COW_SPRITE_FACES = "left"         # which way the cow looks in the picture file: "left" or "right"   # optional picture, drawn looking RIGHT (the game flips it)
COW_SIZE = (48, 40)               # size of the picture in pixels
COW_HITBOX = (30, 14)             # the solid part at the cow's feet (width, height)
COW_FEET_OFFSET = 14              # pixels between the tile center and the cow's feet
COW_SPEED = 30                    # pixels per second
COW_WAIT = (1.5, 5.0)             # a cow rests this many seconds (min, max) between two steps
COW_COLOR = (240, 240, 240)       # used when the picture is missing
COW_SPOT_COLOR = (92, 64, 48)
COW_UDDER_COLOR = (238, 170, 170)
MILK_COLOR = (250, 250, 255)

# ============================================================
# BEEKEEPING
# ============================================================
HIVE_HONEY_DAYS = 3               # days a hive needs to make one honey
HIVE_IMAGE = "assets/items/beehive.png"
HIVE_WOOD = (214, 160, 86)        # colors of the simple hive, used until you draw the pictures
HIVE_ROOF = (240, 200, 110)
HIVE_OUTLINE = (74, 48, 36)
HONEY_COLOR = (255, 200, 50)
HIVE_FLOWER_RADIUS = 5            # the bees look for flowers this many tiles around the hive
HIVE_MIN_FLOWERS = 3              # flowers needed in that area, otherwise the bees do not work
HIVE_PRODUCT = "mad_honey"        # what a hive makes at first (the player only ever sees "Honey")
HIVE_SAFE_PRODUCT = "honey"       # what it makes once the mystery is solved, if the player keeps playing
HIVE_SAFE_FLAG = "mystery_solved" # the story flag that makes the switch


# ============================================================
# PLAYER
# ============================================================
PLAYER_START = (64, 256)          # starting position in pixels
PLAYER_SPEED = 200                # pixels per second
PLAYER_HITBOX = (14, 10)          # width and height of the feet hitbox
PLAYER_SPRITE_SIZE = (64, 64)
PLAYER_FALLBACK_COLOR = (230, 200, 80)

# ============================================================
# NPCS
# ============================================================
NPC_SPEED = 80                    # pixels per second
NPC_SIZE = 24                     # side of the colored square used without a picture
NPC_SPRITE_SIZE = (64, 64)
NPC_FEET_OFFSET = 12              # pixels between the tile center and the feet
SHOW_NPC_NAMES = True
NPC_NAME_COLOR = (255, 255, 255)
NPC_NAME_OFFSET = 18              # pixels between the name and the top of the NPC

# ============================================================
# BUILDINGS
# ============================================================
SHOW_BUILDING_HITBOXES = False    # True draws the hitboxes in red, to adjust them
BUILDING_HITBOX_COLOR = (255, 0, 0)
BUILDING_FALLBACK_COLOR = (110, 110, 120)

# ============================================================
# CONTROLS
# ============================================================
INTERACT_KEYS = (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN)
UP_KEYS = (pygame.K_UP, pygame.K_z, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_q, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
SLOT_KEYS = [pygame.KSCAN_1, pygame.KSCAN_2, pygame.KSCAN_3, pygame.KSCAN_4,
             pygame.KSCAN_5, pygame.KSCAN_6, pygame.KSCAN_7, pygame.KSCAN_8,
             pygame.KSCAN_9, pygame.KSCAN_0]

# ============================================================
# COLORS
# ============================================================
OUTLINE = (34, 23, 18)
WOOD = (118, 82, 54)
WOOD_LIGHT = (156, 114, 78)
WOOD_DARK = (84, 56, 38)
INSET = (58, 40, 31)
INSET_LIGHT = (86, 61, 46)
TEXT = (248, 236, 210)
TEXT_DIM = (196, 176, 146)
ACCENT = (244, 200, 92)
ACCENT_DARK = (176, 126, 40)
COIN_SHINE = (255, 238, 170)
GOOD = (150, 210, 120)
BAD = (232, 128, 112)
DANGER = (150, 64, 52)
ENERGY_GREEN = (110, 190, 90)
ENERGY_LIGHT = (165, 228, 135)

# placeholder art used when a soil or plant picture does not exist
DRY_SOIL = (126, 88, 52)
DRY_FURROW = (100, 68, 40)
WET_SOIL = (84, 56, 34)
WET_FURROW = (62, 40, 24)
SOIL_EDGE = (52, 34, 22)
STEM_COLOR = (58, 128, 62)
LEAF_COLOR = (96, 184, 84)

# ============================================================
# INTERFACE LAYOUT
# ============================================================
ICON_SIZE = 32                    # icons are drawn at their real size so pixels stay sharp
SCREEN_MARGIN = 16
PANEL_BORDER = 8

HOTBAR_SLOT_SIZE = 44
HOTBAR_SLOT_GAP = 3
HOTBAR_BORDER = 6
HOTBAR_MARGIN = 2                 # gap between the hotbar and the bottom of the screen

ENERGY_BAR_WIDTH = 280
ENERGY_BAR_HEIGHT = 36
CLOCK_SIZE = (210, 64)
COIN_BOX_SIZE = (48, 40)
GOLD_BOX_SIZE = (100, 40)
HUD_GAP = 8

SHOP_PANEL_SIZE = (480, 270)
SHOP_ROW_HEIGHT = 40
SHOP_ROW_SPACING = 46

DIALOGUE_BOX_HEIGHT = 130
DIALOGUE_BOX_MARGIN = 20
DIALOGUE_BOX_Y = 412
DIALOGUE_TEXT_PADDING = 20
DIALOGUE_LINE_SPACING = 28