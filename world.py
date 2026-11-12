import json
import pygame
from assets import load_image
from buildings import Building

TILE_SIZE = 32
GROUND_TILE = "1"

# used for tiles outside the map: always a wall
OUTSIDE_TILE = {"name": "outside", "color": [0, 0, 0], "solid": True}

# used for a number in the map that is not in tiles.json: bright pink, solid
UNKNOWN_TILE = {"name": "unknown", "color": [255, 0, 255], "solid": True}


class TileMap:
    """The grid of tiles of one map, with the rules of each kind of tile."""

    def __init__(self, map_path, tiles_path, buildings_path=None):
        """Read the map (numbers separated by spaces), the tile definitions and the buildings."""
        self.rows = []
        with open(map_path) as f:
            for line in f:
                if line.strip():  # skip empty lines
                    self.rows.append(line.split())

        with open(tiles_path) as f:
            self.tiles = json.load(f)

        # tile id -> image already scaled to the tile size
        self.surfaces = {}

        # tile id -> hitbox inside the tile, as a Rect relative to the tile
        self.hitboxes = {}

        # the big pictures placed on the map (shop, houses...), from buildings.json
        self.buildings = []
        if buildings_path is not None:
            with open(buildings_path) as f:
                building_data = json.load(f)
            for entry in building_data["buildings"]:
                self.buildings.append(Building(entry, TILE_SIZE))

        # the tiles drawn in depth order with the player (bushes, fences...):
        # a list of (tile x, tile y, tile id), found once at the start
        self.objects = []
        for y, row in enumerate(self.rows):
            for x, tile_id in enumerate(row):
                if self.get_definition(tile_id).get("object", False):
                    self.objects.append((x, y, tile_id))

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
        if definition.get("solid", False):
            return True
        # a tile touched by the hitbox of a building is solid too (used by the NPCs' paths)
        for building in self.buildings:
            if building.overlaps_tile(tx, ty):
                return True
        return False

    def is_tillable(self, tx, ty):
        """Return True if the shovel can turn this tile into soil."""
        definition = self.get_definition_at(tx, ty)
        return definition.get("tillable", False)

    def get_building_click_tile(self, pos, from_tile):
        """If pos (a position on the screen) is on a building, return the door tile to use.

        Return None if the mouse is not on a building.
        """
        for building in self.buildings:
            door = building.get_click_door(pos, from_tile)
            if door is not None:
                return door
        return None

    def get_action(self, tx, ty):
        """Return the action of this tile ('shop', 'sell'...) or None if it has none."""
        definition = self.get_definition_at(tx, ty)
        action = definition.get("action")
        if action is not None:
            return action
        # no action on the tile itself: maybe it is the door of a building
        for building in self.buildings:
            door_action = building.get_action(tx, ty)
            if door_action is not None:
                return door_action
        return None

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
        """Draw the ground and every flat tile.

        Objects ("object": true in tiles.json) only get their ground here.
        Their picture is drawn by draw_objects, in order with the player.
        A tile can choose another ground with "ground": "5" in tiles.json,
        or no ground at all with "ground": null.
        """
        for y, row in enumerate(self.rows):
            for x, tile_id in enumerate(row):
                position = (x * TILE_SIZE, y * TILE_SIZE)
                definition = self.get_definition(tile_id)
                ground_id = definition.get("ground", GROUND_TILE)
                if ground_id is not None and ground_id != tile_id:
                    screen.blit(self.get_surface(ground_id), position)
                if not definition.get("object", False):
                    screen.blit(self.get_surface(tile_id), position)

    def draw_objects(self, screen, player_bottom, behind):
        """Draw the objects, in depth order with the player.

        An object counts as "lower" on the screen when the bottom of its
        hitbox is lower than the player's feet (player_bottom).
        behind=True: draw the objects the player is in front of (call it
        before drawing the player).
        behind=False: draw the objects that are in front of the player
        (call it after drawing the player).
        """
        for x, y, tile_id in self.objects:
            base_y = y * TILE_SIZE + self.get_hitbox(tile_id).bottom
            player_in_front = base_y <= player_bottom
            if player_in_front == behind:
                screen.blit(self.get_surface(tile_id), (x * TILE_SIZE, y * TILE_SIZE))

        # the buildings follow the same rule, with the bottom of their hitbox
        for building in self.buildings:
            player_in_front = building.get_base_y() <= player_bottom
            if player_in_front == behind:
                building.draw(screen)

    def get_hitbox(self, tile_id):
        """Return the solid part of a tile as a Rect relative to the tile.

        In tiles.json, "hitbox" can be:
          - missing: the whole tile is solid
          - [x, y, width, height]: this rectangle, in pixels inside the 32x32 tile
          - "auto": the box around the visible pixels of the picture
        """
        if tile_id in self.hitboxes:
            return self.hitboxes[tile_id]

        full = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        setting = self.get_definition(tile_id).get("hitbox")

        if setting is None:
            hitbox = full
        elif setting == "auto":
            surface = self.get_surface(tile_id)
            # ignore faint pixels (soft shadows), keep the solid-looking ones
            hitbox = surface.get_bounding_rect(min_alpha=128)
            if hitbox.width == 0 or hitbox.height == 0:
                hitbox = full
        else:
            hitbox = pygame.Rect(setting[0], setting[1], setting[2], setting[3])

        self.hitboxes[tile_id] = hitbox
        return hitbox

    def collides(self, rect):
        """Return True if a rectangle touches the solid part of a solid tile or a building."""
        # first and last tile covered by the rectangle
        left = rect.left // TILE_SIZE
        right = (rect.right - 1) // TILE_SIZE
        top = rect.top // TILE_SIZE
        bottom = (rect.bottom - 1) // TILE_SIZE

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if not self.get_definition_at(tx, ty).get("solid", False):
                    continue
                # move the tile's hitbox to its place in the world
                hitbox = self.get_hitbox(self.get_tile(tx, ty)).move(tx * TILE_SIZE, ty * TILE_SIZE)
                if rect.colliderect(hitbox):
                    return True

        # the hitboxes of the buildings
        for building in self.buildings:
            if rect.colliderect(building.hitbox):
                return True
        return False