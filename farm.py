import pygame
from world import TILE_SIZE

# key = the seed item, value = what the crop needs and gives
CROPS = {
    "turnip_seeds": {
        "growth_days": 4,
        "harvest": "turnip",
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

DRY_SOIL = (110, 75, 40)
WET_SOIL = (70, 45, 25)
GROWING_COLOR = (80, 180, 80)


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

        # 2. hoe: grass becomes tilled soil
        if item == "hoe":
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

    def draw(self, screen):
        for (tx, ty), tile in self.soil.items():
            rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            color = WET_SOIL if tile["watered"] else DRY_SOIL
            pygame.draw.rect(screen, color, rect)

            crop = tile["crop"]
            if crop is not None:
                data = CROPS[crop["seed"]]
                progress = min(crop["days"] / data["growth_days"], 1)
                size = 6 + int(progress * 18)  # grows from 6 to 24 px
                plant = pygame.Rect(0, 0, size, size)
                plant.center = rect.center
                ripe = self.is_ripe(tile)
                pygame.draw.rect(screen, data["ripe_color"] if ripe else GROWING_COLOR, plant)