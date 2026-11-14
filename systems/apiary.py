"""Beehives: placing them, making honey over the days and collecting it."""

import pygame
import config
from systems.farm import get_image


class Apiary:
    """All the beehives of the farm.

    hives maps (tile x, tile y) -> {"days": days of work since the last honey}.
    """

    def __init__(self, world):
        """Start with no hive. The world is told about each hive so that it blocks the way."""
        self.world = world
        self.hives = {}

    def has_hive(self, tx, ty):
        """Return True if there is a beehive on this tile."""
        return (tx, ty) in self.hives

    def get_product(self, story):
        """Return the item a hive makes now: the harmless honey once the mystery is solved."""
        if story.has(config.HIVE_SAFE_FLAG):
            return config.HIVE_SAFE_PRODUCT
        return config.HIVE_PRODUCT

    def has_flowers_near(self, tx, ty):
        """Return True if there are enough flowers around a tile for bees to work."""
        flowers = self.world.count_flowers(tx, ty, config.HIVE_FLOWER_RADIUS)
        return flowers >= config.HIVE_MIN_FLOWERS

    def is_ready(self, hive):
        """Return True if the hive made honey that can be collected."""
        return hive["days"] >= config.HIVE_HONEY_DAYS

    def use(self, tx, ty, inventory, energy, story, taken):
        """Collect the honey of the hive on a tile, or place the held beehive there.

        taken = tiles where nothing can be placed (soil, villagers, the player).
        Return what happened: "collected", "not_ready", "no_flowers", "picked_up",
        "placed", "placed_no_flowers", "bad_spot", "full" or "tired". Return None if this
        tile and the held item have nothing to do with beehives.
        """
        hive = self.hives.get((tx, ty))
        if hive is not None:
            # the pickaxe takes an empty hive back; anything else (or a hive with honey) collects the honey
            slot = inventory.get_selected()
            holding_pickaxe = slot is not None and slot["id"] == "pickaxe"
            if holding_pickaxe and not self.is_ready(hive):
                return self.pick_up((tx, ty), inventory, energy, story)
            return self.collect((tx, ty), hive, inventory, energy, story)

        slot = inventory.get_selected()
        if slot is None or slot["id"] != "beehive":
            return None
        return self.place(tx, ty, inventory, energy, story, taken)

    def collect(self, tile, hive, inventory, energy, story):
        """Take one honey out of a hive if it is ready. The hive starts working again."""
        if not self.is_ready(hive):
            if self.has_flowers_near(*tile):
                return "not_ready"
            return "no_flowers"

        product = self.get_product(story)
        if not inventory.can_add(product):
            return "full"
        cost = config.ENERGY_COSTS["harvest"]
        if not energy.can_afford(cost):
            return "tired"

        inventory.add_item(product)
        energy.spend(cost)
        hive["days"] = 0
        story.set("first_honey")
        return "collected"

    def pick_up(self, tile, inventory, energy, story):
        """Take a hive back into the inventory. Its progress is lost."""
        if not inventory.can_add("beehive"):
            return "full"
        cost = config.ENERGY_COSTS["pickup_hive"]
        if not energy.can_afford(cost):
            return "tired"

        inventory.add_item("beehive")
        energy.spend(cost)
        del self.hives[tile]
        self.world.remove_blocker(*tile)
        if len(self.hives) == 0:
            story.clear("hive_built")
            story.clear("hive_no_flowers")
        return "picked_up"

    def place(self, tx, ty, inventory, energy, story, taken):
        """Put the held beehive on a free patch of grass."""
        if not self.world.is_tillable(tx, ty) or (tx, ty) in taken:
            return "bad_spot"
        cost = config.ENERGY_COSTS["place_hive"]
        if not energy.can_afford(cost):
            return "tired"

        inventory.remove_one_selected()
        energy.spend(cost)
        self.hives[(tx, ty)] = {"days": 0}
        self.world.add_blocker(tx, ty)
        story.set("hive_built")
        if self.has_flowers_near(tx, ty):
            story.clear("hive_no_flowers")
            return "placed"
        story.set("hive_no_flowers")      # Jonas will tell the player to move it near flowers
        return "placed_no_flowers"

    def new_day(self):
        """Every hive with flowers around works one more day, until its honey is ready."""
        for (tx, ty), hive in self.hives.items():
            if self.has_flowers_near(tx, ty):
                hive["days"] = min(hive["days"] + 1, config.HIVE_HONEY_DAYS)

    def draw_ready_marker(self, screen, rect):
        """Draw a golden circle above a hive whose honey is ready (it bobs up and down)."""
        bob = (pygame.time.get_ticks() // 300) % 2 * 2
        center = (rect.centerx, rect.y + 4 + bob)
        pygame.draw.circle(screen, config.HIVE_OUTLINE, center, 7)
        pygame.draw.circle(screen, config.HONEY_COLOR, center, 5)
        pygame.draw.circle(screen, (255, 245, 190), (center[0] - 1, center[1] - 2), 2)

    def draw(self, screen, camera):
        """Draw every visible hive with your picture, and a golden circle when its honey is ready."""
        size = config.TILE_SIZE
        screen_rect = screen.get_rect()
        image = get_image(config.HIVE_IMAGE)
        for (tx, ty), hive in self.hives.items():
            rect = pygame.Rect(tx * size - camera.x, ty * size - camera.y, size, size)
            if not rect.colliderect(screen_rect):
                continue

            if image is not None:
                screen.blit(image, rect)
            else:
                pygame.draw.rect(screen, config.HIVE_WOOD, rect.inflate(-8, -8))   # the picture is missing
            if self.is_ready(hive):
                self.draw_ready_marker(screen, rect)
