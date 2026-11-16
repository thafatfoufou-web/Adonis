"""Things lying on the ground that the player picks up (wood for the barn, field flowers...).

They are listed in data/pickups.json. Each one belongs to a quest: it is only visible while
that quest is active, and once picked up it is gone for good (the story flag "picked_<id>").
"""

import json
import pygame
import config
from core.assets import load_image
from systems.items import ITEMS


class Pickups:
    """The pickups of the whole game."""

    def __init__(self, path):
        """Read the pickup file."""
        with open(path, encoding="utf-8") as file:
            self.items = json.load(file)["pickups"]

    def is_visible(self, pickup, story, quests):
        """Return True if the pickup can be seen right now."""
        return quests.status(pickup["quest"]) == "active" and not story.has("picked_" + pickup["id"])

    def at(self, tx, ty, story, quests):
        """Return the visible pickup on this tile, or None."""
        for pickup in self.items:
            if tuple(pickup["tile"]) == (tx, ty) and self.is_visible(pickup, story, quests):
                return pickup
        return None

    def pick(self, tx, ty, inventory, story, quests):
        """Pick up what lies on the tile. Return (message, worked)."""
        pickup = self.at(tx, ty, story, quests)
        name = ITEMS[pickup["item"]]["name"].lower()
        if not inventory.can_add(pickup["item"]):
            return ("Your hotbar is full.", False)
        inventory.add_item(pickup["item"])
        story.set("picked_" + pickup["id"])
        quests.notify("pickup", item=pickup["item"])
        return ("You picked up " + name + ".", True)

    def draw(self, screen, camera, story, quests):
        """Draw the visible pickups on the ground."""
        size = config.TILE_SIZE
        screen_rect = screen.get_rect()
        for pickup in self.items:
            if not self.is_visible(pickup, story, quests):
                continue
            tx, ty = pickup["tile"]
            rect = pygame.Rect(tx * size - camera.x, ty * size - camera.y, size, size)
            if not rect.colliderect(screen_rect):
                continue
            data = ITEMS[pickup["item"]]
            picture = load_image(data["icon"], (size, size), data["color"])
            screen.blit(picture, rect)
