"""The interface drawn over the game: notice, energy bar, clock, gold and hotbar."""

import os
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
        """Draw the short message on a small cream plate just under the energy bar while its timer runs."""
        if self.notice_timer > 0:
            y = config.SCREEN_MARGIN + config.ENERGY_BAR_HEIGHT + config.HUD_GAP
            width = self.font.size(self.notice)[0] + 32
            plate = pygame.Rect(0, 0, width, self.font.get_height() + 14)
            plate.midtop = (screen.get_width() // 2, y)
            theme.draw_frame(screen, plate)
            theme.draw_text(screen, self.font, self.notice, self.notice_color, (plate.centerx, plate.centery - 1), "center")

    def draw_energy(self, screen, energy):
        """Draw the energy bar at the top center; it turns red when almost empty."""
        frame = pygame.Rect(0, 0, config.ENERGY_BAR_WIDTH, config.ENERGY_BAR_HEIGHT)
        frame.midtop = (screen.get_width() // 2, config.SCREEN_MARGIN)
        theme.draw_frame(screen, frame)

        trough = frame.inflate(-16, -16)
        fraction = energy.get_fraction()
        theme.draw_bar(screen, trough, fraction, fraction <= config.LOW_ENERGY)

        text = "Energy  " + str(energy.value) + " / " + str(energy.maximum)
        theme.draw_text(screen, self.small_font, text, config.TEXT_LIGHT, (trough.centerx, trough.centery - 1), "center", True)

    def draw_clock(self, screen, game_time):
        """Draw the day and time panel at the top right and return its rectangle."""
        clock_rect = pygame.Rect(0, 0, *config.CLOCK_SIZE)
        clock_rect.topright = (screen.get_width() - config.SCREEN_MARGIN, config.SCREEN_MARGIN)

        inner = theme.draw_panel(screen, clock_rect)
        theme.draw_text(screen, self.font, game_time.get_text(), config.TEXT, (inner.centerx, inner.centery - 1), "center")
        return clock_rect

    def draw_coin(self, screen, center):
        """Draw the coin icon (assets/ui/Coin.png if it exists, otherwise a small round coin)."""
        if os.path.exists("assets/ui/Coin.png"):
            picture = load_image("assets/ui/Coin.png", (24, 24), config.COIN_FILL)
            screen.blit(picture, picture.get_rect(center=center))
            return
        pygame.draw.circle(screen, config.COIN_OUTLINE, center, 10)
        pygame.draw.circle(screen, config.COIN_DARK, center, 9)
        pygame.draw.circle(screen, config.COIN_FILL, center, 7)
        pygame.draw.rect(screen, config.COIN_SHINE, (center[0] - 4, center[1] - 4, 2, 2))

    def draw_gold(self, screen, inventory, clock_rect):
        """Draw the coin icon and the gold amount just under the clock."""
        icon_rect = pygame.Rect(0, 0, *config.COIN_BOX_SIZE)
        icon_rect.topright = (clock_rect.right, clock_rect.bottom + config.HUD_GAP)
        icon_inner = theme.draw_panel(screen, icon_rect, 6)
        self.draw_coin(screen, icon_inner.center)

        gold_rect = pygame.Rect(0, 0, *config.GOLD_BOX_SIZE)
        gold_rect.topright = (icon_rect.left - config.HUD_GAP, icon_rect.top)
        gold_inner = theme.draw_panel(screen, gold_rect, 6)
        theme.draw_text(screen, self.font, str(inventory.gold), config.ACCENT,
                        (gold_inner.centerx, gold_inner.centery - 1), "center")

    def draw_slot(self, screen, slot_rect, index, inventory):
        """Draw one hotbar slot: key number, item icon, count and selection outline."""
        selected = index == inventory.selected
        theme.draw_slot(screen, slot_rect, selected)

        key_number = (index + 1) % 10
        slot = inventory.slots[index]
        if slot is None:
            # the key number is shown only on empty slots, so it never covers an icon
            theme.draw_text(screen, self.small_font, str(key_number), config.TEXT_DIM, slot_rect.center, "center")
        else:
            data = ITEMS[slot["id"]]
            icon_size = (config.ICON_SIZE, config.ICON_SIZE)
            icon = load_image(data["icon"], icon_size, data["color"])
            screen.blit(icon, icon.get_rect(center=slot_rect.center))

            if slot["count"] > 1:
                count_pos = (slot_rect.right - 4, slot_rect.bottom - 3)
                theme.draw_text(screen, self.small_font, str(slot["count"]), config.TEXT_LIGHT,
                                count_pos, "bottomright", shadow=True)

    def draw_hotbar(self, screen, inventory):
        """Draw the cream bar with the slots, centered at the bottom of the screen."""
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

    def draw_quests(self, screen, quests):
        """Draw the active quests and their goals in a small panel under the menu button."""
        tracker = quests.get_tracker()
        if len(tracker) == 0:
            return
        line_height = self.small_font.get_height() + 2
        rows = sum(1 + len(lines) for _, lines in tracker)
        width = 340
        height = rows * line_height + 24 + (len(tracker) - 1) * 8
        top = config.SCREEN_MARGIN + config.MENU_BUTTON_RECT[3] + config.HUD_GAP
        panel = pygame.Rect(config.SCREEN_MARGIN, top, width, height)
        inner = theme.draw_panel(screen, panel, 8)

        y = inner.y + 4
        for title, lines in tracker:
            theme.draw_text(screen, self.small_font, title, config.ACCENT, (inner.x + 6, y))
            y += line_height
            for text in lines:
                color = config.TEXT_DIM if text.endswith("(done)") else config.TEXT
                theme.draw_text(screen, self.small_font, "- " + text, color, (inner.x + 6, y))
                y += line_height
            y += 8

    def draw(self, screen, game_time, inventory, energy, quests=None):
        """Draw the whole interface; called once per frame after the world."""
        self.draw_notice(screen)
        self.draw_energy(screen, energy)
        clock_rect = self.draw_clock(screen, game_time)
        self.draw_gold(screen, inventory, clock_rect)
        self.draw_hotbar(screen, inventory)
        if quests is not None:
            self.draw_quests(screen, quests)