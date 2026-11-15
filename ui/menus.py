"""The start screens: the title menu and the character creation."""

import os
import pygame
import config
from core.assets import load_image, load_font
from ui import theme
from systems.save import read_save


def make_background(size):
    """Return the picture behind the menus: the file in config.MENU_BACKGROUND, or a moonlit valley."""
    if os.path.exists(config.MENU_BACKGROUND):
        picture = pygame.image.load(config.MENU_BACKGROUND).convert()
        return pygame.transform.scale(picture, size)

    width, height = size
    background = pygame.Surface(size)
    top = config.MENU_BG_TOP
    bottom = config.MENU_BG_BOTTOM
    for y in range(height):
        ratio = y / (height - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        pygame.draw.line(background, color, (0, y), (width, y))

    def scaled(points):
        """Points drawn for a 960 x 544 screen, scaled to this size."""
        return [(x * width / 960, y * height / 544) for x, y in points]

    for x, y in [(90, 50), (210, 90), (350, 40), (480, 110), (610, 60), (820, 140), (60, 160)]:
        pygame.draw.rect(background, (207, 214, 230), (x * width // 960, y * height // 544, 2, 2))
    pygame.draw.circle(background, (217, 207, 166), scaled([(705, 95)])[0], 36)

    far_ridge = [(0, 420), (80, 350), (170, 390), (290, 300), (380, 365), (500, 315), (590, 375),
                 (700, 290), (790, 360), (880, 330), (960, 365), (960, 544), (0, 544)]
    near_ridge = [(0, 470), (130, 440), (290, 480), (460, 435), (630, 478), (790, 440),
                  (960, 470), (960, 544), (0, 544)]
    pygame.draw.polygon(background, (38, 51, 79), scaled(far_ridge))
    pygame.draw.polygon(background, (23, 32, 54), scaled(near_ridge))

    mist = pygame.Surface(size, pygame.SRCALPHA)
    mist_top = int(height * 0.55)
    for y in range(mist_top, height):
        alpha = int(70 * (y - mist_top) / (height - mist_top))
        pygame.draw.line(mist, (150, 185, 190, alpha), (0, y), (width, y))
    background.blit(mist, (0, 0))
    return background


class TitleMenu:
    """The title screen: the game title with a column of buttons (also used for the yes/no question)."""

    def __init__(self, options=None, results=None, message=""):
        """Start with the first button selected. By default the buttons are Start and Quit."""
        self.options = options or ["Start", "Quit"]
        self.results = results or ["start", "quit"]
        self.message = message
        self.selected = 0

    def get_button_rect(self, index):
        """Return the rectangle of a button, used for drawing and for the mouse."""
        width, height = config.MENU_BUTTON_SIZE
        center_x = config.SCREEN_SIZE[0] // 2
        center_y = config.MENU_BUTTONS_Y + index * (height + config.MENU_BUTTON_GAP)
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (center_x, center_y)
        return rect

    def handle_event(self, event):
        """React to a key or the mouse. Return "start" or "quit" when a button is used, else None."""
        count = len(self.options)

        if event.type == pygame.KEYDOWN:
            if event.key in config.UP_KEYS:
                self.selected = (self.selected - 1) % count
            elif event.key in config.DOWN_KEYS:
                self.selected = (self.selected + 1) % count
            elif event.key in config.INTERACT_KEYS:
                return self.results[self.selected]

        elif event.type == pygame.MOUSEMOTION:
            for index in range(count):
                if self.get_button_rect(index).collidepoint(event.pos):
                    self.selected = index

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index in range(count):
                if self.get_button_rect(index).collidepoint(event.pos):
                    return self.results[index]

        return None

    def draw(self, screen, fonts):
        """Draw the buttons and a hint. The title is drawn only when there is no menu picture.

        Your own picture (config.MENU_BACKGROUND) already contains the title, so the code adds
        only the buttons. Without the picture, the title and the subtitle are written in code.
        """
        title_font, font, small_font = fonts
        center_x = config.SCREEN_SIZE[0] // 2

        if not os.path.exists(config.MENU_BACKGROUND):
            title_pos = (center_x, config.TITLE_PANEL_Y - 16)
            theme.draw_text(screen, title_font, config.WINDOW_TITLE.upper(), config.TEXT_LIGHT,
                            title_pos, anchor="center", shadow=True)
            subtitle_pos = (center_x, config.TITLE_PANEL_Y + 46)
            theme.draw_text(screen, font, config.MENU_SUBTITLE, config.TEXT_LIGHT,
                            subtitle_pos, anchor="center", shadow=True)

        for index, label in enumerate(self.options):
            theme.draw_button(screen, font, self.get_button_rect(index), label, index == self.selected)

        if self.message != "":
            message_pos = (center_x, self.get_button_rect(0).top - 26)
            theme.draw_text(screen, font, self.message, config.TEXT_LIGHT, message_pos, anchor="center", shadow=True)


class Creation:
    """The character creation screen: a name, a gender (which gives the hero's picture) and Start."""

    NAME_FOCUS = 0
    GENDER_FOCUS = 1
    BUTTON_FOCUS = 2

    def __init__(self):
        """Start with an empty name, the first gender and the cursor on the name."""
        self.name = ""
        self.genders = list(config.PLAYER_SPRITES)
        self.gender_index = 0
        self.focus = self.NAME_FOCUS
        self.message = ""

    def get_name_rect(self):
        """Return the rectangle of the name box."""
        rect = pygame.Rect(0, 0, *config.NAME_BOX_SIZE)
        rect.center = (config.SCREEN_SIZE[0] // 2, 142)
        return rect

    def get_card_rect(self, index):
        """Return the rectangle of the card of a gender (the cards are side by side)."""
        width, height = config.CARD_SIZE
        count = len(self.genders)
        total_width = count * width + (count - 1) * config.CARD_GAP
        first_x = (config.SCREEN_SIZE[0] - total_width) // 2
        card_x = first_x + index * (width + config.CARD_GAP)
        return pygame.Rect(card_x, 222, width, height)

    def get_start_rect(self):
        """Return the rectangle of the Start button."""
        rect = pygame.Rect(0, 0, *config.START_BUTTON_SIZE)
        rect.center = (config.SCREEN_SIZE[0] // 2, 474)
        return rect

    def add_text(self, text):
        """Add typed characters to the name, up to the maximum length. No leading or double spaces."""
        for character in text:
            if len(self.name) >= config.MAX_NAME_LENGTH:
                return
            if not character.isprintable():
                continue
            if character == " " and (self.name == "" or self.name.endswith(" ")):
                continue
            self.name += character
            self.message = ""

    def move_focus(self, step):
        """Move the cursor between the name, the genders and the Start button (no looping)."""
        self.focus = max(0, min(2, self.focus + step))

    def choose_gender(self, step):
        """Select the previous (-1) or next (+1) gender, looping at the ends."""
        self.gender_index = (self.gender_index + step) % len(self.genders)

    def confirm(self):
        """Try to finish. Return "done" if there is a name, otherwise ask for one and return None."""
        if self.name.strip() == "":
            self.message = "Please type a name first."
            self.focus = self.NAME_FOCUS
            return None
        return "done"

    def get_profile(self):
        """Return the player's choices: the name, the gender and the hero's picture."""
        gender = self.genders[self.gender_index]
        return {
            "name": self.name.strip(),
            "gender": gender,
            "sprite": config.PLAYER_SPRITES[gender],
        }

    def handle_name_key(self, key):
        """Keys while the cursor is on the name: letters come as text, so only the editing keys are here."""
        if key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
            self.message = ""
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_DOWN):
            self.move_focus(1)
        elif key == pygame.K_UP:
            self.move_focus(-1)
        return None

    def handle_gender_key(self, key):
        """Keys while the cursor is on the genders: left and right choose, up and down move on."""
        if key in config.LEFT_KEYS:
            self.choose_gender(-1)
        elif key in config.RIGHT_KEYS:
            self.choose_gender(1)
        elif key in config.UP_KEYS:
            self.move_focus(-1)
        elif key in config.DOWN_KEYS or key in config.INTERACT_KEYS:
            self.move_focus(1)
        return None

    def handle_button_key(self, key):
        """Keys while the cursor is on Start: the interact keys finish, up goes back."""
        if key in config.UP_KEYS:
            self.move_focus(-1)
        elif key in config.INTERACT_KEYS:
            return self.confirm()
        return None

    def handle_key(self, event):
        """Escape goes back to the title, Tab moves the cursor, the other keys depend on where it is."""
        if event.key == pygame.K_ESCAPE:
            return "back"
        if event.key == pygame.K_TAB:
            if event.mod & pygame.KMOD_SHIFT:
                self.move_focus(-1)
            else:
                self.move_focus(1)
            return None

        if self.focus == self.NAME_FOCUS:
            return self.handle_name_key(event.key)
        if self.focus == self.GENDER_FOCUS:
            return self.handle_gender_key(event.key)
        return self.handle_button_key(event.key)

    def handle_click(self, pos):
        """A click on the name box, a card or the Start button. Return "done" if Start was used."""
        if self.get_name_rect().collidepoint(pos):
            self.focus = self.NAME_FOCUS

        for index in range(len(self.genders)):
            if self.get_card_rect(index).collidepoint(pos):
                self.gender_index = index
                self.focus = self.GENDER_FOCUS

        if self.get_start_rect().collidepoint(pos):
            self.focus = self.BUTTON_FOCUS
            return self.confirm()
        return None

    def handle_event(self, event):
        """React to typing, a key or a click. Return "done" or "back" when the screen is finished, else None."""
        if event.type == pygame.TEXTINPUT:
            if self.focus == self.NAME_FOCUS:
                self.add_text(event.text)
        elif event.type == pygame.KEYDOWN:
            return self.handle_key(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.handle_click(event.pos)
        return None

    def draw_name_box(self, screen, font, small_font):
        """Draw the name label, the box with the typed name and a blinking cursor."""
        rect = self.get_name_rect()
        label_pos = (rect.centerx, rect.top - 24)
        theme.draw_text(screen, small_font, "Your name", config.TEXT_DIM, label_pos, anchor="center")

        theme.draw_inset(screen, rect)
        if self.focus == self.NAME_FOCUS:
            pygame.draw.rect(screen, config.ACCENT, rect, 2, border_radius=3)

        text_pos = (rect.x + 14, rect.centery)
        if self.name == "" and self.focus != self.NAME_FOCUS:
            theme.draw_text(screen, font, "Type your name", config.TEXT_DIM, text_pos, anchor="midleft")
            return

        text_rect = theme.draw_text(screen, font, self.name, config.TEXT, text_pos, anchor="midleft")
        blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
        if self.focus == self.NAME_FOCUS and blink_on:
            cursor_x = text_rect.right + 3
            pygame.draw.line(screen, config.ACCENT, (cursor_x, rect.centery - 12), (cursor_x, rect.centery + 10), 2)

    def draw_cards(self, screen, font):
        """Draw one card per gender with the hero's picture; the chosen one has a gold border and hops."""
        for index, gender in enumerate(self.genders):
            rect = self.get_card_rect(index)
            selected = index == self.gender_index
            if selected:
                theme.draw_inset(screen, rect)
            else:
                theme.draw_frame(screen, rect)

            picture = load_image(config.PLAYER_SPRITES[gender], config.CREATION_SPRITE_SIZE,
                                 config.PLAYER_FALLBACK_COLOR)
            hop = 0
            if selected:
                hop = (pygame.time.get_ticks() // 300) % 2 * 3
            picture_rect = picture.get_rect(midtop=(rect.centerx, rect.top + 18 - hop))
            screen.blit(picture, picture_rect)

            if selected:
                label_color = config.ACCENT
            else:
                label_color = config.TEXT_DIM
            label_pos = (rect.centerx, rect.bottom - 26)
            theme.draw_text(screen, font, config.GENDER_LABELS[gender], label_color, label_pos, anchor="center")

            if selected:
                pygame.draw.rect(screen, config.ACCENT, rect, 3, border_radius=4)
                if self.focus == self.GENDER_FOCUS:
                    pygame.draw.rect(screen, config.TEXT, rect.inflate(10, 10), 2, border_radius=6)

    def draw(self, screen, fonts):
        """Draw the window, the title, the name box, the two cards, the Start button and the hints."""
        title_font, font, small_font = fonts
        center_x = config.SCREEN_SIZE[0] // 2

        theme.draw_panel(screen, pygame.Rect(*config.CREATION_PANEL))
        theme.draw_text(screen, font, "Create your character", config.ACCENT, (center_x, 62), anchor="center")

        self.draw_name_box(screen, font, small_font)
        if self.message != "":
            theme.draw_text(screen, small_font, self.message, config.BAD, (center_x, 182), anchor="center")

        theme.draw_text(screen, small_font, "Your character", config.TEXT_DIM, (center_x, 206), anchor="center")
        self.draw_cards(screen, font)
        theme.draw_button(screen, font, self.get_start_rect(), "Start", self.focus == self.BUTTON_FOCUS)


def run_screen(screen, clock, screen_object, background, fonts):
    """Run one menu screen until it gives a result: "start", "quit", "done" or "back"."""
    while True:
        clock.tick(config.FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            result = screen_object.handle_event(event)
            if result is not None:
                return result

        screen.blit(background, (0, 0))
        screen_object.draw(screen, fonts)
        theme.draw_cursor(screen)
        pygame.display.flip()


def run_start_menus(screen, clock, font, small_font):
    """Show the title screen, then the character creation.

    Return the player's profile (name, gender and hero's picture), or None if the player quits.
    The profile has a "save" entry: the saved game to load, or None for a new game.
    Escape in the creation goes back to the title screen.
    """
    title_font = load_font(config.FONT_BOLD_FILE, config.TITLE_FONT_SIZE)
    fonts = (title_font, font, small_font)
    background = make_background(screen.get_size())

    while True:
        save = read_save()
        if save is None:
            title = TitleMenu()
        else:
            title = TitleMenu(["Continue", "New game", "Quit"], ["continue", "start", "quit"])
        choice = run_screen(screen, clock, title, background, fonts)

        if choice == "continue":
            profile = dict(save["profile"])
            default_sprite = config.PLAYER_SPRITES[list(config.PLAYER_SPRITES)[0]]
            profile["sprite"] = config.PLAYER_SPRITES.get(profile.get("gender"), default_sprite)
            profile["save"] = save
            return profile
        if choice != "start":
            return None

        if save is not None:
            question = TitleMenu(["Yes, new game", "Back"], ["yes", "back"], "Replace your saved game?")
            answer = run_screen(screen, clock, question, background, fonts)
            if answer == "quit":
                return None
            if answer != "yes":
                continue

        creation = Creation()
        pygame.key.start_text_input()
        pygame.key.set_repeat(350, 40)
        result = run_screen(screen, clock, creation, background, fonts)
        pygame.key.stop_text_input()
        pygame.key.set_repeat()

        if result == "done":
            profile = creation.get_profile()
            profile["save"] = None
            return profile
        if result == "quit":
            return None
