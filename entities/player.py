"""The player character: position, movement and drawing."""

import pygame
import config
from core.assets import load_image


class Player:
    """The controlled character. Its hitbox is only the feet, so the head can go over things."""


    def __init__(self, x, y, sprite_path=config.PLAYER_SPRITES["female"]):
        """Create the player at pixel position (x, y), looking down, drawn with the picture at sprite_path."""
        self.sprite_path = sprite_path
        self.pos = pygame.Vector2(x, y)
        self.speed = config.PLAYER_SPEED
        self.width, self.height = config.PLAYER_HITBOX
        self.facing = pygame.Vector2(0, 1)

    def get_rect(self):
        """Return the feet hitbox in world pixels."""
        return pygame.Rect(self.pos.x, self.pos.y, self.width, self.height)

    def get_target_tile(self):
        """Return the tile just in front of the player's feet."""
        cx, cy = self.get_rect().center
        tx = int((cx + self.facing.x * config.TILE_SIZE) // config.TILE_SIZE)
        ty = int((cy + self.facing.y * config.TILE_SIZE) // config.TILE_SIZE)
        return tx, ty

    def get_tile(self):
        """Return the tile the player is standing on."""
        cx, cy = self.get_rect().center
        return int(cx // config.TILE_SIZE), int(cy // config.TILE_SIZE)

    def can_reach(self, tx, ty, reach=1):
        """Return True if tile (tx, ty) is within reach tiles of the player (own tile included)."""
        px, py = self.get_tile()
        return max(abs(tx - px), abs(ty - py)) <= reach

    def face_tile(self, tx, ty):
        """Turn toward a tile (horizontal wins on a diagonal)."""
        px, py = self.get_tile()
        dx, dy = tx - px, ty - py
        if dx != 0:
            self.facing = pygame.Vector2(1 if dx > 0 else -1, 0)
        elif dy != 0:
            self.facing = pygame.Vector2(0, 1 if dy > 0 else -1)

    def update(self, dt, world):
        """Read the movement keys and move axis by axis, undoing a move that hits a wall."""
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if any(keys[k] for k in config.LEFT_KEYS):
            direction.x -= 1
        if any(keys[k] for k in config.RIGHT_KEYS):
            direction.x += 1
        if any(keys[k] for k in config.UP_KEYS):
            direction.y -= 1
        if any(keys[k] for k in config.DOWN_KEYS):
            direction.y += 1

        if direction.x != 0:
            self.facing = pygame.Vector2(1 if direction.x > 0 else -1, 0)
        elif direction.y != 0:
            self.facing = pygame.Vector2(0, 1 if direction.y > 0 else -1)

        if direction.length() > 0:
            direction = direction.normalize()
        move = direction * self.speed * dt

        self.pos.x += move.x
        if world.collides(self.get_rect()):
            self.pos.x -= move.x

        self.pos.y += move.y
        if world.collides(self.get_rect()):
            self.pos.y -= move.y

    def draw(self, screen, camera):
        """Draw the sprite with its bottom on the feet hitbox."""
        width, height = config.PLAYER_SPRITE_SIZE
        sprite = load_image(self.sprite_path, config.PLAYER_SPRITE_SIZE, config.PLAYER_FALLBACK_COLOR)
        hitbox = self.get_rect()
        x = hitbox.centerx - width // 2 - camera.x
        y = hitbox.bottom - height - camera.y
        screen.blit(sprite, (x, y))
