import pygame
from world import TILE_SIZE
from assets import load_image

SPRITE_SIZE = (64, 64)


class Player:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.speed = 200
        # the hitbox is only her feet (a small rectangle at the bottom of the
        # sprite), so her head can go over things, like in a real top-down game
        self.width = 14
        self.height = 10
        self.facing = pygame.Vector2(0, 1)  # looking down at the start

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.width, self.height)

    def get_target_tile(self):
        # the tile just in front of the player's feet
        cx, cy = self.get_rect().center
        tx = int((cx + self.facing.x * TILE_SIZE) // TILE_SIZE)
        ty = int((cy + self.facing.y * TILE_SIZE) // TILE_SIZE)
        return tx, ty

    def get_tile(self):
        # the tile the player is standing on (center of her feet)
        cx, cy = self.get_rect().center
        return int(cx // TILE_SIZE), int(cy // TILE_SIZE)

    def can_reach(self, tx, ty, reach=1):
        # True if tile (tx, ty) is within `reach` tiles (our own tile included)
        px, py = self.get_tile()
        return max(abs(tx - px), abs(ty - py)) <= reach

    def face_tile(self, tx, ty):
        # turn toward a tile (horizontal wins in diagonal, like in update)
        px, py = self.get_tile()
        dx, dy = tx - px, ty - py
        if dx != 0:
            self.facing = pygame.Vector2(1 if dx > 0 else -1, 0)
        elif dy != 0:
            self.facing = pygame.Vector2(0, 1 if dy > 0 else -1)

    def update(self, dt, world):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_LEFT] or keys[pygame.K_q] or keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_z] or keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction.y += 1

        # remember where we look (horizontal wins in diagonal)
        if direction.x != 0:
            self.facing = pygame.Vector2(1 if direction.x > 0 else -1, 0)
        elif direction.y != 0:
            self.facing = pygame.Vector2(0, 1 if direction.y > 0 else -1)

        if direction.length() > 0:
            direction = direction.normalize()
        move = direction * self.speed * dt

        # move on X, undo if we hit a wall
        self.pos.x += move.x
        if world.collides(self.get_rect()):
            self.pos.x -= move.x

        # move on Y, undo if we hit a wall
        self.pos.y += move.y
        if world.collides(self.get_rect()):
            self.pos.y -= move.y

    def draw(self, screen):
        sprite = load_image("assets/characters/player.png", SPRITE_SIZE, (230, 200, 80))
        hitbox = self.get_rect()
        x = hitbox.centerx - SPRITE_SIZE[0] // 2
        y = hitbox.bottom - SPRITE_SIZE[1]
        screen.blit(sprite, (x, y))