import os
import sys
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
import pygame
import config
from core.assets import load_font
from core.camera import Camera
from core.gametime import GameTime
from entities.cow import Cow
from entities.npc import load_npcs
from entities.player import Player
from systems.energy import Energy
from systems.farm import Farm
from systems.inventory import Inventory
from ui.dialogue import DialogueBox, load_dialogues, pick_entry, personalize, entry_lines, chat_flag
from ui.hud import HUD, DaySummary, QuestLog
from ui.menus import run_start_menus
from ui.pause import PauseMenu
from ui.ending import EndingScreen, find_ending
from systems.save import build_save, apply_save, write_save
from ui.shop import Shop, sell_selected
from ui import theme
from world.tilemap import TileMap
from systems.story import Story
from systems.quests import Quests
from systems.pickups import Pickups
from systems.visits import Visits
from systems.apiary import Apiary
from systems.affection import Affection
from core.mood import Mood

pygame.init()
window_flags = pygame.SCALED | (pygame.FULLSCREEN if config.FULLSCREEN else 0)
screen = pygame.display.set_mode(config.SCREEN_SIZE, window_flags)
pygame.display.set_caption(config.WINDOW_TITLE)
clock = pygame.time.Clock()
font = load_font(config.FONT_FILE, config.FONT_SIZE)
small_font = load_font(config.FONT_FILE, config.SMALL_FONT_SIZE)
theme.use_pixel_cursor()

pause_menu = PauseMenu()
menu_button_rect = pygame.Rect(*config.MENU_BUTTON_RECT)
quest_button_rect = pygame.Rect(*config.QUEST_BUTTON_RECT)
profile = None
next_screen = None          # the pause menu sets it to "menu"


def start_session(new_profile):
    """Build a fresh game (a new one, or the loaded save inside new_profile)."""
    global profile, world, player, camera, game_time, farm, apiary, shop, hud, npcs, cows
    global affection, dialogues, dialogue_box, inventory, energy, story, night, mood, quests, pending_notices, pickups, visits, summary, quest_log, day_stats, quests_done_at_dawn, ending
    profile = new_profile
    world = TileMap(config.MAP_FILE, config.TILES_FILE, config.BUILDINGS_FILE)
    player = Player(*config.PLAYER_START, profile["sprite"])
    camera = Camera(screen.get_size(), world.pixel_size, config.CAMERA_PADDING)
    game_time = GameTime()
    farm = Farm()
    apiary = Apiary(world)
    shop = Shop()
    hud = HUD(font, small_font)
    npcs = load_npcs(config.NPCS_FILE)
    # cows only exist once the barn is repaired (Quest 4); a save remembers how many there were
    saved_cows = [] if profile["save"] is None else profile["save"].get("cows", [])
    cows = [Cow(tile) for tile in config.COW_START_TILES[:len(saved_cows)]]
    dialogues = load_dialogues(config.DIALOGUES_FILE)
    dialogue_box = DialogueBox()
    inventory = Inventory()
    energy = Energy()
    story = Story()
    quests = Quests(config.QUESTS_FILE, story)
    world.story = story                 # lets buildings (the barn) appear when their story flag is set
    pickups = Pickups(config.PICKUPS_FILE)
    visits = Visits()
    summary = DaySummary()
    quest_log = QuestLog()
    affection = Affection(config.GIFTS_FILE)
    for problem in affection.check_data():
        print("gifts.json problem:", problem)         # typos in item ids show up here when the game starts
    ending = EndingScreen()
    reset_day_stats()
    pending_notices = []
    pause_menu.close()

    if profile["save"] is not None:
        apply_save(profile["save"], game_time, player, energy, inventory, farm, apiary, world, cows, story)
        quests.load(profile["save"].get("quests"))
        affection.load(profile["save"].get("affection"))
    else:
        for item_id, count in config.STARTING_ITEMS:
            inventory.add_item(item_id, count)

    night = pygame.Surface(screen.get_size())
    night.fill(config.NIGHT_COLOR)
    mood = Mood(screen.get_size())


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


def save_game():
    """Write the save file of the slot this game was started in. Return True if it worked."""
    data = build_save(profile, game_time, player, energy, inventory, farm, apiary, cows, story, quests, affection)
    return write_save(data, profile["slot"])


def use_pause_action(action):
    """Do what a pause menu button says."""
    global next_screen
    if action == "resume":
        pause_menu.close()
    elif action == "save":
        if save_game():
            pause_menu.set_message("Saved in slot " + str(profile["slot"]) + ".", config.GOOD)
        else:
            pause_menu.set_message("Could not save!", config.BAD)
    elif action == "menu":
        next_screen = "menu"


def reset_day_stats():
    """Forget what happened today, so the next summary only counts the new day."""
    global day_stats, quests_done_at_dawn
    day_stats = {"tilled": 0, "planted": 0, "watered": 0, "harvested": 0, "sold": 0, "gold": 0, "honey": 0, "milk": 0}
    quests_done_at_dawn = {quest["id"] for quest in quests.defs if quests.is_done(quest["id"])}


def build_summary(slept):
    """Return (title, rows, note) for the end of the day, before the crops grow."""
    stats = day_stats
    finished = game_time.day - 1            # the clock already moved on to the next morning
    season = config.SEASON_NAMES[((finished - 1) // config.SEASON_LENGTH) % len(config.SEASON_NAMES)]
    title = season + " " + str((finished - 1) % config.SEASON_LENGTH + 1) + (" is over" if slept else ": you passed out")
    rows = []
    for label, key in (("Soil tilled", "tilled"), ("Seeds planted", "planted"), ("Plants watered", "watered"),
                       ("Crops harvested", "harvested"), ("Honey collected", "honey"), ("Milk collected", "milk")):
        if stats[key] > 0:
            rows.append((label, stats[key]))
    if stats["sold"] > 0:
        rows.append(("Sold at the box", str(stats["sold"]) + " items, +" + str(stats["gold"]) + " gold"))
    for quest in quests.defs:
        if quests.is_done(quest["id"]) and quest["id"] not in quests_done_at_dawn:
            rows.append(("Quest done", quest["title"]))

    did_something = len(rows) > 0
    planted = [tile for tile in farm.soil.values() if tile["crop"] is not None]
    ripe = sum(1 for tile in planted if farm.is_ripe(tile))
    thirsty = sum(1 for tile in planted if not tile["watered"] and not farm.is_ripe(tile))
    if planted:
        rows.append(("Crops in the ground", str(len(planted)) + (", " + str(ripe) + " ripe" if ripe else "")))
    rows.append(("Gold in your pocket", inventory.gold))

    if not did_something:
        note = "A quiet day. Nothing got done, and the valley kept going without you."
    elif thirsty:
        note = str(thirsty) + " unwatered crop" + ("s" if thirsty > 1 else "") + " will not grow tonight."
    else:
        note = ""
    return title, rows, note


def start_new_day(slept):
    """Start the next morning: crops grow, villagers go home and energy comes back.

    Sleeping restores SLEEP_ENERGY_FRACTION of the energy, staying up until
    midnight only PASS_OUT_FRACTION.
    """
    title, rows, note = build_summary(slept)
    reset_day_stats()
    farm.new_day()
    apiary.new_day()
    affection.new_day()
    for flag in [flag for flag in story.flags if flag.startswith("chat_") and flag.endswith("_today")]:
        story.clear(flag)                   # every villager has a new chat for you
    for npc in npcs:
        npc.go_home()
    for cow in cows:
        cow.new_day()
    player.respawn_home()               # you always wake up at home, even after passing out far away

    if slept:
        energy.restore(config.SLEEP_ENERGY_FRACTION)
        message, color = "You slept well. A new day begins!", config.GOOD
    else:
        energy.restore(config.PASS_OUT_FRACTION)
        message, color = "You fell asleep exhausted...", config.BAD

    # every new day is saved automatically
    if save_game():
        message += "  Game saved."
    else:
        message += "  (Could not save!)"
        color = config.BAD
    summary.open(title, rows, note, message, color)


def farm_counts():
    """Return (tilled tiles, planted tiles, watered tiles); comparing before and after an action tells what happened."""
    tilled = len(farm.soil)
    planted = sum(1 for tile in farm.soil.values() if tile["crop"] is not None)
    watered = sum(1 for tile in farm.soil.values() if tile["watered"])
    return (tilled, planted, watered)


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

    handin_lines = None
    if npc_found is not None:
        handin_lines = quests.try_delivery(npc_found.id, inventory)
        if handin_lines is None:
            handin_lines = quests.try_handin(npc_found.id, inventory)
    if handin_lines is not None:
        open_talk(npc_found, handin_lines)
    elif npc_found is not None:
        entry = pick_entry(dialogues, npc_found.id, game_time, story)
        gifts = entry.get("gives", [])
        if not all(inventory.can_add(gift["item"]) for gift in gifts):
            hud.show_notice("Your hotbar is full. Make some room first.", 2, config.BAD)
        else:
            open_talk(npc_found, entry_lines(entry))
            story.set_many(entry.get("sets", []))
            if entry.get("daily"):
                story.set(chat_flag(npc_found.id))
            quests.notify("talk", npc=npc_found.id)
            for gift in gifts:
                inventory.add_item(gift["item"], gift.get("count", 1))
    elif cow_found is not None:
        milk_result = cow_found.milk(inventory, energy)
        if milk_result == "milked":
            day_stats["milk"] += 1
        text, color = COW_MESSAGES[milk_result]
        hud.show_notice(text, 2, color)
    elif pickups.at(tx, ty, story, quests) is not None:
        text, good = pickups.pick(tx, ty, inventory, story, quests)
        hud.show_notice(text, 2, config.GOOD if good else config.BAD)
    elif action == "shop":
        shop.open(story, cows)
    elif action == "sell":
        held = inventory.get_selected()
        item_id = None if held is None else held["id"]
        gold_before = inventory.gold
        hud.show_notice(sell_selected(inventory))
        if inventory.gold > gold_before:
            quests.notify("sell", item=item_id, gold=inventory.gold - gold_before)
            day_stats["sold"] += 1
            day_stats["gold"] += inventory.gold - gold_before
    elif action == "sleep":
        if game_time.minutes < config.EARLIEST_SLEEP and energy.get_fraction() > config.LOW_ENERGY:
            hud.show_notice("Too early to sleep. The bed is for after 19:00.", 2, config.BAD)
        else:
            game_time.new_day()
            start_new_day(slept=True)
    else:
        taken = set(farm.soil) | {npc.tile for npc in npcs} | {player.get_tile()}
        hive_result = apiary.use(tx, ty, inventory, energy, story, taken)
        if hive_result is not None:
            if hive_result == "collected":
                day_stats["honey"] += 1
            text, color = HIVE_MESSAGES[hive_result]
            hud.show_notice(text, 2, color)
        else:
            before = farm_counts()
            tile_before = farm.soil.get((tx, ty))
            was_ripe = tile_before is not None and farm.is_ripe(tile_before)
            if farm.use(tx, ty, inventory, world, energy) == "tired":
                hud.show_notice("Too tired... go home and sleep.", 2, config.BAD)
            after = farm_counts()
            if was_ripe and farm.soil.get((tx, ty), {}).get("crop", 1) is None:
                day_stats["harvested"] += 1
            if after[0] > before[0]:
                day_stats["tilled"] += 1
                quests.notify("till")
            if after[1] > before[1]:
                day_stats["planted"] += 1
                quests.notify("plant")
            if after[2] > before[2]:
                day_stats["watered"] += 1
                quests.notify("water")


def open_talk(npc, lines):
    """Open the dialogue box for a villager. The first chat of the day also earns a little friendship."""
    gained = affection.talk(npc.id, story)
    hearts = affection.get_hearts(npc.id)
    dialogue_box.open(npc.name, personalize(lines, profile["name"]))
    npc.pause(config.NPC_PAUSE_AFTER_CHAT)
    if gained:
        pending_notices.append((npc.name + " likes you more now (" + str(hearts) + " hearts).", config.GOOD))


def find_gift_target():
    """Return the villager closest to the player within GIFT_REACH tiles (a little preference for the one in front), or None."""
    px, py = player.get_rect().center
    reach = (config.GIFT_REACH + 0.5) * config.TILE_SIZE
    best, best_score = None, None
    for npc in npcs:
        dx, dy = npc.pos.x - px, npc.pos.y - py
        distance = (dx * dx + dy * dy) ** 0.5
        if distance > reach:
            continue
        in_front = dx * player.facing.x + dy * player.facing.y > 0
        score = distance - (config.TILE_SIZE / 2 if in_front else 0)
        if best is None or score < best_score:
            best, best_score = npc, score
    return best


def find_npc_under_mouse():
    """Return the villager whose body is under the mouse (front-most first), or None."""
    world_pos = camera.to_world(pygame.mouse.get_pos())
    for npc in sorted(npcs, key=lambda n: n.get_feet_y(), reverse=True):
        if npc.get_hit_rect().collidepoint(world_pos):
            return npc
    return None


def give_gift(target=None):
    """Give the held item to the villager at the clicked tile, or else to the closest villager near the player."""
    npc_found = None
    if target is not None:
        for npc in npcs:
            if npc.tile == tuple(target):
                npc_found = npc
    if npc_found is None:
        npc_found = find_gift_target()
    if npc_found is None:
        hud.show_notice("Nobody close enough to give a gift to.", 2, config.BAD)
        return
    slot = inventory.get_selected()
    if slot is None:
        hud.show_notice("Select an item to give first.", 2, config.BAD)
        return
    item_id = slot["id"]
    result = affection.give(npc_found.id, item_id, story, profile["name"])
    if not result["ok"]:
        hud.show_notice(result["text"], 2, config.BAD)
        return
    inventory.remove_one_selected()
    quests.notify("gift", npc=npc_found.id, item=item_id)
    dialogue_box.open(npc_found.name, result["lines"])
    npc_found.pause(config.NPC_PAUSE_AFTER_CHAT)
    if result["hearts_gained"]:
        pending_notices.append((npc_found.name + " likes you more now (" + str(result["hearts"]) + " hearts).", config.GOOD))


def get_mouse_tile():
    """Return the tile under the mouse, using the building's door when the mouse is on a building."""
    world_pos = camera.to_world(pygame.mouse.get_pos())
    tile = world.get_building_click_tile(world_pos, player.get_tile())
    if tile is None:
        tile = (world_pos[0] // config.TILE_SIZE, world_pos[1] // config.TILE_SIZE)
    return tile


def open_quest_log():
    """Open the quest book and clear its red dot."""
    quest_log.open()                    # always opens on the Quests page
    hud.quests_unread = False


def handle_events():
    """Process the window, keyboard and mouse events. Return False when the player quits."""
    global next_screen
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif ending.is_open:
            # the story is over: any key or click goes back to the title screen
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                next_screen = "menu"
        elif event.type == pygame.KEYDOWN:
            if pause_menu.is_open:
                use_pause_action(pause_menu.handle_key(event.key))
            elif summary.is_open:
                summary.handle_key(event.key)
            elif quest_log.is_open:
                quest_log.handle_key(event.key)
            elif dialogue_box.is_open:
                dialogue_box.handle_key(event.key)
            elif shop.is_open:
                shop.handle_key(event.key, inventory)
            elif event.key == config.QUEST_LOG_KEY:
                open_quest_log()
            elif event.key == config.GIFT_KEY:
                give_gift()
            elif event.key == pygame.K_ESCAPE:
                pause_menu.open()
            else:
                if event.key in config.INTERACT_KEYS:
                    interact()
                for i, code in enumerate(config.SLOT_KEYS):
                    if event.scancode == code:
                        inventory.select(i)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if pause_menu.is_open:
                    use_pause_action(pause_menu.handle_click(event.pos, screen))
                elif summary.is_open:
                    summary.handle_click()
                elif quest_log.is_open:
                    quest_log.handle_click(event.pos)
                elif dialogue_box.is_open:
                    dialogue_box.handle_click()
                elif shop.is_open:
                    shop.handle_click(event.pos, screen, inventory)
                elif menu_button_rect.collidepoint(event.pos):
                    pause_menu.open()
                elif quest_button_rect.collidepoint(event.pos):
                    open_quest_log()
                else:
                    tile = get_mouse_tile()
                    if player.can_reach(tile[0], tile[1], config.CLICK_REACH):
                        player.face_tile(tile[0], tile[1])
                        interact(tile)
            elif event.button == 3:
                # right click on a villager: give them the held item
                blocked = (pause_menu.is_open or summary.is_open or quest_log.is_open
                           or dialogue_box.is_open or shop.is_open)
                if not blocked:
                    clicked = find_npc_under_mouse()          # click anywhere on the villager's body
                    if clicked is not None:
                        if player.can_reach(clicked.tile[0], clicked.tile[1], config.GIFT_REACH):
                            player.face_tile(clicked.tile[0], clicked.tile[1])
                            give_gift(clicked.tile)
                        else:
                            hud.show_notice("Get closer to give a gift.", 2, config.BAD)
                    else:
                        tile = get_mouse_tile()
                        if player.can_reach(tile[0], tile[1], config.CLICK_REACH):
                            player.face_tile(tile[0], tile[1])
                            give_gift(tile)
        elif event.type == pygame.MOUSEMOTION:
            if pause_menu.is_open:
                pause_menu.handle_hover(event.pos, screen)
            elif shop.is_open:
                shop.handle_hover(event.pos, screen)
        elif event.type == pygame.MOUSEWHEEL:
            if shop.is_open:
                shop.handle_wheel(event.y)
            elif not dialogue_box.is_open and not pause_menu.is_open and not summary.is_open and not quest_log.is_open:
                inventory.scroll(-event.y)
    return True


def update(dt):
    """Advance the game by dt seconds; everything but the HUD freezes while the shop or a dialogue is open."""
    paused = shop.is_open or dialogue_box.is_open or pause_menu.is_open or summary.is_open or quest_log.is_open or ending.is_open
    if not paused:
        player.update(dt, world)
        # the barn can appear on top of the player (it shows up in the morning after the quest): step out of it
        for _ in range(20):
            if not world.collides(player.get_rect()):
                break
            player.pos.y += 8

        if game_time.update(dt):
            start_new_day(slept=False)

        for npc in npcs:
            npc.update(dt, game_time.minutes, world)

        # a villager who has a quest for the player walks over and talks
        visits.update(dt, quests, npcs, player, world, inventory, story,
                      lambda name, lines: dialogue_box.open(name, personalize(lines, profile["name"])),
                      lambda text: hud.show_notice(text, 3, config.BAD))

        blocked = set(farm.soil) | {npc.tile for npc in npcs} | {player.get_tile()}
        for cow in cows:
            cow.update(dt, world, blocked, player.get_rect(), cows)
        world.moving_obstacles = [cow.get_hitbox() for cow in cows]
    hud.update(dt)
    if ending.is_open:
        return

    # quests: start, finish and pay; their messages wait until the dialogue box is closed
    quests.update(game_time.day, game_time.minutes < config.START_OF_DAY + config.MORNING_WINDOW)
    inventory.gold += quests.take_gold()
    if story.has("cows_unlocked") and len(cows) == 0:
        cows.append(Cow(config.COW_START_TILES[0]))
    for text, mood_name in quests.pop_messages():
        pending_notices.append((text, config.GOOD if mood_name == "good" else config.BAD))
    if pending_notices and hud.notice_timer <= 0 and not dialogue_box.is_open and not summary.is_open:
        text, color = pending_notices.pop(0)
        hud.show_notice(text, 3, color)

    # a failed quest can end the story, once its message has been shown
    reached = find_ending(story)
    if reached is not None and not pending_notices and not dialogue_box.is_open and not summary.is_open:
        ending.open(reached)

    player_x, player_y = player.get_rect().center
    camera.follow((player_x, player_y - config.CAMERA_OFFSET_Y))


def draw():
    """Draw one frame: world, farm, characters in depth order, hover outline, night and interface."""
    screen.fill((0, 0, 0))
    world.draw(screen, camera)
    farm.draw(screen, camera)
    pickups.draw(screen, camera, story, quests)
    apiary.draw(screen, camera)
    if config.MOOD_ENABLED:
        mood.draw(screen, config.MOOD_STRENGTH)

    # objects, buildings, villagers, cows and the player: all sorted by the height of their feet
    drawables = world.get_depth_items(screen, camera)
    for walker in npcs + cows:
        drawables.append((walker.get_feet_y(), lambda w=walker: w.draw(screen, small_font, camera)))
    drawables.append((player.get_rect().bottom, lambda: player.draw(screen, camera)))
    drawables.sort(key=lambda item: item[0])      # stable: on a tie the player stays in front
    for _, draw_it in drawables:
        draw_it()

    hover = get_mouse_tile()
    if player.can_reach(hover[0], hover[1], config.CLICK_REACH):
        size = config.TILE_SIZE
        outline = pygame.Rect(hover[0] * size - camera.x, hover[1] * size - camera.y, size, size)
        pygame.draw.rect(screen, config.HOVER_COLOR, outline, config.HOVER_WIDTH)

    night.set_alpha(game_time.get_darkness())
    screen.blit(night, (0, 0))

    hud.draw(screen, game_time, inventory, energy, quests)
    theme.draw_menu_button(screen, menu_button_rect, menu_button_rect.collidepoint(pygame.mouse.get_pos()))
    if shop.is_open:
        shop.draw(screen, font, small_font, inventory)
    dialogue_box.draw(screen, font, small_font)
    summary.draw(screen, font, small_font)
    quest_log.draw(screen, font, small_font, quests, npcs, affection, story)
    pause_menu.draw(screen, font, small_font)
    ending.draw(screen, font, small_font)

    theme.draw_cursor(screen)
    pygame.display.flip()
    
def main():
    """Show the title screen, play, and come back to the title screen from the pause menu."""
    global next_screen
    while True:
        chosen = run_start_menus(screen, clock, font, small_font)
        if chosen is None:
            break
        start_session(chosen)
        next_screen = None
        running = True
        while running and next_screen is None:
            dt = clock.tick(config.FPS) / 1000
            running = handle_events()
            update(dt)
            draw()
        if not running:
            break
    pygame.quit()


if __name__ == "__main__":
    main()