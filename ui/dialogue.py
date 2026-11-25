"""NPC dialogues: loading the lines and the dialogue box."""

import json
import random
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
      "daily":    a get-to-know-you chat: only once per day per villager (see pick_entry)
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
        if entry.get("daily") and story.has(chat_flag(npc_id)):
            continue                      # already had today's chat with this villager
        if entry_matches(entry, game_time, story):
            chosen = entry

    if chosen is None:
        return {"lines": ["..."]}
    return chosen

def chat_flag(npc_id):
    """Return the story flag that says the player already had today's chat with this villager."""
    return "chat_" + npc_id + "_today"


def entry_lines(entry):
    """Return the lines to say: the entry's "lines", or one of its "variants" picked at random (for idle chatter)."""
    if "variants" in entry:
        return list(random.choice(entry["variants"]))
    return list(entry["lines"])


def personalize(lines, player_name):
    """Return the lines with {player} replaced by the player's name."""
    return [line.replace("{player}", player_name) for line in lines]

SPEAKER_NAMES = ["Zoe", "Tom", "Ariane", "Maya", "Jonas", "Cyrus", "Clover", "Walter", "Martha"]


def split_speaker(line, default):
    """Return (speaker, text). A line that starts with a villager's name and a colon, like "Tom: Hello",
    is said by that villager; any other line is said by the default speaker of the box."""
    for name in SPEAKER_NAMES:
        if line.startswith(name + ": "):
            return name, line[len(name) + 2:]
    return default, line


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

def get_style(speaker):
    """Return (box picture, text color, name color) for a speaker: the colored box of a villager listed
    in config.DIALOGUE_STYLES, or the plain cream box for everybody else."""
    style = config.DIALOGUE_STYLES.get(speaker)
    if style is None:
        return "panel", config.TEXT, config.ACCENT
    return style["piece"], style["text"], style["name"]
        
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

        speaker, current_line = split_speaker(self.lines[self.index], self.speaker)
        margin = config.DIALOGUE_BOX_MARGIN
        box = pygame.Rect(margin, config.DIALOGUE_BOX_Y,
                          screen.get_width() - 2 * margin, config.DIALOGUE_BOX_HEIGHT)
        piece, text_color, name_color = get_style(speaker)
        theme.draw_piece(screen, box, piece)
        border = config.PANEL_BORDER
        inner = box.inflate(-2 * border, -2 * border)

        plate_height = font.get_height() + 12
        plate = pygame.Rect(box.x + 24, box.y - plate_height // 2, font.size(speaker)[0] + 36, plate_height)
        theme.draw_piece(screen, plate, piece)
        theme.draw_text(screen, font, speaker, name_color, (plate.centerx, plate.centery - 1), anchor="center")

        padding = config.DIALOGUE_TEXT_PADDING
        text_x = inner.x + padding
        text_width = inner.width - 2 * padding
        line_y = inner.y + 26
        for row in wrap_text(current_line, font, text_width):
            theme.draw_text(screen, font, row, text_color, (text_x, line_y))
            line_y += config.DIALOGUE_LINE_SPACING

        bob = (pygame.time.get_ticks() // 400) % 2 * 3
        x = inner.right - 26
        y = inner.bottom - 22 + bob
        points = [(x - 7, y - 4), (x + 7, y - 4), (x, y + 5)]
        pygame.draw.polygon(screen, name_color, points)
        
