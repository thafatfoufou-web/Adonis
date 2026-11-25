"""Visits: a villager turns up next to the player and starts the quest dialogue.

quests.py starts a quest with a "visit" in the morning and remembers that the visit is waiting.
Here the villager leaves the schedule and appears right next to the player (at the door, when you wake up),
opens the quest's dialogue, sets its flags and gives its items.
A visit can have "with": ["tom"]: those villagers appear too and stay until the talk is over.
"""

import config
from world.pathfinding import find_path

GIVE_UP_SECONDS = 25     # safety net: if the villager is somehow not next to the player after this long, place them there


class Visits:
    """The visit in progress, if any."""

    def __init__(self):
        """Nobody is walking over yet."""
        self.current = None      # {"quest", "npc", "visit", "elapsed", "target", "warned"}

    def get_free_tile_near(self, world, tile, taken=()):
        """Return a walkable tile next to the given tile that nobody stands on (or the tile itself if all are blocked)."""
        for radius in (1, 2, 3):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if max(abs(dx), abs(dy)) != radius:
                        continue
                    spot = (tile[0] + dx, tile[1] + dy)
                    if spot not in taken and not world.is_solid(spot[0], spot[1]):
                        return spot
        return tile

    def begin(self, quests, npcs, world, player_tile):
        """Pick the next waiting visit and make its villager (and companions) appear next to the player."""
        for quest_id in quests.pending_visits():
            visit = quests.by_id[quest_id]["visit"]
            npc = next((n for n in npcs if n.id == visit["npc"]), None)
            if npc is None:                         # no such villager: do not block the quest
                quests.finish_visit(quest_id)
                continue
            npc.visiting = True
            npc.put_on_tile(self.get_free_tile_near(world, player_tile))
            taken = {npc.tile, player_tile}
            companions = [n for n in npcs if n.id in visit.get("with", [])]
            for friend in companions:
                friend.visiting = True
                friend.put_on_tile(self.get_free_tile_near(world, player_tile, taken))
                taken.add(friend.tile)
            self.current = {"quest": quest_id, "npc": npc, "friends": companions, "visit": visit, "elapsed": 0.0, "target": None, "warned": False}
            return

    def walk_toward(self, world, player_tile):
        """Walk toward the player and stop next to them. Placed next to the player after too long."""
        npc = self.current["npc"]
        self.current["elapsed"] += self.dt
        if self.current["target"] != player_tile:
            self.current["target"] = player_tile
            path = find_path(world, npc.tile, player_tile)
            npc.path = path[:-1]                     # the last tile is the player's own
        if self.current["elapsed"] > GIVE_UP_SECONDS or (not npc.path and not self.is_next_to(npc, player_tile)):
            if self.current["elapsed"] > 3:
                npc.put_on_tile(self.get_free_tile_near(world, player_tile))

    def is_next_to(self, npc, player_tile):
        """Return True if the villager stands on a tile touching the player (diagonals count)."""
        return max(abs(npc.tile[0] - player_tile[0]), abs(npc.tile[1] - player_tile[1])) <= 1

    def update(self, dt, quests, npcs, player, world, inventory, story, say, notice):
        """Call every frame while the game runs. say(name, lines) opens the dialogue box; notice(text) shows a short message."""
        self.dt = dt
        if self.current is None:
            self.begin(quests, npcs, world, player.get_tile())
            if self.current is None:
                return

        npc = self.current["npc"]
        visit = self.current["visit"]
        player_tile = player.get_tile()

        if not self.is_next_to(npc, player_tile):
            self.walk_toward(world, player_tile)
            return

        # arrived: wait for room in the hotbar if the villager brings a gift
        gifts = visit.get("gives", [])
        if not all(inventory.can_add(gift["item"]) for gift in gifts):
            if not self.current["warned"]:
                notice("Your hotbar is full. Make some room, " + npc.name + " has something for you.")
                self.current["warned"] = True
            return

        quest_id = self.current["quest"]
        say(npc.name, visit["lines"])
        quests.finish_visit(quest_id)
        story.set("chat_" + npc.id + "_today")      # the visit counts as today's chat with them
        for gift in gifts:
            inventory.add_item(gift["item"], gift.get("count", 1))
        npc.end_visit()
        for friend in self.current["friends"]:
            friend.end_visit()
        self.current = None