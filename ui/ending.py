"""The ending screen: shown when the story ends (a bad ending for now), then back to the title screen."""

import pygame
import config
from ui import theme
from ui.dialogue import wrap_text

# ending flag -> (title, text). Add the next endings here.
ENDINGS = {
    "bad_end_1": ("Bad End: Cold Shoulder",
                  "You never really joined in. Trying to make friends here felt like a waste of time, "
                  "so you packed your things and left. The valley carried on without you."),
}


def find_ending(story):
    """Return the id of the ending that was reached, or None."""
    for flag in ENDINGS:
        if story.has(flag):
            return flag
    return None


class EndingScreen:
    """A dark full-screen text, closed with a click or a key (the game then returns to the title screen)."""

    def __init__(self):
        """Start closed."""
        self.is_open = False
        self.title = ""
        self.text = ""

    def open(self, ending_id):
        """Show the ending with this id."""
        self.is_open = True
        self.title, self.text = ENDINGS[ending_id]

    def draw(self, screen, font, small_font):
        """Cover the game with black and write the ending in the middle."""
        if not self.is_open:
            return
        screen.fill((10, 8, 12))
        width = screen.get_width()
        theme.draw_text(screen, font, self.title, config.TEXT_LIGHT, (width // 2, 150), "center", True)
        y = 220
        for line in wrap_text(self.text, small_font, 560):
            theme.draw_text(screen, small_font, line, config.TEXT_LIGHT, (width // 2, y), "center", True)
            y += small_font.get_height() + 6
        bob = (pygame.time.get_ticks() // 400) % 2 * 3
        theme.draw_text(screen, small_font, "Press E or click to return to the title screen", config.TEXT_DIM,
                        (width // 2, screen.get_height() - 80 + bob), "center", True)
