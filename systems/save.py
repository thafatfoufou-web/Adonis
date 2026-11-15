"""Saving and loading the game: one JSON file with everything that changes during play.

What is saved: the hero's name and gender, the day and time, the player's position and
energy, the hotbar and gold, the tilled soil with its crops, the beehives, whether each cow
has milk, and the story flags. The map, the villagers' positions (they walk home every
morning) and the interface are not saved.
"""

import json
import os
import pygame
import config
from systems.items import ITEMS


def save_exists():
    """Return True if a save file is there."""
    return os.path.exists(config.SAVE_FILE)


def read_save():
    """Return the saved data as a dictionary, or None if there is no usable save file."""
    if not os.path.exists(config.SAVE_FILE):
        return None
    try:
        with open(config.SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError) as error:
        print("[save] could not read " + config.SAVE_FILE + ": " + str(error))
        return None

    if not isinstance(data, dict):
        print("[save] the save file is not valid")
        return None
    version = data.get("version")
    if not isinstance(version, int) or version > config.SAVE_VERSION:
        print("[save] the save file has an unknown version: " + str(version))
        return None
    for key in ("profile", "time", "player"):
        if not isinstance(data.get(key), dict):
            print("[save] the save file is missing: " + key)
            return None
    return data


def write_save(data):
    """Write the data to the save file. Return True if it worked.

    The data goes to a temporary file first and replaces the real save only when it is
    complete, so a crash in the middle cannot ruin an existing save.
    """
    temporary = config.SAVE_FILE + ".tmp"
    try:
        folder = os.path.dirname(config.SAVE_FILE)
        if folder != "":
            os.makedirs(folder, exist_ok=True)
        with open(temporary, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=1)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, config.SAVE_FILE)
        return True
    except OSError as error:
        print("[save] could not write " + config.SAVE_FILE + ": " + str(error))
        return False


def build_save(profile, game_time, player, energy, inventory, farm, apiary, cows, story):
    """Collect everything worth keeping into a dictionary that can be written as JSON."""
    soil = []
    for (tx, ty), tile in farm.soil.items():
        crop = tile["crop"]
        soil.append({
            "x": tx,
            "y": ty,
            "watered": bool(tile["watered"]),
            "idle": int(tile.get("idle", 0)),
            "crop": None if crop is None else {"seed": crop["seed"], "days": int(crop["days"])},
        })

    hives = []
    for (tx, ty), hive in apiary.hives.items():
        hives.append({"x": tx, "y": ty, "days": int(hive["days"])})

    return {
        "version": config.SAVE_VERSION,
        "profile": {"name": profile["name"], "gender": profile["gender"]},
        "time": {"day": game_time.day, "minutes": game_time.minutes},
        "player": {
            "x": player.pos.x,
            "y": player.pos.y,
            "facing": [player.facing.x, player.facing.y],
            "energy": energy.value,
        },
        "inventory": {
            "slots": [None if slot is None else {"id": slot["id"], "count": slot["count"]}
                      for slot in inventory.slots],
            "selected": inventory.selected,
            "gold": inventory.gold,
        },
        "farm": soil,
        "hives": hives,
        "cows": [bool(cow.milk_ready) for cow in cows],
        "story": sorted(story.flags),
    }


def apply_save(data, game_time, player, energy, inventory, farm, apiary, world, cows, story):
    """Put the saved values back into the game objects. Anything unknown or broken is skipped."""
    time_data = data["time"]
    game_time.day = max(1, int(time_data.get("day", 1)))
    game_time.minutes = float(time_data.get("minutes", config.START_OF_DAY))

    player_data = data["player"]
    player.pos = pygame.Vector2(float(player_data.get("x", player.pos.x)),
                                float(player_data.get("y", player.pos.y)))
    facing = player_data.get("facing", [0, 1])
    player.facing = pygame.Vector2(float(facing[0]), float(facing[1]))
    energy.value = max(0, min(energy.maximum, int(player_data.get("energy", energy.maximum))))

    inventory_data = data.get("inventory", {})
    saved_slots = inventory_data.get("slots", [])
    for i in range(config.SLOT_COUNT):
        inventory.slots[i] = None
        if i < len(saved_slots) and isinstance(saved_slots[i], dict):
            item_id = saved_slots[i].get("id")
            count = int(saved_slots[i].get("count", 1))
            if item_id in ITEMS and count >= 1:
                inventory.slots[i] = {"id": item_id, "count": count}
    inventory.select(int(inventory_data.get("selected", 0)))
    inventory.gold = int(inventory_data.get("gold", config.START_GOLD))

    farm.soil = {}
    for entry in data.get("farm", []):
        crop = entry.get("crop")
        if crop is not None:
            if crop.get("seed") not in config.CROPS:
                continue
            crop = {"seed": crop["seed"], "days": int(crop.get("days", 0))}
        farm.soil[(int(entry["x"]), int(entry["y"]))] = {
            "watered": bool(entry.get("watered", False)),
            "crop": crop,
            "idle": int(entry.get("idle", 0)),
        }

    apiary.hives = {}
    for entry in data.get("hives", []):
        tx, ty = int(entry["x"]), int(entry["y"])
        apiary.hives[(tx, ty)] = {"days": int(entry.get("days", 0))}
        world.add_blocker(tx, ty)

    for cow, milk_ready in zip(cows, data.get("cows", [])):
        cow.milk_ready = bool(milk_ready)

    story.flags = set(str(flag) for flag in data.get("story", []))
