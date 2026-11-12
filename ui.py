import pygame
import theme
from assets import load_image
from inventory import ITEMS, SLOT_COUNT

# sizes in pixels
SCREEN_MARGIN = 16
PANEL_BORDER = 8
# SLOT_SIZE = 52
# SLOT_GAP = 4
ICON_SIZE = 32   # the icons are drawn at their real size (32x32), so the pixels stay sharp

SLOT_SIZE = 44
SLOT_GAP = 3
HOTBAR_BORDER = 6     # the wooden edge around the slots
HOTBAR_MARGIN = 2    # the gap between the bar and the bottom of the screen


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

    def draw_held_item(self, screen, inventory):
        """Draw the short message (for example 'Sold for 40 gold') at the top left."""
        if self.notice_timer > 0:
            theme.draw_text(screen, self.font, self.notice, theme.GOOD, (SCREEN_MARGIN, SCREEN_MARGIN))

    def draw_clock(self, screen, game_time):
        """Draw the day and time panel at the top right. Returns its rectangle."""
        clock_rect = pygame.Rect(0, 0, 210, 64)
        clock_rect.topright = (screen.get_width() - SCREEN_MARGIN, SCREEN_MARGIN)

        inner = theme.draw_panel(screen, clock_rect, PANEL_BORDER)
        theme.draw_text(screen, self.font, game_time.get_text(), theme.TEXT, inner.center, "center")
        return clock_rect

    def draw_gold(self, screen, inventory, clock_rect):
        """Draw the gold amount and a coin icon, just under the clock."""
        # the coin box is on the right, under the clock
        icon_rect = pygame.Rect(0, 0, 48, 40)
        icon_rect.topright = (clock_rect.right, clock_rect.bottom + 8)
        icon_inner = theme.draw_panel(screen, icon_rect, 6)
        center = icon_inner.center
        pygame.draw.circle(screen, theme.OUTLINE, center, 10)
        pygame.draw.circle(screen, theme.ACCENT_DARK, center, 9)
        pygame.draw.circle(screen, theme.ACCENT, center, 7)
        pygame.draw.rect(screen, (255, 238, 170), (center[0] - 4, center[1] - 4, 2, 2))

        # the gold amount is on the left of the coin
        gold_rect = pygame.Rect(0, 0, 100, 40)
        gold_rect.topright = (icon_rect.left - 8, icon_rect.top)
        gold_inner = theme.draw_panel(screen, gold_rect, 6)
        theme.draw_text(screen, self.font, str(inventory.gold), theme.ACCENT, gold_inner.center, "center")

    def draw_slot(self, screen, slot_rect, index, inventory):
        """Draw one hotbar slot: sunken square, key number, item, count and selection."""
        selected = index == inventory.selected
        theme.draw_inset(screen, slot_rect, theme.INSET_LIGHT if selected else theme.INSET)

        # the key number (1 to 9, then 0) is small, at the top left
        key_number = (index + 1) % 10
        number_pos = (slot_rect.x + 4, slot_rect.y + 3)
        theme.draw_text(screen, self.small_font, str(key_number), theme.TEXT_DIM, number_pos)

        slot = inventory.slots[index]
        if slot is not None:
            data = ITEMS[slot["id"]]
            icon = load_image(data["icon"], (ICON_SIZE, ICON_SIZE), data["color"])
            screen.blit(icon, icon.get_rect(center=slot_rect.center))

            if slot["count"] > 1:
                count_pos = (slot_rect.right - 4, slot_rect.bottom - 3)
                theme.draw_text(screen, self.small_font, str(slot["count"]), theme.TEXT, count_pos, "bottomright")

        # the selected slot has a gold outline
        if selected:
            pygame.draw.rect(screen, theme.ACCENT, slot_rect, 3)

    def draw_hotbar(self, screen, inventory):
        """Draw the wooden bar with the 10 slots, centered at the bottom of the screen."""
        slots_width = SLOT_COUNT * SLOT_SIZE + (SLOT_COUNT - 1) * SLOT_GAP
        panel_width = slots_width + 2 * HOTBAR_BORDER
        panel_height = SLOT_SIZE + 2 * HOTBAR_BORDER

        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel_x = screen.get_width() // 2
        panel_y = screen.get_height() - HOTBAR_MARGIN
        panel.midbottom = (panel_x, panel_y)
        theme.draw_frame(screen, panel)

        for index in range(SLOT_COUNT):
            slot_x = panel.x + HOTBAR_BORDER + index * (SLOT_SIZE + SLOT_GAP)
            slot_y = panel.y + HOTBAR_BORDER
            slot_rect = pygame.Rect(slot_x, slot_y, SLOT_SIZE, SLOT_SIZE)
            self.draw_slot(screen, slot_rect, index, inventory)


    def draw(self, screen, game_time, inventory):
        """Draw the whole interface. Called once per frame, after the world."""
        self.draw_held_item(screen, inventory)
        clock_rect = self.draw_clock(screen, game_time)
        self.draw_gold(screen, inventory, clock_rect)
        self.draw_hotbar(screen, inventory)