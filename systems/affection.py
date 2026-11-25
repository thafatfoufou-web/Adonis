"""Friendship with the villagers: hearts, gifts and what each villager thinks of them.

Every villager has friendship points. 150 points make one heart (see config.AFFECTION), up to 3 hearts:
one for each step of the affection ladder in the Character Sheet.
Points come from the first chat of the day and from gifts (one gift per villager per day).
Reaching a heart sets the story flag "<npc id>_hearts_<n>" (for example "mira_hearts_4"), so a line or a
quest in dialogues.json / quests.json can wait for it with "requires": ["mira_hearts_4"].

The likes and dislikes, and what each villager says about each gift, are written in data/gifts.json.
"""

import json
import random
import config
from systems.items import ITEMS


class Affection:
    """Friendship points of every villager, and who got a gift or a chat today."""

    def __init__(self, path):
        """Read the gift preferences. Everybody starts at 0 hearts."""
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        self.prefs = data["npcs"]
        self.reactions = data["reactions"]
        self.npc_reactions = data.get("npc_reactions", {})
        self.gift_lines = data.get("lines", {})       # npc id -> item id -> what that villager says about that gift
        self.points = {}              # npc id -> friendship points
        self.gifted_today = set()     # villagers who already got a gift today
        self.talked_today = set()     # villagers whose first chat of the day already counted

    def check_data(self, known_npcs=None):
        """Return a list of problems in gifts.json (unknown item ids, an item in two tiers, a line for nothing).

        An empty list means the file is fine. main.py prints the problems when the game starts.
        """
        problems = []
        for npc_id, prefs in self.prefs.items():
            if known_npcs is not None and npc_id not in known_npcs:
                problems.append("gifts.json: unknown villager '" + npc_id + "'")
            seen = {}
            for tier, item_ids in prefs.items():
                for item_id in item_ids:
                    if item_id not in ITEMS:
                        problems.append(npc_id + ": '" + item_id + "' (" + tier + ") is not in items.json")
                    elif item_id in seen:
                        problems.append(npc_id + ": '" + item_id + "' is in both " + seen[item_id] + " and " + tier)
                    seen[item_id] = tier
            for item_id in self.gift_lines.get(npc_id, {}):
                if item_id not in ITEMS:
                    problems.append(npc_id + ": line for '" + item_id + "', which is not in items.json")
        for npc_id in self.gift_lines:
            if npc_id not in self.prefs:
                problems.append("gifts.json: lines for '" + npc_id + "', who has no entry in 'npcs'")
        return problems

    # ----- asking questions -------------------------------------------------------

    def get_points(self, npc_id):
        """Return the friendship points of a villager."""
        return self.points.get(npc_id, 0)

    def get_hearts(self, npc_id):
        """Return the full hearts of a villager (0 to 3)."""
        return min(self.get_points(npc_id) // config.AFFECTION["heart_points"], config.AFFECTION["max_hearts"])

    def get_tier(self, npc_id, item_id):
        """Return what the villager thinks of an item: "love", "like", "dislike" or "neutral"."""
        prefs = self.prefs.get(npc_id, {})
        item_id = ITEMS[item_id].get("gift_as", item_id)      # mad honey counts as honey: it is only "Honey" to the player
        for tier in ("love", "like", "dislike", "neutral"):
            if item_id in prefs.get(tier, []):
                return tier
        return "neutral"

    def can_gift_item(self, item_id):
        """Return (True, "") if the item can be given away, otherwise (False, the reason to show)."""
        item = ITEMS[item_id]
        if item["type"] not in config.AFFECTION["giftable_types"]:
            return False, "That is not a gift."
        return True, ""

    # ----- changing friendship ----------------------------------------------------

    def add_points(self, npc_id, amount, story):
        """Change a villager's points (never below 0, never above the maximum) and set the heart flags.

        Return how many hearts the villager gained (0 if none).
        """
        before = self.get_hearts(npc_id)
        cap = config.AFFECTION["max_hearts"] * config.AFFECTION["heart_points"]
        self.points[npc_id] = max(0, min(cap, self.get_points(npc_id) + amount))
        after = self.get_hearts(npc_id)
        for heart in range(1, after + 1):
            story.set(npc_id + "_hearts_" + str(heart))
        return max(0, after - before)

    def talk(self, npc_id, story):
        """The player talked to a villager. The first chat of the day gives a few points.

        Return the hearts gained.
        """
        if npc_id in self.talked_today:
            return 0
        self.talked_today.add(npc_id)
        return self.add_points(npc_id, config.AFFECTION["talk_points"], story)

    def give(self, npc_id, item_id, story, player_name):
        """Give an item to a villager.

        Returns a dictionary: {"ok": False, "text": why not}, or
        {"ok": True, "tier", "lines" (what the villager says), "hearts_gained", "hearts"}.
        The caller takes the item out of the inventory when "ok" is True.
        """
        allowed, reason = self.can_gift_item(item_id)
        if not allowed:
            return {"ok": False, "text": reason}
        if npc_id in self.gifted_today:
            return {"ok": False, "text": "They already got a gift from you today."}

        tier = self.get_tier(npc_id, item_id)
        self.gifted_today.add(npc_id)
        gained = self.add_points(npc_id, config.AFFECTION["gift_points"][tier], story)

        gift_id = ITEMS[item_id].get("gift_as", item_id)       # mad honey gets the lines of honey
        own = self.gift_lines.get(npc_id, {}).get(gift_id)      # 1. this villager's line for this exact gift
        if own is None:
            own = self.npc_reactions.get(npc_id, {}).get(tier)  # 2. this villager's line for the tier
        line = own if own is not None else random.choice(self.reactions[tier])   # 3. a general line for the tier
        line = line.replace("{player}", player_name)
        name = ITEMS[item_id]["name"].lower()
        pieces = line.split("{item}")
        line = pieces[0]
        for piece in pieces[1:]:
            before = line.rstrip(" ")
            starts_sentence = before == "" or before.endswith(("!", "?")) or (before.endswith(".") and not before.endswith("..."))
            line += (name[0].upper() + name[1:] if starts_sentence else name) + piece
        line = line[0].upper() + line[1:]
        return {"ok": True, "tier": tier, "lines": [line], "hearts_gained": gained, "hearts": self.get_hearts(npc_id)}

    def new_day(self):
        """A new day: everybody can get a gift and a chat again."""
        self.gifted_today = set()
        self.talked_today = set()

    # ----- saving -----------------------------------------------------------------

    def to_dict(self):
        """Return the friendships as a dictionary that can be saved as JSON."""
        return {"points": dict(self.points), "gifted_today": sorted(self.gifted_today),
                "talked_today": sorted(self.talked_today)}

    def load(self, data):
        """Put saved friendships back. Broken entries are skipped."""
        self.points = {}
        self.gifted_today = set()
        self.talked_today = set()
        if not isinstance(data, dict):
            return
        points = data.get("points", {})
        if isinstance(points, dict):
            for npc_id, value in points.items():
                try:
                    self.points[str(npc_id)] = max(0, int(value))
                except (TypeError, ValueError):
                    pass
        self.gifted_today = set(str(npc_id) for npc_id in data.get("gifted_today", []))
        self.talked_today = set(str(npc_id) for npc_id in data.get("talked_today", []))
