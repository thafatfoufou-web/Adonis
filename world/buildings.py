"""Big pictures placed on the map (shop, house) with a hitbox and doors."""

import os
import pygame
import config


class Building:
    """A building drawn at its real size, with a hitbox the player cannot cross and door tiles that start actions."""

    def __init__(self, data, tile_size):
        """Read one building entry of buildings.json and load its picture."""
        self.name = data.get("name", "building")
        self.tile_size = tile_size

        self.x = data["tile"][0] * tile_size
        self.y = data["tile"][1] * tile_size

        box = data["hitbox"]
        self.hitbox = pygame.Rect(self.x + box[0], self.y + box[1], box[2], box[3])

        self.doors = {}
        for door in data.get("doors", []):
            door_x = data["tile"][0] + door["tile"][0]
            door_y = data["tile"][1] + door["tile"][1]
            self.doors[(door_x, door_y)] = door["action"]

        self.image = self.load_picture(data["image"])

    def load_picture(self, path):
        """Load the picture at its real size, or return None if it is missing or unreadable."""
        if not os.path.exists(path):
            print("[buildings] missing image: " + path + " (a gray box is used)")
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            print("[buildings] cannot read image: " + path + " (a gray box is used)")
            return None

    def get_base_y(self):
        """Return the world height of the bottom of the hitbox, used for depth order."""
        return self.hitbox.bottom

    def get_action(self, tx, ty):
        """Return the action of the door on this tile, or None."""
        return self.doors.get((tx, ty))

    def contains_point(self, pos):
        """Return True if the world position pos is on a visible pixel of the building."""
        if self.image is None:
            return self.hitbox.collidepoint(pos)
        x = pos[0] - self.x
        y = pos[1] - self.y
        if x < 0 or y < 0 or x >= self.image.get_width() or y >= self.image.get_height():
            return False
        return self.image.get_at((x, y)).a > 0

    def get_click_door(self, pos, from_tile):
        """Return the door tile nearest to from_tile if pos is on the building, otherwise None."""
        if not self.doors or not self.contains_point(pos):
            return None
        return min(self.doors, key=lambda door: max(abs(door[0] - from_tile[0]),
                                                    abs(door[1] - from_tile[1])))

    def overlaps_tile(self, tx, ty):
        """Return True if the hitbox touches the tile (tx, ty)."""
        tile_rect = pygame.Rect(tx * self.tile_size, ty * self.tile_size,
                                self.tile_size, self.tile_size)
        return self.hitbox.colliderect(tile_rect)

    def draw(self, screen, camera):
        """Draw the picture, or a gray box on the hitbox if there is none, plus the hitbox if enabled."""
        if self.image is None:
            pygame.draw.rect(screen, config.BUILDING_FALLBACK_COLOR, self.hitbox.move(-camera.x, -camera.y))
        else:
            screen.blit(self.image, (self.x - camera.x, self.y - camera.y))

        if config.SHOW_BUILDING_HITBOXES:
            pygame.draw.rect(screen, config.BUILDING_HITBOX_COLOR, self.hitbox.move(-camera.x, -camera.y), 2)
