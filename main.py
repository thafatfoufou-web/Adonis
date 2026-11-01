import pygame
from player import Player
from world import TileMap

pygame.init()
screen = pygame.display.set_mode((960, 540))
pygame.display.set_caption("Farm Mystery")
clock = pygame.time.Clock()

world = TileMap("maps/farm.txt")
player = Player(64, 256)

running = True
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.update(dt, world)

    screen.fill((0, 0, 0))  # black background around the map
    world.draw(screen)
    player.draw(screen)
    pygame.display.flip()

pygame.quit()