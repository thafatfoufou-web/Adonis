"""Cows: they wander inside their pen and give one milk a day."""

import os
import random
import pygame
import config
from core.assets import load_image


class Cow:
    """A cow that walks tile by tile inside config.COW_PEN and can be milked once a day."""

    def __init__(self, tile):
        """Create a cow resting on a tile. It starts with milk ready."""
        self.tile = tile
        self.pos = self.get_tile_center(tile)
        self.target = None                    # tile the cow is walking to, or None when it rests
        self.wait = random.uniform(*config.COW_WAIT)
        self.facing_left = random.random() < 0.5
        self.milk_ready = True
        self.has_sprite = os.path.exists(config.COW_SPRITE)

    def get_tile_center(self, tile):
        """Return the pixel position of the center of a tile."""
        size = config.TILE_SIZE
        return pygame.Vector2(tile[0] * size + size // 2, tile[1] * size + size // 2)

    def get_hitbox_at(self, center):
        """Return the solid feet box the cow would have with its tile center at center."""
        box = pygame.Rect(0, 0, *config.COW_HITBOX)
        box.midbottom = (int(center.x), int(center.y) + config.COW_FEET_OFFSET)
        return box

    def get_hitbox(self):
        """Return the solid feet box of the cow (the player cannot walk through it)."""
        return self.get_hitbox_at(self.pos)

    def get_feet_y(self):
        """Return the world height of the cow's feet, used for depth order."""
        return int(self.pos.y) + config.COW_FEET_OFFSET

    def get_body_rect(self):
        """Return the rectangle the whole cow covers, used for clicking and drawing."""
        body = pygame.Rect(0, 0, *config.COW_SIZE)
        body.midbottom = (int(self.pos.x), self.get_feet_y())
        return body

    def is_on_tile(self, tx, ty):
        """Return True if the cow covers part of tile (tx, ty), so a click there reaches it."""
        size = config.TILE_SIZE
        return self.get_body_rect().colliderect(pygame.Rect(tx * size, ty * size, size, size))

    def is_free(self, tile, world, blocked, player_rect, herd):
        """Return True if the cow may step on this tile: inside the pen, free and not next to the player."""
        x0, y0, x1, y1 = config.COW_PEN
        if not (x0 <= tile[0] <= x1 and y0 <= tile[1] <= y1):
            return False
        if world.is_solid(*tile) or tile in blocked:
            return False
        for other in herd:
            if other is not self and (other.tile == tile or other.target == tile):
                return False
        box = self.get_hitbox_at(self.get_tile_center(tile))
        return not player_rect.inflate(16, 16).colliderect(box)

    def choose_target(self, world, blocked, player_rect, herd):
        """Pick a random free neighbor tile to walk to, if there is one."""
        steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(steps)
        for step_x, step_y in steps:
            tile = (self.tile[0] + step_x, self.tile[1] + step_y)
            if self.is_free(tile, world, blocked, player_rect, herd):
                self.target = tile
                return

    def walk(self, dt, player_rect):
        """Move toward the target tile. The cow waits if the player stands in its way."""
        goal = self.get_tile_center(self.target)
        to_goal = goal - self.pos
        step = config.COW_SPEED * dt

        arrived = to_goal.length() <= step
        new_pos = goal if arrived else self.pos + to_goal.normalize() * step
        if player_rect.colliderect(self.get_hitbox_at(new_pos)):
            return

        if to_goal.x != 0:
            self.facing_left = to_goal.x < 0
        self.pos = new_pos
        if arrived:
            self.target = None

    def update(self, dt, world, blocked, player_rect, herd):
        """Rest, then take a step to a random neighbor tile, again and again.

        blocked = tiles a cow must not enter (soil, villagers, the player).
        herd = all the cows, so that two cows never take the same tile.
        """
        if self.target is None:
            self.wait -= dt
            if self.wait <= 0:
                self.choose_target(world, blocked, player_rect, herd)
                self.wait = random.uniform(*config.COW_WAIT)
        else:
            self.walk(dt, player_rect)

        size = config.TILE_SIZE
        self.tile = (int(self.pos.x // size), int(self.pos.y // size))

    def new_day(self):
        """Every morning the cow has milk again."""
        self.milk_ready = True

    def milk(self, inventory, energy):
        """Take the milk of the cow. Return "milked", "not_ready", "full" or "tired"."""
        if not self.milk_ready:
            return "not_ready"
        if not inventory.can_add("milk"):
            return "full"
        cost = config.ENERGY_COSTS["milk"]
        if not energy.can_afford(cost):
            return "tired"

        inventory.add_item("milk")
        energy.spend(cost)
        self.milk_ready = False
        return "milked"

    def draw(self, screen, font, camera):
        """Draw the cow with its feet on the ground, and a bobbing milk drop when it can be milked."""
        body = self.get_body_rect().move(-camera.x, -camera.y)

        if self.has_sprite:
            picture = load_image(config.COW_SPRITE, config.COW_SIZE, config.COW_COLOR)
            sprite_looks_left = config.COW_SPRITE_FACES == "left"
            if self.facing_left != sprite_looks_left:
                picture = pygame.transform.flip(picture, True, False)
            screen.blit(picture, body)
        else:
            self.draw_placeholder(screen, body)

        if self.milk_ready:
            bob = (pygame.time.get_ticks() // 300) % 2 * 2
            drop = (body.centerx, body.y - 6 + bob)
            pygame.draw.circle(screen, config.HIVE_OUTLINE, drop, 5)
            pygame.draw.circle(screen, config.MILK_COLOR, drop, 3)