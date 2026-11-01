import json
import pygame
from assets import load_image

TILE_SIZE = 32

# used for tiles outside the map: always a wall
OUTSIDE_TILE = {"name": "outside", "color": [0, 0, 0], "solid": True}

# used for a number in the map that is not in tiles.json: bright pink, solid
UNKNOWN_TILE = {"name": "unknown", "color": [255, 0, 255], "solid": True}


class TileMap:
    """The grid of tiles of one map, with the rules of each kind of tile."""

    def __init__(self, map_path, tiles_path):
        """Read the map (numbers separated by spaces) and the tile definitions."""
        self.rows = []
        with open(map_path) as f:
            for line in f:
                if line.strip():  # skip empty lines
                    self.rows.append(line.split())

        with open(tiles_path) as f:
            self.tiles = json.load(f)

        # tile id -> image already scaled to the tile size
        self.surfaces = {}

    def get_tile(self, tx, ty):
        """Return the tile id at a position, or None if it is outside the map."""
        if ty < 0 or ty >= len(self.rows):
            return None
        if tx < 0 or tx >= len(self.rows[ty]):
            return None
        return self.rows[ty][tx]

    def get_definition(self, tile_id):
        """Return the definition (a dictionary from tiles.json) of a tile id."""
        if tile_id is None:
            return OUTSIDE_TILE
        definition = self.tiles.get(tile_id)
        if definition is None:
            return UNKNOWN_TILE
        return definition

    def get_definition_at(self, tx, ty):
        """Return the definition of the tile at a position."""
        tile_id = self.get_tile(tx, ty)
        return self.get_definition(tile_id)

    def is_solid(self, tx, ty):
        """Return True if the player cannot walk on this tile."""
        definition = self.get_definition_at(tx, ty)
        return definition.get("solid", False)

    def is_tillable(self, tx, ty):
        """Return True if the hoe can turn this tile into soil."""
        definition = self.get_definition_at(tx, ty)
        return definition.get("tillable", False)

    def get_action(self, tx, ty):
        """Return the action of this tile ('shop', 'sell'...) or None if it has none."""
        definition = self.get_definition_at(tx, ty)
        return definition.get("action")

    def get_surface(self, tile_id):
        """Return the picture of a tile id, loaded once and scaled to TILE_SIZE."""
        if tile_id in self.surfaces:
            return self.surfaces[tile_id]

        definition = self.get_definition(tile_id)
        size = (TILE_SIZE, TILE_SIZE)
        path = definition.get("image")
        surface = load_image(path, size, definition["color"])

        self.surfaces[tile_id] = surface
        return surface

    def draw(self, screen):
        """Draw every tile of the map."""
        for y, row in enumerate(self.rows):
            for x, tile_id in enumerate(row):
                surface = self.get_surface(tile_id)
                screen.blit(surface, (x * TILE_SIZE, y * TILE_SIZE))

    def collides(self, rect):
        """Return True if a rectangle touches at least one solid tile."""
        # first and last tile covered by the rectangle
        left = rect.left // TILE_SIZE
        right = (rect.right - 1) // TILE_SIZE
        top = rect.top // TILE_SIZE
        bottom = (rect.bottom - 1) // TILE_SIZE

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if self.is_solid(tx, ty):
                    return True
        return False