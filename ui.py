import pygame
from inventory import ITEMS, SLOT_COUNT

# colors taken from the mockup
MAUVE = (158, 130, 135)
PINK = (255, 200, 210)
TEXT_COLOR = (30, 25, 30)
SELECTED_COLOR = (30, 25, 30)
COIN_COLOR = (240, 190, 60)
COIN_BORDER = (190, 140, 30)
NOTICE_COLOR = (40, 110, 60)

# sizes in pixels
SCREEN_MARGIN = 16
PANEL_BORDER = 8
SLOT_SIZE = 52
SLOT_GAP = 6
NOTCH_SIZE = 20


class HUD:
    """The interface drawn on top of the game: held item, clock, gold and hotbar."""

    def __init__(self, font, small_font):
        """Store the fonts and prepare the short on-screen message."""
        self.font = font
        self.small_font = small_font
        self.notice = ""
        self.notice_timer = 0

    def show_notice(self, text, seconds=2):
        """Show a short message (for example 'Sold for 50 gold') for a few seconds."""
        self.notice = text
        self.notice_timer = seconds

    def update(self, dt):
        """Count down the timer of the short message."""
        if self.notice_timer > 0:
            self.notice_timer -= dt

    def draw_panel(self, screen, rect):
        """Draw a mauve panel with a pink inside, and return the pink inside rectangle."""
        pygame.draw.rect(screen, MAUVE, rect)
        inner = rect.inflate(-2 * PANEL_BORDER, -2 * PANEL_BORDER)
        pygame.draw.rect(screen, PINK, inner)
        return inner

    def draw_centered_text(self, screen, content, rect, font):
        """Draw a text in the middle of a rectangle."""
        label = font.render(content, True, TEXT_COLOR)
        label_rect = label.get_rect()
        label_rect.center = rect.center
        screen.blit(label, label_rect)

    def draw_held_item(self, screen, inventory):
        """Draw the name of the held item at the top left, with the short message under it."""
        held_text = "Currently holding: " + inventory.get_selected_name()
        label = self.font.render(held_text, True, TEXT_COLOR)
        screen.blit(label, (SCREEN_MARGIN, SCREEN_MARGIN))

        if self.notice_timer > 0:
            notice = self.font.render(self.notice, True, NOTICE_COLOR)
            notice_y = SCREEN_MARGIN + 36
            screen.blit(notice, (SCREEN_MARGIN, notice_y))

    def draw_clock(self, screen, game_time):
        """Draw the day and time panel at the top right. Returns its rectangle."""
        clock_rect = pygame.Rect(0, 0, 210, 64)
        clock_rect.topright = (screen.get_width() - SCREEN_MARGIN, SCREEN_MARGIN)

        inner = self.draw_panel(screen, clock_rect)
        self.draw_centered_text(screen, game_time.get_text(), inner, self.font)
        return clock_rect

    def draw_gold(self, screen, inventory, clock_rect):
        """Draw the gold amount and a coin icon, just under the clock."""
        # the icon box is on the right, under the clock
        icon_rect = pygame.Rect(0, 0, 48, 40)
        icon_rect.topright = (clock_rect.right, clock_rect.bottom + 8)
        icon_inner = self.draw_panel(screen, icon_rect)
        pygame.draw.circle(screen, COIN_BORDER, icon_inner.center, 10)
        pygame.draw.circle(screen, COIN_COLOR, icon_inner.center, 7)

        # the gold amount is on the left of the icon
        gold_rect = pygame.Rect(0, 0, 100, 40)
        gold_rect.topright = (icon_rect.left - 8, icon_rect.top)
        gold_inner = self.draw_panel(screen, gold_rect)
        self.draw_centered_text(screen, str(inventory.gold), gold_inner, self.font)

    def draw_slot(self, screen, slot_rect, index, inventory):
        """Draw one hotbar slot: pink square, number notch, item, count and selection."""
        pygame.draw.rect(screen, PINK, slot_rect)

        # the notch at the top left holds the key number (1 to 9, then 0)
        notch_rect = pygame.Rect(slot_rect.x, slot_rect.y, NOTCH_SIZE, NOTCH_SIZE)
        pygame.draw.rect(screen, MAUVE, notch_rect)
        key_number = (index + 1) % 10
        number = self.small_font.render(str(key_number), True, TEXT_COLOR)
        number_rect = number.get_rect()
        number_rect.center = notch_rect.center
        screen.blit(number, number_rect)

        # the item is a colored square for now, until you draw the real icons
        slot = inventory.slots[index]
        if slot is not None:
            data = ITEMS[slot["id"]]
            item_rect = pygame.Rect(0, 0, 24, 24)
            item_rect.center = (slot_rect.centerx + 6, slot_rect.centery + 6)
            pygame.draw.rect(screen, data["color"], item_rect)

            if slot["count"] > 1:
                count = self.small_font.render(str(slot["count"]), True, TEXT_COLOR)
                count_x = slot_rect.right - count.get_width() - 4
                count_y = slot_rect.bottom - count.get_height() - 2
                screen.blit(count, (count_x, count_y))

        # the selected slot has a dark outline
        if index == inventory.selected:
            pygame.draw.rect(screen, SELECTED_COLOR, slot_rect, 3)

    def draw_hotbar(self, screen, inventory):
        """Draw the panel with the 10 slots, centered at the bottom of the screen."""
        slots_width = SLOT_COUNT * SLOT_SIZE + (SLOT_COUNT - 1) * SLOT_GAP
        panel_width = slots_width + 2 * PANEL_BORDER
        panel_height = SLOT_SIZE + 2 * PANEL_BORDER

        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel_x = screen.get_width() // 2
        panel_y = screen.get_height() - SCREEN_MARGIN
        panel.midbottom = (panel_x, panel_y)
        pygame.draw.rect(screen, MAUVE, panel)

        for index in range(SLOT_COUNT):
            slot_x = panel.x + PANEL_BORDER + index * (SLOT_SIZE + SLOT_GAP)
            slot_y = panel.y + PANEL_BORDER
            slot_rect = pygame.Rect(slot_x, slot_y, SLOT_SIZE, SLOT_SIZE)
            self.draw_slot(screen, slot_rect, index, inventory)

    def draw(self, screen, game_time, inventory):
        """Draw the whole interface. Called once per frame, after the world."""
        self.draw_held_item(screen, inventory)
        clock_rect = self.draw_clock(screen, game_time)
        self.draw_gold(screen, inventory, clock_rect)
        self.draw_hotbar(screen, inventory)