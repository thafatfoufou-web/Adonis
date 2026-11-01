import pygame
from player import Player
from world import TileMap, TILE_SIZE
from gametime import GameTime
from inventory import Inventory
from farm import Farm
from shop import Shop, sell_selected
from ui import HUD

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
farm = Farm()
shop = Shop()
hud = HUD(font, small_font)

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
            if shop.is_open:
                shop.handle_key(event.key, inventory)
            else:
                if event.key == pygame.K_e:
                    tx, ty = player.get_target_tile()
                    tile = world.get_tile(tx, ty)
                    if tile == "3":
                        shop.open()
                    elif tile == "4":
                        hud.show_notice(sell_selected(inventory))
                    else:
                        farm.use(tx, ty, inventory, world)
                for i, code in enumerate(SLOT_KEYS):
                    if event.scancode == code:
                        inventory.select(i)
        elif event.type == pygame.MOUSEWHEEL:
            if not shop.is_open:
                inventory.scroll(-event.y)

    # the game is paused while the shop is open
    if not shop.is_open:
        player.update(dt, world)
        if game_time.update(dt):
            farm.new_day()
    hud.update(dt)

    screen.fill((0, 0, 0))
    world.draw(screen)
    farm.draw(screen)
    player.draw(screen)

    # yellow outline on the tile in front of the player
    tx, ty = player.get_target_tile()
    target = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(screen, (255, 220, 60), target, 2)

    # the night covers the whole screen, the interface is drawn on top
    night.set_alpha(game_time.get_darkness())
    screen.blit(night, (0, 0))

    hud.draw(screen, game_time, inventory)
    inventory.draw(screen, small_font)

    if shop.is_open:
        shop.draw(screen, font, small_font, inventory)

    pygame.display.flip()

pygame.quit()