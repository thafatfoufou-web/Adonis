"""Quests: starts quests, counts their progress, completes them or fails them.

The quests are described in data/quests.json. The engine talks to the rest of the game
in only two ways:
  - story flags (a quest can wait for a flag, and sets flags when it starts or ends:
    "<id>_started", "<id>_done" and "<id>_failed" are set automatically)
  - quests.notify("till"), quests.notify("sell", item="carrot", gold=40)... which main.py
    calls when the player does something.

Goal types in quests.json:
  "flag":  done when one story flag is set            {"type": "flag", "flag": "met_mira"}
  "flags": done when all the flags are set            {"type": "flags", "flags": [...]}
  "count": counts events with this name               {"type": "count", "event": "till", "count": 1}
           optional "items": only events whose item is in this list
           optional "sum": add up this value of the event (for example "gold") instead of counting 1
  "wait":  done N days after a flag was set           {"type": "wait", "after_flag": "barn_paid", "days": 4}

A quest can also have a "handin": the player gives gold and items to an NPC by talking to them.
  {"npc": "walter", "gold": 250, "items": {"wood": 5}, "done_flag": "barn_paid",
   "missing_lines": [...], "done_lines": [...]}
The missing_lines are said while the player does not have everything (so they are also the request).
"""

import json


class Quests:
    """All the quests, which of them are active or finished, and the progress of each."""

    def __init__(self, path, story):
        """Read the quest file. Nothing is started until update() is called."""
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        self.defs = data["quests"]
        self.by_id = {quest["id"]: quest for quest in self.defs}
        self.story = story
        self.state = {}          # quest id -> {"status": ..., "progress": {goal id: number}, "marks": {goal id: day}}
        self.messages = []       # short texts for main.py to show: (text, "good" or "bad")
        self.gold_to_give = 0    # gold rewards waiting to be paid by main.py
        self.today = 1           # the current day, remembered from update()

    # ----- asking questions -----------------------------------------------------

    def status(self, quest_id):
        """Return "active", "done", "failed", or None if the quest has not started."""
        entry = self.state.get(quest_id)
        if entry is None:
            return None
        return entry["status"]

    def is_done(self, quest_id):
        """Return True if the quest is finished successfully."""
        return self.status(quest_id) == "done"

    def get_progress(self, quest_id, goal):
        """Return (current, total) for a goal."""
        kind = goal["type"]
        if kind == "flag":
            return (1 if self.story.has(goal["flag"]) else 0, 1)
        if kind == "flags":
            flags = goal["flags"]
            return (sum(1 for flag in flags if self.story.has(flag)), len(flags))
        entry = self.state.get(quest_id)
        if kind == "wait":
            marks = {} if entry is None else entry["marks"]
            if goal["id"] not in marks:
                return (0, goal["days"])
            return (max(0, min(self.today - marks[goal["id"]], goal["days"])), goal["days"])
        done = 0 if entry is None else entry["progress"].get(goal["id"], 0)
        return (min(done, goal["count"]), goal["count"])

    def goal_done(self, quest_id, goal):
        """Return True if a goal is finished."""
        current, total = self.get_progress(quest_id, goal)
        return current >= total

    # ----- starting, finishing, failing ------------------------------------------

    def can_start(self, quest, day):
        """Return True if the quest has not started and all its conditions are met."""
        start = quest.get("start", {})
        if day < start.get("day", 1):
            return False
        for other in start.get("after", []):
            if not self.is_done(other):
                return False
        for flag in start.get("requires", []):
            if not self.story.has(flag):
                return False
        for flag in start.get("forbids", []):
            if self.story.has(flag):
                return False
        return True

    def start(self, quest):
        """Make a quest active and set its start flags."""
        self.state[quest["id"]] = {"status": "active", "progress": {}, "marks": {}}
        self.story.set(quest["id"] + "_started")
        self.story.set_many(quest.get("on_start", {}).get("sets", []))
        self.messages.append(("New quest: " + quest["title"], "good"))

    def complete(self, quest):
        """Finish a quest: set its flags and queue its reward."""
        self.state[quest["id"]]["status"] = "done"
        reward = quest.get("on_complete", {})
        self.story.set(quest["id"] + "_done")
        self.story.set_many(reward.get("sets", []))
        self.gold_to_give += reward.get("gold", 0)
        self.messages.append((reward.get("message", "Quest complete: " + quest["title"]), "good"))

    def fail(self, quest):
        """Fail a quest (its deadline passed): set its failure flags."""
        self.state[quest["id"]]["status"] = "failed"
        result = quest.get("on_fail", {})
        self.story.set(quest["id"] + "_failed")
        self.story.set_many(result.get("sets", []))
        self.messages.append((result.get("message", "Quest failed: " + quest["title"]), "bad"))

    def mark_waits(self, quest):
        """Remember the day on which the flag of each "wait" goal was first seen."""
        marks = self.state[quest["id"]]["marks"]
        for goal in quest["goals"]:
            if goal["type"] == "wait" and goal["id"] not in marks and self.story.has(goal["after_flag"]):
                marks[goal["id"]] = self.today

    def update(self, day):
        """Start the quests whose time has come, finish the ones whose goals are done, check deadlines.

        Call it every frame. A quest finishing can start the next one in the same call.
        """
        self.today = day
        changed = True
        while changed:
            changed = False
            for quest in self.defs:
                quest_id = quest["id"]
                status = self.status(quest_id)
                if status is None:
                    if self.can_start(quest, day):
                        self.start(quest)
                        changed = True
                elif status == "active":
                    self.mark_waits(quest)
                    if all(self.goal_done(quest_id, goal) for goal in quest["goals"]):
                        self.complete(quest)
                        changed = True
                    elif "deadline_day" in quest and day > quest["deadline_day"]:
                        self.fail(quest)
                        changed = True

    def notify(self, event, **data):
        """Tell the quests that something happened, for example notify("sell", item="carrot", gold=40)."""
        for quest in self.defs:
            if self.status(quest["id"]) != "active":
                continue
            progress = self.state[quest["id"]]["progress"]
            for goal in quest["goals"]:
                if goal["type"] != "count" or goal["event"] != event:
                    continue
                if "items" in goal and data.get("item") not in goal["items"]:
                    continue
                amount = data.get(goal["sum"], 0) if "sum" in goal else 1
                progress[goal["id"]] = progress.get(goal["id"], 0) + amount

    def try_handin(self, npc_id, inventory):
        """Called when the player talks to an NPC. If an active quest wants gold or items from this NPC,
        take them when the player has everything and return the NPC's "done_lines". If something is
        missing, return the "missing_lines". Return None if no quest is waiting on this NPC.
        """
        for quest in self.defs:
            if self.status(quest["id"]) != "active":
                continue
            handin = quest.get("handin")
            if handin is None or handin["npc"] != npc_id or self.story.has(handin["done_flag"]):
                continue
            gold = handin.get("gold", 0)
            items = handin.get("items", {})
            enough = inventory.gold >= gold
            for item_id, count in items.items():
                if inventory.count_item(item_id) < count:
                    enough = False
            if not enough:
                return list(handin["missing_lines"])
            inventory.gold -= gold
            for item_id, count in items.items():
                inventory.remove_item(item_id, count)
            self.story.set(handin["done_flag"])
            self.story.set_many(handin.get("also_sets", []))
            return list(handin["done_lines"])
        return None

    # ----- things main.py and the interface ask for --------------------------------

    def pop_messages(self):
        """Return the waiting messages and forget them."""
        messages = self.messages
        self.messages = []
        return messages

    def take_gold(self):
        """Return the gold rewards waiting to be paid, and reset the counter."""
        gold = self.gold_to_give
        self.gold_to_give = 0
        return gold

    def get_tracker(self, limit=3):
        """Return what the interface shows: a list of (title, [goal lines]) for the active quests."""
        tracker = []
        for quest in self.defs:
            if self.status(quest["id"]) != "active":
                continue
            title = quest["title"]
            if not quest.get("required", True):
                title += " (optional)"
            lines = []
            for goal in quest["goals"]:
                current, total = self.get_progress(quest["id"], goal)
                if current >= total:
                    lines.append(goal["text"] + " (done)")
                elif total > 1:
                    lines.append(goal["text"] + " (" + str(current) + "/" + str(total) + ")")
                else:
                    lines.append(goal["text"])
            tracker.append((title, lines))
        return tracker[:limit]

    # ----- saving --------------------------------------------------------------

    def to_dict(self):
        """Return the quest progress as a dictionary that can be saved as JSON."""
        return {"state": self.state}

    def load(self, data):
        """Put saved progress back. Unknown quests and broken entries are skipped."""
        self.state = {}
        if not isinstance(data, dict):
            return
        saved = data.get("state", {})
        if not isinstance(saved, dict):
            return
        for quest_id, entry in saved.items():
            if quest_id in self.by_id and isinstance(entry, dict):
                status = entry.get("status")
                progress = entry.get("progress", {})
                marks = entry.get("marks", {})
                if status in ("active", "done", "failed") and isinstance(progress, dict) and isinstance(marks, dict):
                    self.state[quest_id] = {"status": status, "progress": dict(progress), "marks": dict(marks)}
