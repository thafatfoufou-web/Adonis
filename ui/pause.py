"""The pause menu: resume, save the game, or go back to the main menu (after a yes/no question)."""

import pygame
import config
from ui import theme


class PauseMenu:
    """A small window over the frozen game."""

    OPTIONS = ["Resume", "Save game", "Main menu"]
    ACTIONS = ["resume", "save", "ask_menu"]
    CONFIRM_OPTIONS = ["Yes, main menu", "No"]
    CONFIRM_ACTIONS = ["menu", "stay"]

    def __init__(self):
        """Start closed."""
        self.is_open = False
        self.confirming = False
        self.selected = 0
        self.message = ""
        self.message_color = config.GOOD
        self.dim = None

    def open(self):
        """Open the menu with the first button selected."""
        self.is_open = True
        self.confirming = False
        self.selected = 0
        self.message = ""

    def close(self):
        """Close the menu."""
        self.is_open = False

    def set_message(self, text, color):
        """Show a short result (like 'Game saved.') at the bottom of the window."""
        self.message = text
        self.message_color = color

    def get_options(self):
        """Return the button labels of the current page."""
        return self.CONFIRM_OPTIONS if self.confirming else self.OPTIONS

    def get_panel(self, screen):
        """Return the rectangle of the window, centered on the screen."""
        panel = pygame.Rect(0, 0, *config.PAUSE_PANEL_SIZE)
        panel.center = screen.get_rect().center
        return panel

    def get_button_rect(self, panel, index):
        """Return the rectangle of a button."""
        rect = pygame.Rect(0, 0, 260, 52)
        rect.centerx = panel.centerx
        top = 120 if self.confirming else 72
        rect.y = panel.y + top + index * (rect.height + 12)
        return rect

    def choose(self, index):
        """Use a button. Return "resume", "save" or "menu" when the game must act, else None."""
        if self.confirming:
            action = self.CONFIRM_ACTIONS[index]
        else:
            action = self.ACTIONS[index]

        if action == "ask_menu":
            self.confirming = True
            self.selected = 1          # "No" is selected first, to be safe
            self.message = ""
            return None
        if action == "stay":
            self.confirming = False
            self.selected = 0
            return None
        return action

    def handle_key(self, key):
        """Esc goes back (or resumes), up/down choose, the interact keys use the button."""
        count = len(self.get_options())
        if key == pygame.K_ESCAPE:
            if self.confirming:
                self.confirming = False
                self.selected = 0
                return None
            return "resume"
        if key in config.UP_KEYS:
            self.selected = (self.selected - 1) % count
        elif key in config.DOWN_KEYS:
            self.selected = (self.selected + 1) % count
        elif key in config.INTERACT_KEYS:
            return self.choose(self.selected)
        return None

    def handle_hover(self, pos, screen):
        """Select the button under the mouse."""
        panel = self.get_panel(screen)
        for index in range(len(self.get_options())):
            if self.get_button_rect(panel, index).collidepoint(pos):
                self.selected = index

    def handle_click(self, pos, screen):
        """A click on a button uses it; a click outside the window resumes."""
        panel = self.get_panel(screen)
        if not panel.collidepoint(pos):
            return "resume"
        for index in range(len(self.get_options())):
            if self.get_button_rect(panel, index).collidepoint(pos):
                self.selected = index
                return self.choose(index)
        return None

    def draw(self, screen, font, small_font):
        """Darken the game and draw the window."""
        if not self.is_open:
            return

        if self.dim is None or self.dim.get_size() != screen.get_size():
            self.dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            self.dim.fill((20, 12, 8, 120))
        screen.blit(self.dim, (0, 0))

        panel = self.get_panel(screen)
        theme.draw_panel(screen, panel)
        title = "Back to the title?" if self.confirming else "Paused"
        theme.draw_text(screen, font, title, config.TEXT, (panel.centerx, panel.y + 40), "center")

        if self.confirming:
            theme.draw_text(screen, small_font, "Unsaved progress will be lost.", config.TEXT_DIM,
                            (panel.centerx, panel.y + 84), "center")

        for index, label in enumerate(self.get_options()):
            theme.draw_button(screen, font, self.get_button_rect(panel, index), label, index == self.selected)

        if self.message != "" and not self.confirming:
            theme.draw_text(screen, small_font, self.message, self.message_color,
                            (panel.centerx, panel.bottom - 34), "center")