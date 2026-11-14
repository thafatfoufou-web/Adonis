"""Farming: tilled soil, watering, planting, growing and harvesting."""

import os
import pygame
import config
from core.assets import load_image

_images = {}


def get_image(path):
    """Return the tile-sized picture of a file, or None if the file does not exist."""
    if path not in _images:
        if os.path.exists(path):
            size = (config.TILE_SIZE, config.TILE_SIZE)
            _images[path] = load_image(path, size, config.MISSING_IMAGE_COLOR)
        else:
            _images[path] = None
    return _images[path]


class Farm:
    """All the tilled tiles of the farm and the crops growing on them."""

    def __init__(self):
        """Start with no tilled soil. soil maps (tile x, tile y) -> {"watered": bool, "crop": None or {"seed", "days"}}."""
        self.soil = {}

    def is_ripe(self, tile):
        """Return True if the soil tile has a crop that finished growing."""
        crop = tile["crop"]
        if crop is None:
            return False
        return crop["days"] >= config.CROPS[crop["seed"]]["growth_days"]

    def use(self, tx, ty, inventory, world, energy):
        """Do the farming action of the held item on a tile (harvest, till, water or plant).

        Each action costs energy (config.ENERGY_COSTS). Return "tired" if the
        action was possible but energy is too low, otherwise None.
        """
        tile = self.soil.get((tx, ty))
        costs = config.ENERGY_COSTS

        if tile is not None and self.is_ripe(tile):
            if not energy.can_afford(costs["harvest"]):
                return "tired"
            harvest = config.CROPS[tile["crop"]["seed"]]["harvest"]
            if inventory.add_item(harvest):
                tile["crop"] = None
                energy.spend(costs["harvest"])
            return None

        slot = inventory.get_selected()
        if slot is None:
            return None
        item = slot["id"]

        if item == "shovel":
            if tile is None and world.is_tillable(tx, ty):
                if not energy.can_afford(costs["till"]):
                    return "tired"
                self.soil[(tx, ty)] = {"watered": False, "crop": None, "idle": 0}
                energy.spend(costs["till"])

        elif item == "pickaxe":
            if tile is not None:
                # the pickaxe turns the soil back to grass, and destroys the crop on it
                if not energy.can_afford(costs["untill"]):
                    return "tired"
                del self.soil[(tx, ty)]
                energy.spend(costs["untill"])

        elif item == "watering_can":
            if tile is not None and not tile["watered"]:
                if not energy.can_afford(costs["water"]):
                    return "tired"
                tile["watered"] = True
                energy.spend(costs["water"])

        elif item in config.CROPS:
            if tile is not None and tile["crop"] is None:
                if not energy.can_afford(costs["plant"]):
                    return "tired"
                tile["crop"] = {"seed": item, "days": 0}
                inventory.remove_one_selected()
                energy.spend(costs["plant"])

        return None

    def new_day(self):
        """Grow every watered crop by one day, dry the soil, and let unused soil go back to grass.

        A tile counts as used on a day when it has a crop or was watered. After
        config.SOIL_REVERT_DAYS unused days in a row, it turns back into grass.
        """
        for position, tile in list(self.soil.items()):
            used = tile["crop"] is not None or tile["watered"]
            if tile["crop"] is not None and tile["watered"]:
                tile["crop"]["days"] += 1
            tile["watered"] = False

            if used:
                tile["idle"] = 0
            else:
                tile["idle"] = tile.get("idle", 0) + 1
                if tile["idle"] >= config.SOIL_REVERT_DAYS:
                    del self.soil[position]

    def draw_soil(self, screen, rect, watered):
        """Draw one tilled tile: its picture if it exists, otherwise colored soil with furrows."""
        image = get_image(config.SOIL_IMAGES[watered])
        if image is not None:
            screen.blit(image, rect)
            return

        pygame.draw.rect(screen, config.WET_SOIL if watered else config.DRY_SOIL, rect)
        furrow = config.WET_FURROW if watered else config.DRY_FURROW
        for y in (9, 17, 25):
            pygame.draw.line(screen, furrow, (rect.x + 4, rect.y + y), (rect.right - 5, rect.y + y), 2)
        pygame.draw.rect(screen, config.SOIL_EDGE, rect, 1)

    def draw_sprout(self, screen, rect, stage):
        """Draw a small plant made of rectangles; stage 0 is tiny and stage 2 almost grown."""
        stem_height = (5, 9, 13)[stage]
        leaf_width = (3, 4, 5)[stage]
        pairs = (1, 2, 3)[stage]
        x = rect.centerx - 1
        top = rect.bottom - 6 - stem_height

        pygame.draw.rect(screen, config.STEM_COLOR, (x, top, 2, stem_height))
        for i in range(pairs):
            y = top + 1 + i * 4
            pygame.draw.rect(screen, config.LEAF_COLOR, (x - leaf_width, y, leaf_width, 2))
            pygame.draw.rect(screen, config.LEAF_COLOR, (x + 2, y, leaf_width, 2))

    def draw_crop(self, screen, rect, tile):
        """Draw the crop of a tile with the picture of its growth stage, or a placeholder."""
        crop = tile["crop"]
        data = config.CROPS[crop["seed"]]
        ripe = self.is_ripe(tile)
        progress = min(crop["days"] / data["growth_days"], 1)
        stage = config.RIPE_STAGE if ripe else int(progress * config.RIPE_STAGE)

        image = get_image(config.CROPS_DIR + data["harvest"] + "_" + str(stage) + ".png")
        if image is not None:
            screen.blit(image, rect)
        elif not ripe:
            self.draw_sprout(screen, rect, stage)
        else:
            icon = get_image(config.ITEMS_DIR + data["harvest"] + ".png")
            if icon is not None:
                screen.blit(icon, rect)
            else:
                plant = pygame.Rect(0, 0, 20, 20)
                plant.center = rect.center
                pygame.draw.rect(screen, data["ripe_color"], plant)

    def draw(self, screen, camera):
        """Draw every visible tilled tile and its crop."""
        size = config.TILE_SIZE
        screen_rect = screen.get_rect()
        for (tx, ty), tile in self.soil.items():
            rect = pygame.Rect(tx * size - camera.x, ty * size - camera.y, size, size)
            if not rect.colliderect(screen_rect):
                continue
            self.draw_soil(screen, rect, tile["watered"])
            if tile["crop"] is not None:
                self.draw_crop(screen, rect, tile)