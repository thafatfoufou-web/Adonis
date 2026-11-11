import os
import pygame

# set to True to see the hitboxes of the buildings (red), to adjust them
SHOW_HITBOXES = False


class Building:
    """A big picture (shop, house...) placed on the map, with its own hitbox and doors.

    The picture is drawn at its real size, never scaled. The hitbox is the part
    the player cannot walk through, and the doors are tiles that start an action.
    """

    def __init__(self, data, tile_size):
        """Read one building from buildings.json and load its picture."""
        self.name = data.get("name", "building")
        self.tile_size = tile_size

        # the picture's top left corner, in pixels
        self.x = data["tile"][0] * tile_size
        self.y = data["tile"][1] * tile_size

        # the hitbox is given inside the picture: [x, y, width, height] in pixels
        box = data["hitbox"]
        self.hitbox = pygame.Rect(self.x + box[0], self.y + box[1], box[2], box[3])

        # door tiles are given relative to the picture's top left tile
        self.doors = {}
        for door in data.get("doors", []):
            door_x = data["tile"][0] + door["tile"][0]
            door_y = data["tile"][1] + door["tile"][1]
            self.doors[(door_x, door_y)] = door["action"]

        self.image = self.load_picture(data["image"])

    def load_picture(self, path):
        """Load the picture at its real size. Return None if it cannot be loaded."""
        if not os.path.exists(path):
            print("[buildings] missing image: " + path + " (a gray box is used)")
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            print("[buildings] cannot read image: " + path + " (a gray box is used)")
            return None

    def get_base_y(self):
        """Return the screen height of the bottom of the hitbox, used for depth order."""
        return self.hitbox.bottom

    def get_action(self, tx, ty):
        """Return the action of the door on this tile, or None if there is none."""
        return self.doors.get((tx, ty))

    def contains_point(self, pos):
        """Return True if pos (a position on the screen) is on a visible pixel of the building."""
        if self.image is None:
            return self.hitbox.collidepoint(pos)
        x = pos[0] - self.x
        y = pos[1] - self.y
        if x < 0 or y < 0 or x >= self.image.get_width() or y >= self.image.get_height():
            return False
        return self.image.get_at((x, y)).a > 0

    def get_click_door(self, pos, from_tile):
        """If pos is on the building, return its door tile nearest to from_tile.

        This lets the player click anywhere on the building, not only on the door
        tiles. Return None if pos is not on the building or it has no door.
        """
        if not self.doors or not self.contains_point(pos):
            return None
        return min(self.doors, key=lambda door: max(abs(door[0] - from_tile[0]),
                                                    abs(door[1] - from_tile[1])))

    def overlaps_tile(self, tx, ty):
        """Return True if the hitbox touches the tile (tx, ty)."""
        tile_rect = pygame.Rect(tx * self.tile_size, ty * self.tile_size,
                                self.tile_size, self.tile_size)
        return self.hitbox.colliderect(tile_rect)

    def draw(self, screen):
        """Draw the picture (or a gray box on the hitbox if there is no picture)."""
        if self.image is None:
            pygame.draw.rect(screen, (110, 110, 120), self.hitbox)
        else:
            screen.blit(self.image, (self.x, self.y))

        if SHOW_HITBOXES:
            pygame.draw.rect(screen, (255, 0, 0), self.hitbox, 2)