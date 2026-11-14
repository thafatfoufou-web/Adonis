import os
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
import pygame
import config
from core.camera import Camera
from core.gametime import GameTime
from entities.cow import Cow
from entities.npc import load_npcs
from entities.player import Player
from systems.energy import Energy
from systems.farm import Farm
from systems.inventory import Inventory
from ui.dialogue import DialogueBox, load_dialogues, pick_entry
from ui.hud import HUD
from ui.shop import Shop, sell_selected
from world.tilemap import TileMap
from systems.story import Story
from systems.apiary import Apiary

pygame.init()
window_flags = pygame.SCALED | (pygame.FULLSCREEN if config.FULLSCREEN else 0)
screen = pygame.display.set_mode(config.SCREEN_SIZE, window_flags)
pygame.display.set_caption(config.WINDOW_TITLE)
clock = pygame.time.Clock()
font = pygame.font.Font(None, config.FONT_SIZE)
small_font = pygame.font.Font(None, config.SMALL_FONT_SIZE)

world = TileMap(config.MAP_FILE, config.TILES_FILE, config.BUILDINGS_FILE)
player = Player(*config.PLAYER_START)
camera = Camera(screen.get_size(), world.pixel_size, config.CAMERA_PADDING)
game_time = GameTime()
farm = Farm()
apiary = Apiary(world)
shop = Shop()
hud = HUD(font, small_font)
npcs = load_npcs(config.NPCS_FILE)
cows = [Cow(tile) for tile in config.COW_START_TILES]
dialogues = load_dialogues(config.DIALOGUES_FILE)
dialogue_box = DialogueBox()
inventory = Inventory()
energy = Energy()
story = Story()

for item_id, count in config.STARTING_ITEMS:
    inventory.add_item(item_id, count)

night = pygame.Surface(screen.get_size())
night.fill(config.NIGHT_COLOR)

HIVE_MESSAGES = {
    "placed": ("You placed the beehive.", config.GOOD),
    "collected": ("You collected some honey.", config.GOOD),
    "not_ready": ("The bees are still working...", config.GOOD),
    "bad_spot": ("A hive needs a free patch of grass.", config.BAD),
    "full": ("Your hotbar is full.", config.BAD),
    "tired": ("Too tired... go home and sleep.", config.BAD),
    "picked_up": ("You took the beehive back.", config.GOOD),
        "placed_no_flowers": ("Placed. But bees need flowers nearby to make honey.", config.BAD),
    "no_flowers": ("No flowers nearby: the bees cannot make honey here.", config.BAD),
}


COW_MESSAGES = {
    "milked": ("You milked the cow.", config.GOOD),
    "not_ready": ("This cow has no milk left today.", config.BAD),
    "full": ("Your hotbar is full.", config.BAD),
    "tired": ("Too tired... go home and sleep.", config.BAD),
}


def start_new_day(slept):
    """Start the next morning: crops grow, villagers go home and energy comes back.

    Sleeping restores SLEEP_ENERGY_FRACTION of the energy, staying up until
    midnight only PASS_OUT_FRACTION.
    """
    farm.new_day()
    apiary.new_day()
    for npc in npcs:
        npc.go_home()
    for cow in cows:
        cow.new_day()

    if slept:
        energy.restore(config.SLEEP_ENERGY_FRACTION)
        hud.show_notice("You slept well. A new day begins!")
    else:
        energy.restore(config.PASS_OUT_FRACTION)
        hud.show_notice("You fell asleep exhausted...", 3, config.BAD)


def interact(target=None):
    """Do the action on a tile: the one in front of the player, or the clicked one if target is given.

    An NPC starts a dialogue, the shop counter opens the shop, the box sells
    the held item, the bed sleeps, and anything else goes to the farm.
    """
    if target is None:
        tx, ty = player.get_target_tile()
    else:
        tx, ty = target
    action = world.get_action(tx, ty)

    npc_found = None
    for npc in npcs:
        if npc.tile == (tx, ty):
            npc_found = npc

    cow_found = None
    for cow in cows:
        if cow.is_on_tile(tx, ty):
            cow_found = cow

    if npc_found is not None:
        entry = pick_entry(dialogues, npc_found.id, game_time, story)
        gifts = entry.get("gives", [])
        if not all(inventory.can_add(gift["item"]) for gift in gifts):
            hud.show_notice("Your hotbar is full. Make some room first.", 2, config.BAD)
        else:
            dialogue_box.open(npc_found.name, entry["lines"])
            story.set_many(entry.get("sets", []))
            for gift in gifts:
                inventory.add_item(gift["item"], gift.get("count", 1))
    elif cow_found is not None:
        text, color = COW_MESSAGES[cow_found.milk(inventory, energy)]
        hud.show_notice(text, 2, color)
    elif action == "shop":
        shop.open()
    elif action == "sell":
        hud.show_notice(sell_selected(inventory))
    elif action == "sleep":
        game_time.new_day()
        start_new_day(slept=True)
    else:
        taken = set(farm.soil) | {npc.tile for npc in npcs} | {player.get_tile()}
        hive_result = apiary.use(tx, ty, inventory, energy, story, taken)
        if hive_result is not None:
            text, color = HIVE_MESSAGES[hive_result]
            hud.show_notice(text, 2, color)
        elif farm.use(tx, ty, inventory, world, energy) == "tired":
            hud.show_notice("Too tired... go home and sleep.", 2, config.BAD)


def get_mouse_tile():
    """Return the tile under the mouse, using the building's door when the mouse is on a building."""
    world_pos = camera.to_world(pygame.mouse.get_pos())
    tile = world.get_building_click_tile(world_pos, player.get_tile())
    if tile is None:
        tile = (world_pos[0] // config.TILE_SIZE, world_pos[1] // config.TILE_SIZE)
    return tile


def handle_events():
    """Process the window, keyboard and mouse events. Return False when the player quits."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.KEYDOWN:
            if dialogue_box.is_open:
                dialogue_box.handle_key(event.key)
            elif shop.is_open:
                shop.handle_key(event.key, inventory)
            else:
                if event.key in config.INTERACT_KEYS:
                    interact()
                for i, code in enumerate(config.SLOT_KEYS):
                    if event.scancode == code:
                        inventory.select(i)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if dialogue_box.is_open:
                    dialogue_box.handle_click()
                elif shop.is_open:
                    shop.handle_click(event.pos, screen, inventory)
                else:
                    tile = get_mouse_tile()
                    if player.can_reach(tile[0], tile[1], config.CLICK_REACH):
                        player.face_tile(tile[0], tile[1])
                        interact(tile)
        elif event.type == pygame.MOUSEMOTION:
            if shop.is_open:
                shop.handle_hover(event.pos, screen)
        elif event.type == pygame.MOUSEWHEEL:
            if not shop.is_open and not dialogue_box.is_open:
                inventory.scroll(-event.y)
    return True


def update(dt):
    """Advance the game by dt seconds; everything but the HUD freezes while the shop or a dialogue is open."""
    paused = shop.is_open or dialogue_box.is_open
    if not paused:
        player.update(dt, world)

        if game_time.update(dt):
            start_new_day(slept=False)

        for npc in npcs:
            npc.update(dt, game_time.minutes, world)

        blocked = set(farm.soil) | {npc.tile for npc in npcs} | {player.get_tile()}
        for cow in cows:
            cow.update(dt, world, blocked, player.get_rect(), cows)
        world.moving_obstacles = [cow.get_hitbox() for cow in cows]
    hud.update(dt)

    player_x, player_y = player.get_rect().center
    camera.follow((player_x, player_y - config.CAMERA_OFFSET_Y))


def draw():
    """Draw one frame: world, farm, characters in depth order, hover outline, night and interface."""
    screen.fill((0, 0, 0))
    world.draw(screen, camera)
    farm.draw(screen, camera)
    apiary.draw(screen, camera)
    feet = player.get_rect().bottom
    world.draw_objects(screen, camera, feet, True)

    walkers = npcs + cows       # villagers and cows are drawn in depth order with the player
    for walker in walkers:
        if walker.get_feet_y() <= feet:
            walker.draw(screen, small_font, camera)
    player.draw(screen, camera)
    for walker in walkers:
        if walker.get_feet_y() > feet:
            walker.draw(screen, small_font, camera)
    world.draw_objects(screen, camera, feet, False)

    hover = get_mouse_tile()
    if player.can_reach(hover[0], hover[1], config.CLICK_REACH):
        size = config.TILE_SIZE
        outline = pygame.Rect(hover[0] * size - camera.x, hover[1] * size - camera.y, size, size)
        pygame.draw.rect(screen, config.HOVER_COLOR, outline, config.HOVER_WIDTH)

    night.set_alpha(game_time.get_darkness())
    screen.blit(night, (0, 0))

    hud.draw(screen, game_time, inventory, energy)
    if shop.is_open:
        shop.draw(screen, font, small_font, inventory)
    dialogue_box.draw(screen, font, small_font)

    pygame.display.flip()


def main():
    """Run the game loop until the window is closed."""
    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000
        running = handle_events()
        update(dt)
        draw()
    pygame.quit()


if __name__ == "__main__":
    main()