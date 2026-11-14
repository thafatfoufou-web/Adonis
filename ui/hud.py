"""The interface drawn over the game: notice, energy bar, clock, gold and hotbar."""

import pygame
import config
from core.assets import load_image
from systems.items import ITEMS
from ui import theme


class HUD:
    """The interface drawn on top of the game."""

    def __init__(self, font, small_font):
        """Store the fonts and prepare the short on-screen message."""
        self.font = font
        self.small_font = small_font
        self.notice = ""
        self.notice_color = config.GOOD
        self.notice_timer = 0

    def show_notice(self, text, seconds=2, color=config.GOOD):
        """Show a short message (for example 'Sold for 50 gold') for a few seconds."""
        self.notice = text
        self.notice_color = color
        self.notice_timer = seconds

    def update(self, dt):
        """Count down the timer of the short message."""
        if self.notice_timer > 0:
            self.notice_timer -= dt

    def draw_notice(self, screen):
        """Draw the short message just under the energy bar while its timer runs."""
        if self.notice_timer > 0:
            y = config.SCREEN_MARGIN + config.ENERGY_BAR_HEIGHT + config.HUD_GAP
            theme.draw_text(screen, self.font, self.notice, self.notice_color,
                            (screen.get_width() // 2, y), "midtop")

    def draw_energy(self, screen, energy):
        """Draw the energy bar at the top center; it turns red when almost empty."""
        bar_rect = pygame.Rect(0, 0, config.ENERGY_BAR_WIDTH, config.ENERGY_BAR_HEIGHT)
        bar_rect.midtop = (screen.get_width() // 2, config.SCREEN_MARGIN)
        inner = theme.draw_panel(screen, bar_rect, 6)

        fraction = energy.get_fraction()
        fill = inner.inflate(-6, -6)
        fill.width = int(fill.width * fraction)
        if fill.width > 0:
            color = config.ENERGY_GREEN if fraction > config.LOW_ENERGY else config.BAD
            pygame.draw.rect(screen, color, fill)
            pygame.draw.line(screen, config.ENERGY_LIGHT, fill.topleft, (fill.right - 1, fill.top))

        text = "Energy  " + str(energy.value) + " / " + str(energy.maximum)
        theme.draw_text(screen, self.small_font, text, config.TEXT, inner.center, "center")

    def draw_clock(self, screen, game_time):
        """Draw the day and time panel at the top right and return its rectangle."""
        clock_rect = pygame.Rect(0, 0, *config.CLOCK_SIZE)
        clock_rect.topright = (screen.get_width() - config.SCREEN_MARGIN, config.SCREEN_MARGIN)

        inner = theme.draw_panel(screen, clock_rect)
        theme.draw_text(screen, self.font, game_time.get_text(), config.TEXT, inner.center, "center")
        return clock_rect

    def draw_gold(self, screen, inventory, clock_rect):
        """Draw the coin icon and the gold amount just under the clock."""
        icon_rect = pygame.Rect(0, 0, *config.COIN_BOX_SIZE)
        icon_rect.topright = (clock_rect.right, clock_rect.bottom + config.HUD_GAP)
        icon_inner = theme.draw_panel(screen, icon_rect, 6)
        center = icon_inner.center
        pygame.draw.circle(screen, config.OUTLINE, center, 10)
        pygame.draw.circle(screen, config.ACCENT_DARK, center, 9)
        pygame.draw.circle(screen, config.ACCENT, center, 7)
        pygame.draw.rect(screen, config.COIN_SHINE, (center[0] - 4, center[1] - 4, 2, 2))

        gold_rect = pygame.Rect(0, 0, *config.GOLD_BOX_SIZE)
        gold_rect.topright = (icon_rect.left - config.HUD_GAP, icon_rect.top)
        gold_inner = theme.draw_panel(screen, gold_rect, 6)
        theme.draw_text(screen, self.font, str(inventory.gold), config.ACCENT, gold_inner.center, "center")

    def draw_slot(self, screen, slot_rect, index, inventory):
        """Draw one hotbar slot: key number, item icon, count and selection outline."""
        selected = index == inventory.selected
        theme.draw_inset(screen, slot_rect, config.INSET_LIGHT if selected else config.INSET)

        key_number = (index + 1) % 10
        number_pos = (slot_rect.x + 4, slot_rect.y + 3)
        theme.draw_text(screen, self.small_font, str(key_number), config.TEXT_DIM, number_pos)

        slot = inventory.slots[index]
        if slot is not None:
            data = ITEMS[slot["id"]]
            icon_size = (config.ICON_SIZE, config.ICON_SIZE)
            icon = load_image(data["icon"], icon_size, data["color"])
            screen.blit(icon, icon.get_rect(center=slot_rect.center))

            if slot["count"] > 1:
                count_pos = (slot_rect.right - 4, slot_rect.bottom - 3)
                theme.draw_text(screen, self.small_font, str(slot["count"]), config.TEXT, count_pos, "bottomright")

        if selected:
            pygame.draw.rect(screen, config.ACCENT, slot_rect, 3)

    def draw_hotbar(self, screen, inventory):
        """Draw the wooden bar with the slots, centered at the bottom of the screen."""
        slot_size = config.HOTBAR_SLOT_SIZE
        gap = config.HOTBAR_SLOT_GAP
        border = config.HOTBAR_BORDER
        slots_width = config.SLOT_COUNT * slot_size + (config.SLOT_COUNT - 1) * gap

        panel = pygame.Rect(0, 0, slots_width + 2 * border, slot_size + 2 * border)
        panel.midbottom = (screen.get_width() // 2, screen.get_height() - config.HOTBAR_MARGIN)
        theme.draw_frame(screen, panel)

        for index in range(config.SLOT_COUNT):
            slot_x = panel.x + border + index * (slot_size + gap)
            slot_rect = pygame.Rect(slot_x, panel.y + border, slot_size, slot_size)
            self.draw_slot(screen, slot_rect, index, inventory)

    def draw(self, screen, game_time, inventory, energy):
        """Draw the whole interface; called once per frame after the world."""
        self.draw_notice(screen)
        self.draw_energy(screen, energy)
        clock_rect = self.draw_clock(screen, game_time)
        self.draw_gold(screen, inventory, clock_rect)
        self.draw_hotbar(screen, inventory)
