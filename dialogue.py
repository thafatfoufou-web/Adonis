import json
import pygame
from controls import INTERACT_KEYS

BOX_HEIGHT = 130
BOX_MARGIN = 20
BOX_Y = 320
TEXT_PADDING = 20
LINE_SPACING = 28


def load_dialogues(path):
    """Read the dialogue file and return a dictionary: npc id -> list of entries."""
    with open(path) as f:
        data = json.load(f)
    return data


def get_lines(dialogues, npc_id, day):
    """Return the lines an NPC says on the given day.

    We go through the entries in order and keep the last one
    whose day_min is already reached.
    """
    entries = dialogues.get(npc_id)
    if entries is None:
        return ["..."]

    chosen = entries[0]
    for entry in entries:
        if day >= entry["day_min"]:
            chosen = entry
    return chosen["lines"]


def wrap_text(text, font, max_width):
    """Cut a long text into a list of lines that each fit in max_width pixels."""
    words = text.split()
    lines = []
    current = ""

    for word in words:
        if current == "":
            test = word
        else:
            test = current + " " + word

        width = font.size(test)[0]
        fits = width <= max_width

        # a single word too long for the box is accepted, to avoid an empty line
        if fits or current == "":
            current = test
        else:
            lines.append(current)
            current = word

    if current != "":
        lines.append(current)
    return lines


class DialogueBox:
    """The box at the bottom of the screen where an NPC speaks."""

    def __init__(self):
        """Create a closed dialogue box."""
        self.is_open = False
        self.speaker = ""
        self.lines = []
        self.index = 0

    def open(self, speaker, lines):
        """Start a conversation: show the first line of the list."""
        self.is_open = True
        self.speaker = speaker
        self.lines = lines
        self.index = 0

    def close(self):
        """Close the box right away."""
        self.is_open = False

    def advance(self):
        """Go to the next line, and close the box after the last one."""
        self.index += 1
        if self.index >= len(self.lines):
            self.is_open = False

    def handle_key(self, key):
        """React to a key while the box is open: Esc closes, the action keys continue."""
        if key == pygame.K_ESCAPE:
            self.close()
        elif key in INTERACT_KEYS:
            self.advance()

    def handle_click(self):
        """React to a left click while the box is open: show the next line."""
        self.advance()

    def draw(self, screen, font, small_font):
        """Draw the box, the speaker name, the current line and a small hint."""
        if not self.is_open:
            return

        box_width = screen.get_width() - 2 * BOX_MARGIN
        box = pygame.Rect(BOX_MARGIN, BOX_Y, box_width, BOX_HEIGHT)
        pygame.draw.rect(screen, (30, 30, 40), box)
        pygame.draw.rect(screen, (255, 220, 60), box, 3)

        text_x = box.x + TEXT_PADDING
        text_width = box.width - 2 * TEXT_PADDING

        name = font.render(self.speaker, True, (255, 220, 60))
        screen.blit(name, (text_x, box.y + 12))

        current_line = self.lines[self.index]
        wrapped = wrap_text(current_line, font, text_width)
        line_y = box.y + 48
        for row in wrapped:
            label = font.render(row, True, (255, 255, 255))
            screen.blit(label, (text_x, line_y))
            line_y += LINE_SPACING

        counter = str(self.index + 1) + "/" + str(len(self.lines))
        hint_text = "E / Enter / click: continue   Esc: close   " + counter
        hint = small_font.render(hint_text, True, (180, 180, 180))
        hint_y = box.bottom - 24
        screen.blit(hint, (text_x, hint_y))