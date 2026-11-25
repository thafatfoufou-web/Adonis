"""Villagers that follow a daily schedule and walk between their spots."""

import json
import os
import pygame
import config
from ui import theme
from core.assets import load_image, get_back_path
from world.pathfinding import find_path


def load_npcs(path):
    """Read the NPC file and return a list of NPC objects."""
    with open(path) as f:
        data = json.load(f)
    return [NPC(entry) for entry in data["npcs"]]


class NPC:
    """A villager who follows a schedule and walks between its spots."""

    def __init__(self, data):
        """Create an NPC on the first spot of its schedule.

        The picture is assets/characters/<id>.png unless npcs.json gives a "sprite".
        Without a picture, a colored square is used.
        """
        self.id = data["id"]
        self.name = data["name"]
        self.color = tuple(data["color"])
        self.schedule = data["schedule"]
        # the tile in front of the villager's house door; a schedule spot written "home" means this tile
        home = data.get("home")
        self.home_tile = (home[0], home[1]) if home else self.resolve_tile(self.schedule[0]["tile"])

        default_path = config.CHARACTERS_DIR + self.id + ".png"
        self.sprite_path = data.get("sprite", default_path)
        self.has_sprite = os.path.exists(self.sprite_path)
        if not self.has_sprite:
            print("[npc] no picture for " + self.id + ", expected " + self.sprite_path)

        self.start_tile = self.resolve_tile(self.schedule[0]["tile"])
        self.tile = self.start_tile
        self.pos = self.get_tile_center(self.start_tile)
        self.goal = self.start_tile
        self.path = []
        self.visiting = False    # True while systems/visits.py walks this villager to the player
        self.facing_up = False   # True while walking up the screen: the back picture is drawn
        self.pause_timer = 0     # seconds left standing still (after a chat or a gift)

    def resolve_tile(self, tile):
        """Turn a schedule spot into a (column, row) tuple: "home" means the tile in front of the villager's house."""
        if tile == "home":
            return self.home_tile
        return (tile[0], tile[1])

    def get_tile_center(self, tile):
        """Return the pixel position of the center of a tile."""
        center_x = tile[0] * config.TILE_SIZE + config.TILE_SIZE // 2
        center_y = tile[1] * config.TILE_SIZE + config.TILE_SIZE // 2
        return pygame.Vector2(center_x, center_y)

    def get_scheduled_tile(self, minutes):
        """Return the tile the schedule says the NPC should be on at this time (last passed hour wins)."""
        hour = minutes / 60
        tile = self.schedule[0]["tile"]
        for entry in self.schedule:
            if hour >= entry["hour"]:
                tile = entry["tile"]
        return self.resolve_tile(tile)

    def go_home(self):
        """Put the NPC back on its first spot of the day."""
        self.tile = self.start_tile
        self.pos = self.get_tile_center(self.start_tile)
        self.goal = self.start_tile
        self.path = []
        self.facing_up = False

    def put_on_tile(self, tile):
        """Place the NPC on a tile right away and stop its walk."""
        self.tile = tile
        self.pos = self.get_tile_center(tile)
        self.path = []

    def end_visit(self):
        """Go back to the schedule: the next update walks to wherever the clock says."""
        self.visiting = False
        self.goal = None
        self.path = []

    def pause(self, seconds):
        """Stand still for a few seconds (the clock only runs while the game is not paused by a dialogue)."""
        self.pause_timer = seconds

    def get_hit_rect(self):
        """Return the rectangle (world pixels) of the villager's body, for clicking on them anywhere, not only on their feet."""
        rect = pygame.Rect(0, 0, config.NPC_SPRITE_SIZE[0] * 5 // 8, config.NPC_SPRITE_SIZE[1] * 15 // 16)
        rect.midbottom = (int(self.pos.x), self.get_feet_y())
        return rect

    def update(self, dt, minutes, world):
        """Check the schedule, compute a new path if the goal changed, then walk."""
        if self.pause_timer > 0:
            self.pause_timer -= dt
            self.facing_up = False
            return
        if not self.visiting:
            scheduled = self.get_scheduled_tile(minutes)
            if scheduled != self.goal:
                self.goal = scheduled
                self.path = find_path(world, self.tile, scheduled)

        self.walk(dt)
        self.tile = self.compute_tile()

    def walk(self, dt):
        """Move toward the next tile of the path and drop it once reached."""
        if len(self.path) == 0:
            self.facing_up = False       # standing still: look at the player
            return

        target = self.get_tile_center(self.path[0])
        to_target = target - self.pos
        distance = to_target.length()
        step = config.NPC_SPEED * dt

        # going up the screen shows the back; sideways or down shows the front
        if abs(to_target.y) > abs(to_target.x):
            self.facing_up = to_target.y < 0
        elif abs(to_target.x) > 0:
            self.facing_up = False

        if distance <= step:
            self.pos = target
            self.path.pop(0)
        else:
            direction = to_target.normalize()
            self.pos = self.pos + direction * step

    def compute_tile(self):
        """Return the tile (column, row) under the NPC's center."""
        tile_x = int(self.pos.x // config.TILE_SIZE)
        tile_y = int(self.pos.y // config.TILE_SIZE)
        return (tile_x, tile_y)

    def get_feet_y(self):
        """Return the world height of the NPC's feet, used for depth order."""
        return int(self.pos.y) + config.NPC_FEET_OFFSET

    def get_rect(self):
        """Return the colored square's rectangle, centered on the NPC."""
        rect = pygame.Rect(0, 0, config.NPC_SIZE, config.NPC_SIZE)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def draw_picture(self, screen, camera):
        """Draw the NPC's picture with its feet on the ground and return its rectangle."""
        path = get_back_path(self.sprite_path) if self.facing_up else self.sprite_path
        picture = load_image(path, config.NPC_SPRITE_SIZE, self.color)
        picture_rect = picture.get_rect()
        picture_rect.midbottom = (int(self.pos.x) - camera.x, self.get_feet_y() - camera.y)
        screen.blit(picture, picture_rect)
        return picture_rect

    def draw_square(self, screen, camera):
        """Draw the colored square used without a picture and return its rectangle."""
        rect = self.get_rect().move(-camera.x, -camera.y)
        pygame.draw.rect(screen, self.color, rect)
        return rect

    def draw(self, screen, font, camera):
        """Draw the NPC (picture or square) and its name above it."""
        if self.has_sprite:
            body = self.draw_picture(screen, camera)
        else:
            body = self.draw_square(screen, camera)

        if config.SHOW_NPC_NAMES:
            theme.draw_name_label(screen, font, self.name, (body.centerx, body.y - config.NPC_NAME_OFFSET + 14))
