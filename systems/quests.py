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

  "deliver": done when the player has handed in enough items (see "delivery" below)
           {"type": "deliver", "items": ["carrot", "pumpkin"], "count": 10, "min_kinds": 2}

A quest can also have a "delivery": the player hands items to an NPC in as many trips as they like.
  {"npc": "mira", "wait_lines": [{"day_min": 29, "lines": [...]}], "thanks_lines": [...], "done_lines": [...]}
Every "deliver" goal of the quest is filled from the inventory when the player talks to that NPC. With "min_kinds"
the player can never hand in so many of one kind that the other kinds could no longer reach the minimum.

A quest's "start" can have "expires_day": after that day the quest can no longer start (it simply never appears).

A quest can have "reminders": [{"day": 33, "text": "...", "mood": "good"}], notices shown once on that morning,
and "deadline_day": the quest fails when that day is over (the tracker shows the days left).

A quest can also have a "visit": the villager walks to the player and talks first thing in the morning.
  {"npc": "walter", "notice": "Walter is coming to see you.", "lines": [...],
   "sets": ["some_flag"], "gives": [{"item": "beehive", "count": 1}]}
A quest with a visit only starts in the morning (see update), so the villager is there when you wake up.
systems/visits.py walks the villager over; this file only remembers that a visit is waiting ("visit_pending").
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
        if kind == "deliver":
            given = {} if entry is None else entry.get("delivered", {}).get(goal["id"], {})
            total = sum(given.values())
            kinds = sum(1 for amount in given.values() if amount > 0)
            current = min(total, goal["count"])
            if current >= goal["count"] and kinds < goal.get("min_kinds", 1):
                current = goal["count"] - 1      # enough items, but not enough different kinds
            return (current, goal["count"])
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

    def can_start(self, quest, day, morning=True):
        """Return True if the quest has not started and all its conditions are met.

        A quest with a "visit" also waits for the morning, so the villager can come to the player's door.
        """
        start = quest.get("start", {})
        if day < start.get("day", 1):
            return False
        if "expires_day" in start and day > start["expires_day"]:
            return False                      # the chance has gone: the quest never starts
        if "visit" in quest and not morning:
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
        self.state[quest["id"]] = {"status": "active", "progress": {}, "marks": {}, "visit_pending": "visit" in quest,
                                   "delivered": {}, "reminded": []}
        self.story.set(quest["id"] + "_started")
        self.story.set_many(quest.get("on_start", {}).get("sets", []))
        self.messages.append(("New quest: " + quest["title"], "good"))
        if "visit" in quest and quest["visit"].get("notice"):
            self.messages.append((quest["visit"]["notice"], "good"))

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

    def update(self, day, morning=True):
        """Start the quests whose time has come, finish the ones whose goals are done, check deadlines.

        Call it every frame. A quest finishing can start the next one in the same call.
        morning is True during the first hours of a day: quests with a "visit" only start then.
        """
        self.today = day
        changed = True
        while changed:
            changed = False
            for quest in self.defs:
                quest_id = quest["id"]
                status = self.status(quest_id)
                if status is None:
                    if self.can_start(quest, day, morning):
                        self.start(quest)
                        changed = True
                elif status == "active":
                    self.mark_waits(quest)
                    self.send_reminders(quest, day)
                    if all(self.goal_done(quest_id, goal) for goal in quest["goals"]):
                        self.complete(quest)
                        changed = True
                    elif "deadline_day" in quest and day > quest["deadline_day"]:
                        self.fail(quest)
                        changed = True

    def send_reminders(self, quest, day):
        """Show each reminder of the quest once, on the morning of its day (and not again after loading a save)."""
        reminded = self.state[quest["id"]].setdefault("reminded", [])
        for reminder in quest.get("reminders", []):
            if reminder["day"] == day and day not in reminded:
                reminded.append(day)
                self.messages.append((reminder["text"], reminder.get("mood", "good")))

    def days_left(self, quest):
        """Return the number of days left including today, or None if the quest has no deadline."""
        if "deadline_day" not in quest:
            return None
        return max(0, quest["deadline_day"] - self.today + 1)

    # ----- delivery: handing items to an NPC over several trips -----------------------

    def deliver_goals(self, quest):
        """Return the goals of the quest that are filled by handing items in."""
        return [goal for goal in quest["goals"] if goal["type"] == "deliver"]

    def missing_text(self, quest):
        """Return a sentence listing what is still missing, like '4 vegetables and 1 milk'."""
        parts = []
        for goal in self.deliver_goals(quest):
            current, total = self.get_progress(quest["id"], goal)
            if current < total:
                left = total - current
                label = goal.get("label", goal["id"]) if left != 1 else goal.get("label_one", goal.get("label", goal["id"]))
                parts.append(str(left) + " " + label)
        return " and ".join(parts) if len(parts) < 3 else ", ".join(parts[:-1]) + " and " + parts[-1]

    def try_delivery(self, npc_id, inventory):
        """Called when the player talks to an NPC. Take what the quest still needs from the inventory.

        Returns the lines to say, or None if no active quest takes deliveries from this NPC.
        """
        for quest in self.defs:
            if self.status(quest["id"]) != "active":
                continue
            delivery = quest.get("delivery")
            if delivery is None or delivery["npc"] != npc_id:
                continue
            given_all = self.state[quest["id"]].setdefault("delivered", {})
            handed = 0
            for goal in self.deliver_goals(quest):
                given = given_all.setdefault(goal["id"], {})
                cap = goal["count"] - (goal.get("min_kinds", 1) - 1)     # most we accept of one kind
                for item_id in goal["items"]:
                    room = goal["count"] - sum(given.values())
                    take = min(inventory.count_item(item_id), room, cap - given.get(item_id, 0))
                    if take > 0:
                        inventory.remove_item(item_id, take)
                        given[item_id] = given.get(item_id, 0) + take
                        handed += take
            missing = self.missing_text(quest)
            if missing == "":
                return list(delivery["done_lines"])
            if handed > 0:
                return [line.replace("{missing}", missing) for line in delivery["thanks_lines"]]
            lines = []
            for option in delivery["wait_lines"]:
                if self.today >= option.get("day_min", 1):
                    lines = option["lines"]
            return [line.replace("{missing}", missing) for line in lines]
        return None

    # ----- visits: a villager comes to the player's door -------------------------------

    def pending_visits(self):
        """Return the ids of the quests whose visit has not happened yet, in quest order."""
        return [quest["id"] for quest in self.defs
                if self.state.get(quest["id"], {}).get("visit_pending")]

    def finish_visit(self, quest_id):
        """The villager has talked: set the visit's flags and forget the visit."""
        self.state[quest_id]["visit_pending"] = False
        self.story.set_many(self.by_id[quest_id]["visit"].get("sets", []))

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

    def get_tracker(self, limit=4):
        """Return what the interface shows: a list of (title, [goal lines]) for the active quests."""
        tracker = []
        for quest in self.defs:
            if self.status(quest["id"]) != "active":
                continue
            title = quest["title"]
            if not quest.get("required", True):
                title += " (optional)"
            left = self.days_left(quest)
            if left is not None:
                title += " - last day!" if left == 1 else " - " + str(left) + " days left"
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

    def get_log(self):
        """Return what the quest log shows: a list of (title, [(goal text, done), ...]) for the active quests."""
        log = []
        for quest in self.defs:
            if self.status(quest["id"]) != "active":
                continue
            title = quest["title"]
            if not quest.get("required", True):
                title += " (optional)"
            left = self.days_left(quest)
            if left is not None:
                title += " - last day!" if left == 1 else " - " + str(left) + " days left"
            goals = []
            for goal in quest["goals"]:
                current, total = self.get_progress(quest["id"], goal)
                text = goal["text"]
                if total > 1 and current < total:
                    text += " (" + str(current) + "/" + str(total) + ")"
                goals.append((text, current >= total))
            log.append((title, goals))
        return log

    def get_next_goal(self):
        """Return the text of the next goal to do (required quests first), or None when nothing is active."""
        for required in (True, False):
            for quest in self.defs:
                if self.status(quest["id"]) != "active" or quest.get("required", True) != required:
                    continue
                for goal in quest["goals"]:
                    current, total = self.get_progress(quest["id"], goal)
                    if current < total:
                        return goal["text"] + (" (" + str(current) + "/" + str(total) + ")" if total > 1 else "")
        return None

    def count_done(self):
        """Return how many quests are finished."""
        return sum(1 for quest in self.defs if self.status(quest["id"]) == "done")

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
                    delivered = entry.get("delivered", {})
                    reminded = entry.get("reminded", [])
                    self.state[quest_id] = {"status": status, "progress": dict(progress), "marks": dict(marks),
                                            "delivered": dict(delivered) if isinstance(delivered, dict) else {},
                                            "reminded": list(reminded) if isinstance(reminded, list) else [],
                                            "visit_pending": bool(entry.get("visit_pending", False)) and "visit" in self.by_id[quest_id]}