"""The interface drawn over the game: notice, energy bar, clock, gold and hotbar."""

import os
import pygame
import config
from core.assets import load_image
from systems.items import ITEMS
from ui import theme
from ui.hearts import draw_hearts


class HUD:
    """The interface drawn on top of the game."""

    def __init__(self, font, small_font):
        """Store the fonts and prepare the short on-screen message."""
        self.font = font
        self.small_font = small_font
        self.notice = ""
        self.notice_color = config.GOOD
        self.notice_timer = 0
        self.quest_signature = None      # what the quest tracker said last frame, to notice changes
        self.quest_flash = 0             # seconds left of the bright one-line tracker
        self.quests_unread = False       # True: the book button shows a red dot

    def show_notice(self, text, seconds=2, color=config.GOOD):
        """Show a short message (for example 'Sold for 50 gold') for a few seconds."""
        self.notice = text
        self.notice_color = color
        self.notice_timer = seconds

    def update(self, dt):
        """Count down the timer of the short message."""
        if self.notice_timer > 0:
            self.notice_timer -= dt
        if self.quest_flash > 0:
            self.quest_flash -= dt

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

    def draw_quests(self, screen, quests, hovered=False):
        """Draw the quest book button (with a red dot when something is new) and the next goal on one small line."""
        signature = (str(quests.get_log()))
        if signature != self.quest_signature:
            if self.quest_signature is not None:        # the first look is silent, so loading a save shows no dot
                self.quest_flash = config.QUEST_FLASH_SECONDS
                self.quests_unread = True
            self.quest_signature = signature

        button = pygame.Rect(*config.QUEST_BUTTON_RECT)
        theme.draw_piece(screen, button, "button_down" if hovered else "button")
        icon = load_image(config.QUEST_BOOK_ICON, (32, 32), config.ACCENT)
        screen.blit(icon, icon.get_rect(center=(button.centerx, button.centery - 1)))
        if self.quests_unread:
            pygame.draw.circle(screen, config.TEXT_LIGHT, (button.right - 6, button.top + 8), 9)
            pygame.draw.circle(screen, config.BAD, (button.right - 6, button.top + 8), 6)

        goal = quests.get_next_goal()
        if goal is None:
            return
        bright = self.quest_flash > 0
        width = self.small_font.size(goal)[0] + 24
        plate = pygame.Rect(button.right + 8, 0, width, self.small_font.get_height() + 12)
        plate.centery = button.centery
        surface = pygame.Surface(plate.size, pygame.SRCALPHA)
        surface.fill((253, 236, 203, 255 if bright else 190))
        pygame.draw.rect(surface, config.ACCENT, surface.get_rect(), 2)
        screen.blit(surface, plate)
        color = config.TEXT if bright else config.TEXT_DIM
        theme.draw_text(screen, self.small_font, goal, color, (plate.x + 12, plate.centery - 1), "midleft")

    def draw(self, screen, game_time, inventory, energy, quests=None):
        """Draw the whole interface; called once per frame after the world."""
        self.draw_notice(screen)
        self.draw_energy(screen, energy)
        clock_rect = self.draw_clock(screen, game_time)
        self.draw_gold(screen, inventory, clock_rect)
        self.draw_hotbar(screen, inventory)
        if quests is not None:
            self.draw_quests(screen, quests, pygame.Rect(*config.QUEST_BUTTON_RECT).collidepoint(pygame.mouse.get_pos()))


class DaySummary:
    """The screen shown after each night: what you did today, then a click to start the next morning."""

    WIDTH = 620
    ROW_HEIGHT = 30

    def __init__(self):
        """Start closed."""
        self.is_open = False
        self.title = ""
        self.rows = []         # (label, value) pairs
        self.note = ""         # a short sentence under the rows
        self.footer = ""       # save result, shown at the bottom
        self.footer_color = config.GOOD

    def open(self, title, rows, note="", footer="", footer_color=config.GOOD):
        """Show the summary."""
        self.is_open = True
        self.title, self.rows, self.note = title, rows, note
        self.footer, self.footer_color = footer, footer_color

    def close(self):
        """Hide the summary and let the new day start."""
        self.is_open = False

    def handle_key(self, key):
        """Any interact key (or Esc) closes it."""
        if key in config.INTERACT_KEYS or key == pygame.K_ESCAPE:
            self.close()

    def handle_click(self):
        """A left click closes it."""
        self.close()

    def draw(self, screen, font, small_font):
        """Dim the game and draw the summary panel in the middle."""
        if not self.is_open:
            return
        dim = pygame.Surface(screen.get_size())
        dim.set_alpha(150)
        screen.blit(dim, (0, 0))

        height = 150 + self.ROW_HEIGHT * len(self.rows) + (34 if self.note else 0) + (26 if self.footer else 0)
        panel = pygame.Rect(0, 0, self.WIDTH, min(height, screen.get_height() - 40))
        panel.center = (screen.get_width() // 2, screen.get_height() // 2)
        inner = theme.draw_panel(screen, panel)

        theme.draw_text(screen, font, self.title, config.ACCENT, (inner.centerx, inner.y + 30), "center")
        y = inner.y + 70
        for label, value in self.rows:
            theme.draw_text(screen, font, label, config.TEXT, (inner.x + 28, y))
            theme.draw_text(screen, font, str(value), config.ACCENT, (inner.right - 28, y), "topright")
            y += self.ROW_HEIGHT
        if self.note:
            theme.draw_text(screen, small_font, self.note, config.TEXT_DIM, (inner.centerx, y + 8), "center")
        if self.footer:
            theme.draw_text(screen, small_font, self.footer, self.footer_color, (inner.centerx, inner.bottom - 54), "center")

        bob = (pygame.time.get_ticks() // 400) % 2 * 3
        theme.draw_text(screen, small_font, "Press E or click to start the next day", config.TEXT_DIM,
                        (inner.centerx, inner.bottom - 24 + bob), "center")


def wrap_text(font, text, width):
    """Split text into lines that fit in width pixels."""
    lines, line = [], ""
    for word in text.split(" "):
        trial = (line + " " + word).strip()
        if line and font.size(trial)[0] > width:
            lines.append(line)
            line = word
        else:
            line = trial
    lines.append(line)
    return lines


class QuestLog:
    """The quest book, with two pages: the active quests (finished goals greyed out) and the Villagers
    (hearts of each villager you have met). Pauses the game while open."""

    WIDTH = 540
    PAGES = ("Quests", "Villagers")
    ROW = 36

    def __init__(self):
        """Start closed, on the first page."""
        self.is_open = False
        self.page = 0
        self.tab_rects = []

    def open(self):
        """Show the book on the Quests page."""
        self.is_open = True
        self.page = 0

    def close(self):
        """Hide the book."""
        self.is_open = False

    def handle_key(self, key):
        """The quest key or Esc closes it; left and right turn the page."""
        if key == config.QUEST_LOG_KEY or key == pygame.K_ESCAPE:
            self.close()
        elif key in config.LEFT_KEYS:
            self.page = (self.page - 1) % len(self.PAGES)
        elif key in config.RIGHT_KEYS:
            self.page = (self.page + 1) % len(self.PAGES)

    def handle_click(self, pos):
        """A click on a page tab turns to that page; a click anywhere else closes the book."""
        for index, rect in enumerate(self.tab_rects):
            if rect.collidepoint(pos):
                self.page = index
                return
        self.close()

    def draw(self, screen, font, small_font, quests, npcs, affection, story):
        """Dim the game and draw the current page in the middle."""
        if not self.is_open:
            return
        dim = pygame.Surface(screen.get_size())
        dim.set_alpha(150)
        screen.blit(dim, (0, 0))

        if self.page == 0:
            blocks = self.get_quest_blocks(small_font, quests)
            goal_height = small_font.get_height() + 2
            height = 110 + sum(font.get_height() + 10 if kind == "title" else goal_height for kind, _, _ in blocks)
        else:
            met = [npc for npc in npcs if story.has(npc.id + "_c1")]
            height = 140 + max(len(met), 1) * self.ROW
        panel = pygame.Rect(0, 0, self.WIDTH, min(height, screen.get_height() - 40))
        panel.center = (screen.get_width() // 2, screen.get_height() // 2)
        inner = theme.draw_panel(screen, panel)

        self.tab_rects = []
        for index, label in enumerate(self.PAGES):
            rect = pygame.Rect(inner.x + 28 + index * 116, inner.y + 10, 108, 32)
            theme.draw_button(screen, small_font, rect, label, index == self.page)
            self.tab_rects.append(rect)
        theme.draw_text(screen, small_font, "Tab or Esc to close", config.TEXT_DIM, (inner.right - 28, inner.y + 18), "topright")

        if self.page == 0:
            self.draw_quests(screen, font, small_font, quests, inner, blocks)
        else:
            self.draw_villagers(screen, font, small_font, inner, met, affection)

    def get_quest_blocks(self, small_font, quests):
        """Return the rows of the Quests page as (kind, text, done), already wrapped."""
        text_width = self.WIDTH - 2 * config.PANEL_BORDER - 56
        blocks = []
        for title, goals in quests.get_log():
            blocks.append(("title", title, False))
            for text, done in goals:
                for index, line in enumerate(wrap_text(small_font, "- " + text + (" (done)" if done else ""), text_width)):
                    blocks.append(("goal", ("  " if index else "") + line, done))
        if not blocks:
            blocks.append(("goal", "No active quests right now. Talk to the villagers.", False))
        return blocks

    def draw_quests(self, screen, font, small_font, quests, inner, blocks):
        """Draw the active quests and their goals."""
        goal_height = small_font.get_height() + 2
        y = inner.y + 56
        for kind, text, done in blocks:
            if y > inner.bottom - 44:
                theme.draw_text(screen, small_font, "...", config.TEXT_DIM, (inner.x + 28, y))
                break
            if kind == "title":
                y += 6
                theme.draw_text(screen, font, text, config.ACCENT, (inner.x + 28, y))
                y += font.get_height() + 4
            else:
                theme.draw_text(screen, small_font, text, config.TEXT_DIM if done else config.TEXT, (inner.x + 28, y))
                y += goal_height
        theme.draw_text(screen, small_font, "Quests done: " + str(quests.count_done()), config.TEXT_DIM,
                        (inner.x + 28, inner.bottom - 28))

    def draw_villagers(self, screen, font, small_font, inner, met, affection):
        """Draw every villager met so far with their hearts."""
        y = inner.y + 56
        if not met:
            theme.draw_text(screen, small_font, "You have not met anyone yet.", config.TEXT_DIM, (inner.x + 28, y))
        for npc in met:
            theme.draw_text(screen, font, npc.name, config.TEXT, (inner.x + 28, y))
            if npc.id in affection.gifted_today:
                theme.draw_text(screen, small_font, "gift given today", config.TEXT_DIM, (inner.x + 190, y + 8))
            row_width = config.AFFECTION["max_hearts"] * 26
            draw_hearts(screen, (inner.right - 28 - row_width, y + 2), affection.get_hearts(npc.id), size=24, gap=2)
            y += self.ROW
        theme.draw_text(screen, small_font, "Hold an item and press G (or right click) near a villager to give a gift. One a day each.",
                        config.TEXT_DIM, (inner.x + 28, inner.bottom - 28))
