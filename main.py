import pygame
from player import Player
from world import TileMap
from gametime import GameTime

pygame.init()
screen = pygame.display.set_mode((960, 540))
pygame.display.set_caption("Farm Mystery")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)

world = TileMap("maps/farm.txt")
player = Player(64, 256)
game_time = GameTime()

# the night layer is created once and reused every frame
night = pygame.Surface(screen.get_size())
night.fill((0, 0, 40))

running = True
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.update(dt, world)
    game_time.update(dt)

    screen.fill((0, 0, 0))
    world.draw(screen)
    player.draw(screen)

    night.set_alpha(game_time.get_darkness())
    screen.blit(night, (0, 0))

    text = font.render(game_time.get_text(), True, (255, 255, 255))
    screen.blit(text, (540, 20))

    pygame.display.flip()

pygame.quit()