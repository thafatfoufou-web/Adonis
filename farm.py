import os
import pygame
from assets import load_image
from world import TILE_SIZE

# key = the seed item, value = what the crop needs and gives
CROPS = {
    "cauliflower_seeds": {
        "growth_days": 4,
        "harvest": "cauliflower",
        "ripe_color": (230, 230, 240),
    },
        "carrot_seeds": {
        "growth_days": 3,
        "harvest": "carrot",
        "ripe_color": (240, 140, 40),
    },
    "pumpkin_seeds": {
        "growth_days": 6,
        "harvest": "pumpkin",
        "ripe_color": (230, 120, 30),
    },
}

# pictures you can draw later. If a file is missing, the code draws a simple one.
#   assets/tiles/soil_dry.png and soil_wet.png          (32x32)
#   assets/crops/<harvest>_<stage>.png, for example carrot_0.png ... carrot_3.png
# stages 0, 1, 2 are the growing plant and stage 3 is the ripe crop
SOIL_IMAGES = {False: "assets/tiles/soil_dry.png", True: "assets/tiles/soil_wet.png"}
RIPE_STAGE = 3

# colors of the simple soil and plant, used until you draw the pictures
DRY_SOIL = (126, 88, 52)
DRY_FURROW = (100, 68, 40)
WET_SOIL = (84, 56, 34)
WET_FURROW = (62, 40, 24)
SOIL_EDGE = (52, 34, 22)
STEM_COLOR = (58, 128, 62)
LEAF_COLOR = (96, 184, 84)

# file path -> picture, or None when the file does not exist
_images = {}


def get_image(path):
    """Return the 32x32 picture of a file, or None if the file does not exist."""
    if path not in _images:
        if os.path.exists(path):
            _images[path] = load_image(path, (TILE_SIZE, TILE_SIZE), (255, 0, 255))
        else:
            _images[path] = None
    return _images[path]


class Farm:
    def __init__(self):
        # (tile x, tile y) -> {"watered": bool, "crop": None or {"seed": id, "days": int}}
        self.soil = {}

    def is_ripe(self, tile):
        crop = tile["crop"]
        if crop is None:
            return False
        return crop["days"] >= CROPS[crop["seed"]]["growth_days"]

    def use(self, tx, ty, inventory, world):
        tile = self.soil.get((tx, ty))

        # 1. a ripe crop is harvested whatever we hold
        if tile is not None and self.is_ripe(tile):
            harvest = CROPS[tile["crop"]["seed"]]["harvest"]
            if inventory.add_item(harvest):
                tile["crop"] = None
            return

        slot = inventory.get_selected()
        if slot is None:
            return
        item = slot["id"]

        # 2. shovel: grass becomes tilled soil
        if item == "shovel":
            if tile is None and world.is_tillable(tx, ty):
                self.soil[(tx, ty)] = {"watered": False, "crop": None}

        # 3. watering can: water tilled soil
        elif item == "watering_can":
            if tile is not None:
                tile["watered"] = True

        # 4. seeds: plant on empty tilled soil
        elif item in CROPS:
            if tile is not None and tile["crop"] is None:
                tile["crop"] = {"seed": item, "days": 0}
                inventory.remove_one_selected()

    def new_day(self):
        for tile in self.soil.values():
            if tile["crop"] is not None and tile["watered"]:
                tile["crop"]["days"] += 1
            tile["watered"] = False

    def draw_soil(self, screen, rect, watered):
        """Draw one tilled tile: its picture if it exists, otherwise soil with furrows."""
        image = get_image(SOIL_IMAGES[watered])
        if image is not None:
            screen.blit(image, rect)
            return

        pygame.draw.rect(screen, WET_SOIL if watered else DRY_SOIL, rect)
        furrow = WET_FURROW if watered else DRY_FURROW
        for y in (9, 17, 25):
            pygame.draw.line(screen, furrow, (rect.x + 4, rect.y + y), (rect.right - 5, rect.y + y), 2)
        pygame.draw.rect(screen, SOIL_EDGE, rect, 1)

    def draw_sprout(self, screen, rect, stage):
        """Draw a small plant made of rectangles. Stage 0 is tiny, stage 2 is almost grown."""
        stem_height = (5, 9, 13)[stage]
        leaf_width = (3, 4, 5)[stage]
        pairs = (1, 2, 3)[stage]
        x = rect.centerx - 1
        top = rect.bottom - 6 - stem_height

        pygame.draw.rect(screen, STEM_COLOR, (x, top, 2, stem_height))
        for i in range(pairs):
            y = top + 1 + i * 4
            pygame.draw.rect(screen, LEAF_COLOR, (x - leaf_width, y, leaf_width, 2))
            pygame.draw.rect(screen, LEAF_COLOR, (x + 2, y, leaf_width, 2))

    def draw_crop(self, screen, rect, tile):
        """Draw the crop of a tile, with the picture of its growth stage."""
        crop = tile["crop"]
        data = CROPS[crop["seed"]]
        ripe = self.is_ripe(tile)
        progress = min(crop["days"] / data["growth_days"], 1)
        stage = RIPE_STAGE if ripe else int(progress * RIPE_STAGE)

        image = get_image("assets/crops/" + data["harvest"] + "_" + str(stage) + ".png")
        if image is not None:
            screen.blit(image, rect)
        elif not ripe:
            self.draw_sprout(screen, rect, stage)
        else:
            # until the ripe picture exists, show the vegetable icon on the soil
            icon = get_image("assets/items/" + data["harvest"] + ".png")
            if icon is not None:
                screen.blit(icon, rect)
            else:
                plant = pygame.Rect(0, 0, 20, 20)
                plant.center = rect.center
                pygame.draw.rect(screen, data["ripe_color"], plant)

    def draw(self, screen):
        for (tx, ty), tile in self.soil.items():
            rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            self.draw_soil(screen, rect, tile["watered"])
            if tile["crop"] is not None:
                self.draw_crop(screen, rect, tile)