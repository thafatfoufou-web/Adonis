"""The player's hotbar slots and gold."""

import config
from systems.items import ITEMS


class Inventory:
    """Ten item slots (the hotbar), the selected slot and the gold."""

    def __init__(self):
        """Create an empty inventory with the starting gold."""
        self.slots = [None] * config.SLOT_COUNT
        self.selected = 0
        self.gold = config.START_GOLD

    def add_item(self, item_id, count=1):
        """Add items to a stack or an empty slot. Return False if the inventory is full."""
        if ITEMS[item_id]["stackable"]:
            for slot in self.slots:
                if slot is not None and slot["id"] == item_id:
                    slot["count"] += count
                    return True
        for i in range(config.SLOT_COUNT):
            if self.slots[i] is None:
                self.slots[i] = {"id": item_id, "count": count}
                return True
        return False

    def get_selected(self):
        """Return the selected slot ({"id", "count"}) or None if it is empty."""
        return self.slots[self.selected]

    def get_selected_name(self):
        """Return the name of the held item, or 'Empty hand'."""
        slot = self.get_selected()
        if slot is None:
            return "Empty hand"
        return ITEMS[slot["id"]]["name"]

    def remove_one_selected(self):
        """Use one item of the selected slot and empty the slot when it reaches 0."""
        slot = self.slots[self.selected]
        if slot is None:
            return
        slot["count"] -= 1
        if slot["count"] <= 0:
            self.slots[self.selected] = None
    def can_add(self, item_id):
        """Return True if one more item of this kind fits (in an existing stack or an empty slot)."""
        if ITEMS[item_id]["stackable"]:
            for slot in self.slots:
                if slot is not None and slot["id"] == item_id:
                    return True
        return None in self.slots
    
    def count_item(self, item_id):
        """Return how many items of this kind the player carries."""
        return sum(slot["count"] for slot in self.slots if slot is not None and slot["id"] == item_id)

    def remove_item(self, item_id, count=1):
        """Take count items of this kind out of the slots."""
        for i in range(config.SLOT_COUNT):
            slot = self.slots[i]
            if slot is not None and slot["id"] == item_id:
                taken = min(slot["count"], count)
                slot["count"] -= taken
                count -= taken
                if slot["count"] <= 0:
                    self.slots[i] = None
                if count == 0:
                    return

    def select(self, index):
        """Select the slot at index if it exists."""
        if 0 <= index < config.SLOT_COUNT:
            self.selected = index

    def scroll(self, direction):
        """Move the selection by direction slots, wrapping around."""
        self.selected = (self.selected + direction) % config.SLOT_COUNT

    
