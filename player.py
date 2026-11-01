import pygame
from world import TILE_SIZE


class Player:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.speed = 200
        self.size = 24  # smaller than a tile, so he fits through gaps
        self.facing = pygame.Vector2(0, 1)  # looking down at the start

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.size, self.size)

    def get_target_tile(self):
        # the tile just in front of the player's center
        cx, cy = self.get_rect().center
        tx = int((cx + self.facing.x * TILE_SIZE) // TILE_SIZE)
        ty = int((cy + self.facing.y * TILE_SIZE) // TILE_SIZE)
        return tx, ty

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
        pygame.draw.rect(screen, (230, 200, 80), self.get_rect())