import pygame


class Player:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.speed = 200
        self.size = 24  # smaller than a tile, so he fits through gaps

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.size, self.size)

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