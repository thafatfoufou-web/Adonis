"""The tile grid of a map: tile rules, collisions and drawing."""

import json
import pygame
import config
from core.assets import load_image
from world.buildings import Building


class TileMap:
    """The grid of tiles of one map, with the rules of each kind of tile."""

    def __init__(self, map_path, tiles_path, buildings_path=None):
        """Read the map file, the tile definitions and the buildings, and find the depth-sorted objects."""
        self.rows = []
        with open(map_path) as f:
            for line in f:
                if line.strip():
                    self.rows.append(line.split())

        with open(tiles_path) as f:
            self.tiles = json.load(f)

        self.surfaces = {}
        self.hitboxes = {}

        self.blockers = set()   # tiles made solid by things placed later, like beehives
        self.moving_obstacles = []   # rectangles of things that move (cows), set by main.py every frame

        self.story = None            # set by main.py: buildings with a "requires" flag only exist once it is set
        self.all_buildings = []
        if buildings_path is not None:
            with open(buildings_path) as f:
                building_data = json.load(f)
            for entry in building_data["buildings"]:
                self.all_buildings.append(Building(entry, config.TILE_SIZE))

        self.objects = []
        for y, row in enumerate(self.rows):
            for x, tile_id in enumerate(row):
                if self.get_definition(tile_id).get("object", False):
                    self.objects.append((x, y, tile_id))

    @property
    def buildings(self):
        """Return the buildings that exist right now (the barn only appears once the barn quest is done)."""
        return [building for building in self.all_buildings
                if building.requires is None or (self.story is not None and self.story.has(building.requires))]

    @property
    def pixel_size(self):
        """Return the size of the whole map in pixels: (width, height)."""
        width = max(len(row) for row in self.rows)
        return width * config.TILE_SIZE, len(self.rows) * config.TILE_SIZE

    def get_tile(self, tx, ty):
        """Return the tile id at a position, or None if it is outside the map."""
        if ty < 0 or ty >= len(self.rows):
            return None
        if tx < 0 or tx >= len(self.rows[ty]):
            return None
        return self.rows[ty][tx]

    def add_blocker(self, tx, ty):
        """Make a tile solid (for example because a beehive was placed on it)."""
        self.blockers.add((tx, ty))

    def remove_blocker(self, tx, ty):
        """Make a tile walkable again (for example because a beehive was picked up)."""
        self.blockers.discard((tx, ty))

    def get_definition(self, tile_id):
        """Return the tiles.json definition of a tile id (a wall for outside, pink for unknown ids)."""
        if tile_id is None:
            return config.OUTSIDE_TILE
        definition = self.tiles.get(tile_id)
        if definition is None:
            return config.UNKNOWN_TILE
        return definition

    def get_definition_at(self, tx, ty):
        """Return the definition of the tile at a position."""
        tile_id = self.get_tile(tx, ty)
        return self.get_definition(tile_id)

    def is_solid(self, tx, ty):
        """Return True if this tile is solid or touched by a building hitbox (used by NPC paths)."""
        if (tx, ty) in self.blockers:
            return True
        definition = self.get_definition_at(tx, ty)
        if definition.get("solid", False):
            return True
        for building in self.buildings:
            if building.overlaps_tile(tx, ty):
                return True
        return False

    def is_tillable(self, tx, ty):
        """Return True if the shovel can turn this tile into soil."""
        if (tx, ty) in self.blockers:
            return False
        definition = self.get_definition_at(tx, ty)
        return definition.get("tillable", False)

    def count_flowers(self, tx, ty, radius):
        """Count the flower tiles ("flower": true in tiles.json) in the square of the given radius around a tile."""
        count = 0
        for y in range(ty - radius, ty + radius + 1):
            for x in range(tx - radius, tx + radius + 1):
                if self.get_definition_at(x, y).get("flower", False):
                    count += 1
        return count
    
    def get_building_click_tile(self, pos, from_tile):
        """Return the door tile to use if the world position pos is on a building, otherwise None."""
        for building in self.buildings:
            door = building.get_click_door(pos, from_tile)
            if door is not None:
                return door
        return None

    def get_action(self, tx, ty):
        """Return the action of this tile or of a building door on it ('shop', 'sell', 'sleep'), or None."""
        definition = self.get_definition_at(tx, ty)
        action = definition.get("action")
        if action is not None:
            return action
        for building in self.buildings:
            door_action = building.get_action(tx, ty)
            if door_action is not None:
                return door_action
        return None

    def get_surface(self, tile_id):
        """Return the picture of a tile id, loaded once and scaled to the tile size."""
        if tile_id in self.surfaces:
            return self.surfaces[tile_id]

        definition = self.get_definition(tile_id)
        size = (config.TILE_SIZE, config.TILE_SIZE)
        path = definition.get("image")
        surface = load_image(path, size, definition["color"])

        self.surfaces[tile_id] = surface
        return surface

    def draw(self, screen, camera):
        """Draw the ground and every flat tile on screen.

        Objects ("object": true in tiles.json) only get their ground here; their
        picture is drawn by draw_objects. A tile can choose another ground with
        "ground": "5", or no ground with "ground": null.
        """
        size = config.TILE_SIZE
        first_col, first_row, last_col, last_row = camera.visible_tiles(size)
        for y in range(max(first_row, 0), min(last_row, len(self.rows))):
            row = self.rows[y]
            for x in range(max(first_col, 0), min(last_col, len(row))):
                tile_id = row[x]
                position = (x * size - camera.x, y * size - camera.y)
                definition = self.get_definition(tile_id)
                ground_id = definition.get("ground", config.GROUND_TILE)
                if ground_id is not None and ground_id != tile_id:
                    screen.blit(self.get_surface(ground_id), position)
                if not definition.get("object", False):
                    screen.blit(self.get_surface(tile_id), position)

    def draw_objects(self, screen, camera, player_bottom, behind):
        """Draw objects and buildings in depth order with the player.

        behind=True draws those the player is in front of (call before drawing the player).
        behind=False draws those in front of the player (call after).
        """
        size = config.TILE_SIZE
        for x, y, tile_id in self.objects:
            base_y = y * size + self.get_hitbox(tile_id).bottom
            player_in_front = base_y <= player_bottom
            if player_in_front == behind:
                screen.blit(self.get_surface(tile_id), (x * size - camera.x, y * size - camera.y))

        for building in self.buildings:
            player_in_front = building.get_base_y() <= player_bottom
            if player_in_front == behind:
                building.draw(screen, camera)

    def get_hitbox(self, tile_id):
        """Return the solid part of a tile as a Rect relative to the tile.

        "hitbox" in tiles.json can be missing (whole tile), [x, y, width, height],
        or "auto" (the box around the visible pixels of the picture).
        """
        if tile_id in self.hitboxes:
            return self.hitboxes[tile_id]

        size = config.TILE_SIZE
        full = pygame.Rect(0, 0, size, size)
        setting = self.get_definition(tile_id).get("hitbox")

        if setting is None:
            hitbox = full
        elif setting == "auto":
            surface = self.get_surface(tile_id)
            hitbox = surface.get_bounding_rect(min_alpha=config.AUTO_HITBOX_MIN_ALPHA)
            if hitbox.width == 0 or hitbox.height == 0:
                hitbox = full
        else:
            hitbox = pygame.Rect(setting[0], setting[1], setting[2], setting[3])

        self.hitboxes[tile_id] = hitbox
        return hitbox

    def get_depth_items(self, screen, camera):
        """Return [(base_y, draw_function)] for every object and building on screen, to be sorted with the characters."""
        size = config.TILE_SIZE
        first_col, first_row, last_col, last_row = camera.visible_tiles(size)
        items = []
        for x, y, tile_id in self.objects:
            if x < first_col - 1 or x > last_col or y < first_row - 1 or y > last_row + 1:
                continue
            base_y = y * size + self.get_hitbox(tile_id).bottom
            surface = self.get_surface(tile_id)
            position = (x * size - camera.x, y * size - camera.y)
            items.append((base_y, lambda s=surface, p=position: screen.blit(s, p)))
        for building in self.buildings:
            items.append((building.get_base_y(), lambda b=building: b.draw(screen, camera)))
        return items

    def collides(self, rect):
        """Return True if a rectangle touches the solid part of a solid tile or a building."""
        size = config.TILE_SIZE
        left = rect.left // size
        right = (rect.right - 1) // size
        top = rect.top // size
        bottom = (rect.bottom - 1) // size

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if (tx, ty) in self.blockers:
                    return True
                if not self.get_definition_at(tx, ty).get("solid", False):
                    continue
                hitbox = self.get_hitbox(self.get_tile(tx, ty)).move(tx * size, ty * size)
                if rect.colliderect(hitbox):
                    return True

        for building in self.buildings:
            if rect.colliderect(building.hitbox):
                return True
        for obstacle in self.moving_obstacles:
            if rect.colliderect(obstacle):
                return True
        return False