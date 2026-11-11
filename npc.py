import json
import os
import pygame
from world import TILE_SIZE
from pathfinding import find_path
from assets import load_image

NPC_SPEED = 80        # pixels per second
NPC_SIZE = 24         # size of the colored square used when there is no picture
SPRITE_SIZE = (64, 64)
FEET_OFFSET = 12      # how far below the tile center the feet are, in pixels
SHOW_NAMES = True     # set to False to hide the name above the head


def load_npcs(path):
    """Read the NPC file and return a list of NPC objects."""
    with open(path) as f:
        data = json.load(f)
    return [NPC(entry) for entry in data["npcs"]]


class NPC:
    """A villager who follows a schedule and walks between its spots."""

    def __init__(self, data):
        """Create an NPC standing on the first spot of its schedule.

        The picture is assets/characters/<id>.png, unless the NPC has a
        "sprite" entry in npcs.json. Without a picture, a colored square is used.
        """
        self.id = data["id"]
        self.name = data["name"]
        self.color = tuple(data["color"])
        self.schedule = data["schedule"]  # sorted by hour

        default_path = "assets/characters/" + self.id + ".png"
        self.sprite_path = data.get("sprite", default_path)
        self.has_sprite = os.path.exists(self.sprite_path)
        if not self.has_sprite:
            print("[npc] no picture for " + self.id + ", expected " + self.sprite_path)

        first = self.schedule[0]["tile"]
        self.start_tile = (first[0], first[1])
        self.tile = self.start_tile
        self.pos = self.get_tile_center(self.start_tile)
        self.goal = self.start_tile
        self.path = []

    def get_tile_center(self, tile):
        """Return the pixel position of the center of a tile."""
        center_x = tile[0] * TILE_SIZE + TILE_SIZE // 2
        center_y = tile[1] * TILE_SIZE + TILE_SIZE // 2
        return pygame.Vector2(center_x, center_y)

    def get_scheduled_tile(self, minutes):
        """Return the tile where the schedule says the NPC should be now.

        The last entry whose hour has already passed wins.
        """
        hour = minutes / 60
        tile = self.schedule[0]["tile"]
        for entry in self.schedule:
            if hour >= entry["hour"]:
                tile = entry["tile"]
        return (tile[0], tile[1])

    def go_home(self):
        """Put the NPC back on its first spot of the day (it slept there)."""
        self.tile = self.start_tile
        self.pos = self.get_tile_center(self.start_tile)
        self.goal = self.start_tile
        self.path = []

    def update(self, dt, minutes, world):
        """Check the schedule, compute a new path if the goal changed, then walk."""
        scheduled = self.get_scheduled_tile(minutes)
        if scheduled != self.goal:
            self.goal = scheduled
            self.path = find_path(world, self.tile, scheduled)

        self.walk(dt)
        self.tile = self.compute_tile()

    def walk(self, dt):
        """Move toward the next tile of the path, and remove it once reached."""
        if len(self.path) == 0:
            return

        target = self.get_tile_center(self.path[0])
        to_target = target - self.pos
        distance = to_target.length()
        step = NPC_SPEED * dt

        if distance <= step:
            self.pos = target
            self.path.pop(0)
        else:
            direction = to_target.normalize()
            self.pos = self.pos + direction * step

    def compute_tile(self):
        """Return the tile (column, row) that is under the NPC's center."""
        tile_x = int(self.pos.x // TILE_SIZE)
        tile_y = int(self.pos.y // TILE_SIZE)
        return (tile_x, tile_y)

    def get_feet_y(self):
        """Return the screen height of the NPC's feet, used to draw in depth order."""
        return int(self.pos.y) + FEET_OFFSET

    def get_rect(self):
        """Return the rectangle of the colored square, centered on the NPC's position."""
        rect = pygame.Rect(0, 0, NPC_SIZE, NPC_SIZE)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def draw_picture(self, screen):
        """Draw the NPC's picture with its feet on the ground. Return its rectangle."""
        picture = load_image(self.sprite_path, SPRITE_SIZE, self.color)
        picture_rect = picture.get_rect()
        picture_rect.midbottom = (int(self.pos.x), self.get_feet_y())
        screen.blit(picture, picture_rect)
        return picture_rect

    def draw_square(self, screen):
        """Draw the colored square used when there is no picture. Return its rectangle."""
        rect = self.get_rect()
        pygame.draw.rect(screen, self.color, rect)
        return rect

    def draw(self, screen, font):
        """Draw the NPC (picture or colored square) and its name above it."""
        if self.has_sprite:
            body = self.draw_picture(screen)
        else:
            body = self.draw_square(screen)

        if SHOW_NAMES:
            label = font.render(self.name, True, (255, 255, 255))
            label_x = body.centerx - label.get_width() // 2
            screen.blit(label, (label_x, body.y - 18))