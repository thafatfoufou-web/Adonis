import pygame
import json

SLOT_COUNT = 10
SLOT_SIZE = 48
SLOT_GAP = 4

def load_items(path):
    """Read the item file and return a dictionary: item id -> item data."""
    with open(path) as f:
        items = json.load(f)

    for item in items.values():
        item["color"] = tuple(item["color"])
    return items


ITEMS = load_items("data/items.json")


class Inventory:
    def __init__(self):
        self.slots = [None] * SLOT_COUNT
        self.selected = 0
        self.gold = 100

    def add_item(self, item_id, count=1):
        # stackable items join an existing stack if there is one
        if ITEMS[item_id]["stackable"]:
            for slot in self.slots:
                if slot is not None and slot["id"] == item_id:
                    slot["count"] += count
                    return True
        # otherwise take the first empty slot
        for i in range(SLOT_COUNT):
            if self.slots[i] is None:
                self.slots[i] = {"id": item_id, "count": count}
                return True
        return False  # inventory full

    def get_selected(self):
        return self.slots[self.selected]

    def get_selected_name(self):
        slot = self.get_selected()
        if slot is None:
            return "Empty hand"
        return ITEMS[slot["id"]]["name"]

    def remove_one_selected(self):
        # uses one item of the selected slot, empties the slot at 0
        slot = self.slots[self.selected]
        if slot is None:
            return
        slot["count"] -= 1
        if slot["count"] <= 0:
            self.slots[self.selected] = None

    def select(self, index):
        if 0 <= index < SLOT_COUNT:
            self.selected = index

    def scroll(self, direction):
        self.selected = (self.selected + direction) % SLOT_COUNT

    def draw(self, screen, font):
        total_width = SLOT_COUNT * (SLOT_SIZE + SLOT_GAP) - SLOT_GAP
        start_x = (screen.get_width() - total_width) // 2
        y = screen.get_height() - SLOT_SIZE - 8

        for i, slot in enumerate(self.slots):
            x = start_x + i * (SLOT_SIZE + SLOT_GAP)
            rect = pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)
            pygame.draw.rect(screen, (40, 40, 40), rect)

            if slot is not None:
                data = ITEMS[slot["id"]]
                inner = rect.inflate(-16, -16)
                pygame.draw.rect(screen, data["color"], inner)
                if slot["count"] > 1:
                    text = font.render(str(slot["count"]), True, (255, 255, 255))
                    screen.blit(text, (rect.right - text.get_width() - 3,
                                       rect.bottom - text.get_height() - 2))

            if i == self.selected:
                pygame.draw.rect(screen, (255, 220, 60), rect, 3)
            else:
                pygame.draw.rect(screen, (120, 120, 120), rect, 1)