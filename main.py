import pygame
from player import Player
from world import TileMap, TILE_SIZE
from gametime import GameTime
from inventory import Inventory
from farm import Farm
from shop import Shop, sell_selected
from ui import HUD
from npc import load_npcs
from controls import INTERACT_KEYS
from dialogue import DialogueBox, load_dialogues, get_lines

pygame.init()
screen = pygame.display.set_mode((960, 544), pygame.SCALED | pygame.FULLSCREEN)
pygame.display.set_caption("Farm Mystery")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)        # your font lines here
small_font = pygame.font.Font(None, 22)  # your font lines here

# physical keys 1 to 9 then 0, whatever the keyboard layout
SLOT_KEYS = [pygame.KSCAN_1, pygame.KSCAN_2, pygame.KSCAN_3, pygame.KSCAN_4,
             pygame.KSCAN_5, pygame.KSCAN_6, pygame.KSCAN_7, pygame.KSCAN_8,
             pygame.KSCAN_9, pygame.KSCAN_0]

world = TileMap("maps/farm.txt", "data/tiles.json")
player = Player(64, 256)
game_time = GameTime()
farm = Farm()
shop = Shop()
hud = HUD(font, small_font)
npcs = load_npcs("data/npcs.json")
dialogues = load_dialogues("data/dialogues.json")
dialogue_box = DialogueBox()

inventory = Inventory()
inventory.add_item("hoe")
inventory.add_item("watering_can")
inventory.add_item("turnip_seeds", 5)

night = pygame.Surface(screen.get_size())
night.fill((0, 0, 40))


def interact():
    """Do the action on the tile in front of the player.

    An NPC there starts a dialogue, the shop counter opens the shop, the box
    sells the held item, and anything else goes to the farm
    (till, water, plant, harvest).
    """
    tx, ty = player.get_target_tile()
    action = world.get_action(tx, ty)

    # is there an NPC on the tile in front of us?
    npc_found = None
    for npc in npcs:
        if npc.tile == (tx, ty):
            npc_found = npc

    if npc_found is not None:
        lines = get_lines(dialogues, npc_found.id, game_time.day)
        dialogue_box.open(npc_found.name, lines)
    elif action == "shop":
        shop.open()
    elif action == "sell":
        hud.show_notice(sell_selected(inventory))
    else:
        farm.use(tx, ty, inventory, world)


running = True
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if dialogue_box.is_open:
                dialogue_box.handle_key(event.key)
            elif shop.is_open:
                shop.handle_key(event.key, inventory)
            else:
                if event.key in INTERACT_KEYS:
                    interact()
                for i, code in enumerate(SLOT_KEYS):
                    if event.scancode == code:
                        inventory.select(i)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # button 1 is the left click
            if event.button == 1:
                if dialogue_box.is_open:
                    dialogue_box.handle_click()
                elif shop.is_open:
                    shop.handle_click(event.pos, screen, inventory)
                else:
                    interact()
        elif event.type == pygame.MOUSEWHEEL:
            if not shop.is_open and not dialogue_box.is_open:
                inventory.scroll(-event.y)

    # the game is paused while the shop or a dialogue is open
    paused = shop.is_open or dialogue_box.is_open
    if not paused:
        player.update(dt, world)

        new_day = game_time.update(dt)
        if new_day:
            farm.new_day()
            for npc in npcs:
                npc.go_home()

        for npc in npcs:
            npc.update(dt, game_time.minutes, world)
    hud.update(dt)

    screen.fill((180, 229, 145))
    world.draw(screen)
    farm.draw(screen)
    for npc in npcs:
        npc.draw(screen, small_font)
    player.draw(screen)

    # yellow outline on the tile in front of the player
    tx, ty = player.get_target_tile()
    target = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(screen, (255, 220, 60), target, 2)

    # the night covers the whole screen, the interface is drawn on top
    night.set_alpha(game_time.get_darkness())
    screen.blit(night, (0, 0))

    hud.draw(screen, game_time, inventory)

    if shop.is_open:
        shop.draw(screen, font, small_font, inventory)

    dialogue_box.draw(screen, font, small_font)

    pygame.display.flip()

pygame.quit()