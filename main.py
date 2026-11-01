import pygame
from player import Player
from world import TileMap
from gametime import GameTime
from inventory import Inventory

pygame.init()
screen = pygame.display.set_mode((960, 540))
pygame.display.set_caption("Farm Mystery")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 22)

# physical keys 1 to 9 then 0, whatever the keyboard layout
SLOT_KEYS = [pygame.KSCAN_1, pygame.KSCAN_2, pygame.KSCAN_3, pygame.KSCAN_4,
             pygame.KSCAN_5, pygame.KSCAN_6, pygame.KSCAN_7, pygame.KSCAN_8,
             pygame.KSCAN_9, pygame.KSCAN_0]

world = TileMap("maps/farm.txt")
player = Player(64, 256)
game_time = GameTime()

inventory = Inventory()
inventory.add_item("hoe")
inventory.add_item("watering_can")
inventory.add_item("turnip_seeds", 5)

night = pygame.Surface(screen.get_size())
night.fill((0, 0, 40))

running = True
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            for i, code in enumerate(SLOT_KEYS):
                if event.scancode == code:
                    inventory.select(i)
        elif event.type == pygame.MOUSEWHEEL:
            inventory.scroll(-event.y)

    player.update(dt, world)
    game_time.update(dt)

    screen.fill((0, 0, 0))
    world.draw(screen)
    player.draw(screen)

    night.set_alpha(game_time.get_darkness())
    screen.blit(night, (0, 0))

    text = font.render(game_time.get_text(), True, (255, 255, 255))
    screen.blit(text, (540, 20))
    held = font.render(inventory.get_selected_name(), True, (255, 255, 255))
    screen.blit(held, (540, 60))

    inventory.draw(screen, small_font)

    pygame.display.flip()

pygame.quit()