import json
import pygame
from world import TILE_SIZE
from pathfinding import find_path

NPC_SPEED = 80   # pixels per second
NPC_SIZE = 24


def load_npcs(path):
    """Read the NPC file and return a list of NPC objects."""
    with open(path) as f:
        data = json.load(f)
    return [NPC(entry) for entry in data["npcs"]]


class NPC:
    """A villager who follows a schedule and walks between its spots."""

    def __init__(self, data):
        """Create an NPC standing on the first spot of its schedule."""
        self.id = data["id"]
        self.name = data["name"]
        self.color = tuple(data["color"])
        self.schedule = data["schedule"]  # sorted by hour

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

    def get_rect(self):
        """Return the rectangle of the NPC, centered on its pixel position."""
        rect = pygame.Rect(0, 0, NPC_SIZE, NPC_SIZE)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def draw(self, screen, font):
        """Draw the NPC as a colored square with its name above."""
        rect = self.get_rect()
        pygame.draw.rect(screen, self.color, rect)
        label = font.render(self.name, True, (255, 255, 255))
        label_x = rect.centerx - label.get_width() // 2
        screen.blit(label, (label_x, rect.y - 18))