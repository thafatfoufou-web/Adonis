"""NPC dialogues: loading the lines and the dialogue box."""

import json
import pygame
import config
from ui import theme


def load_dialogues(path):
    """Read the dialogue file and return a dictionary: npc id -> list of entries."""
    with open(path) as f:
        data = json.load(f)
    return data


def entry_matches(entry, game_time, story):
    """Return True if every condition of a dialogue entry is met.

    All the conditions are optional:
      "day_min":  the day number must be at least this one
      "requires": story flags that must all be set
      "forbids":  story flags that must not be set
      "time":     "day" or "night"
    """
    if game_time.day < entry.get("day_min", 1):
        return False
    for flag in entry.get("requires", []):
        if not story.has(flag):
            return False
    for flag in entry.get("forbids", []):
        if story.has(flag):
            return False

    when = entry.get("time")
    if when == "night" and not game_time.is_night():
        return False
    if when == "day" and game_time.is_night():
        return False
    return True


def pick_entry(dialogues, npc_id, game_time, story):
    """Return the dialogue entry an NPC says right now.

    The entries of an NPC are checked in order and the last one whose conditions
    are all met wins. So put the general entries first and the special ones after.
    An entry can also have "sets": story flags that are set when it is said.
    """
    chosen = None
    for entry in dialogues.get(npc_id, []):
        if entry_matches(entry, game_time, story):
            chosen = entry

    if chosen is None:
        return {"lines": ["..."]}
    return chosen


def wrap_text(text, font, max_width):
    """Cut a long text into lines that each fit in max_width pixels."""
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
        """Start a conversation by showing the first line."""
        self.is_open = True
        self.speaker = speaker
        self.lines = lines
        self.index = 0

    def close(self):
        """Close the box right away."""
        self.is_open = False

    def advance(self):
        """Go to the next line and close the box after the last one."""
        self.index += 1
        if self.index >= len(self.lines):
            self.is_open = False

    def handle_key(self, key):
        """Esc closes the box; the interact keys show the next line."""
        if key == pygame.K_ESCAPE:
            self.close()
        elif key in config.INTERACT_KEYS:
            self.advance()

    def handle_click(self):
        """Show the next line on a left click."""
        self.advance()

    def draw(self, screen, font, small_font):
        """Draw the box, the speaker's name plate, the current line and a bobbing arrow."""
        if not self.is_open:
            return

        margin = config.DIALOGUE_BOX_MARGIN
        box = pygame.Rect(margin, config.DIALOGUE_BOX_Y,
                          screen.get_width() - 2 * margin, config.DIALOGUE_BOX_HEIGHT)
        inner = theme.draw_panel(screen, box)

        plate = pygame.Rect(box.x + 24, box.y - 16, font.size(self.speaker)[0] + 32, 32)
        theme.draw_frame(screen, plate)
        theme.draw_text(screen, font, self.speaker, config.ACCENT, plate.center, anchor="center")

        padding = config.DIALOGUE_TEXT_PADDING
        text_x = inner.x + padding
        text_width = inner.width - 2 * padding
        line_y = inner.y + 26
        for row in wrap_text(self.lines[self.index], font, text_width):
            theme.draw_text(screen, font, row, config.TEXT, (text_x, line_y))
            line_y += config.DIALOGUE_LINE_SPACING

        bob = (pygame.time.get_ticks() // 400) % 2 * 3
        x = inner.right - 26
        y = inner.bottom - 22 + bob
        points = [(x - 7, y - 4), (x + 7, y - 4), (x, y + 5)]
        shadow = [(px + 1, py + 1) for px, py in points]
        pygame.draw.polygon(screen, config.OUTLINE, shadow)
        pygame.draw.polygon(screen, config.ACCENT, points)
