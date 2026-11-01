import pygame
from gametime import START_OF_DAY, END_OF_DAY

PANEL_COLOR = (30, 30, 40)
BORDER_COLOR = (255, 220, 60)
WHITE = (255, 255, 255)
GOLD = (255, 220, 60)
GREY = (180, 180, 180)

CONTROLS = [
    "Move: arrows / ZQSD",
    "E: use the tool, open, sell",
    "1-0 or mouse wheel: choose a slot",
]


class HUD:
    def __init__(self, font, small_font):
        self.font = font
        self.small_font = small_font
        self.panel = pygame.Rect(528, 8, 424, 468)
        self.notice = ""
        self.notice_timer = 0

    def show_notice(self, text, seconds=2):
        self.notice = text
        self.notice_timer = seconds

    def update(self, dt):
        if self.notice_timer > 0:
            self.notice_timer -= dt

    def text(self, screen, content, x, y, color, small=False):
        font = self.small_font if small else self.font
        screen.blit(font.render(content, True, color), (x, y))

    def draw(self, screen, game_time, inventory):
        pygame.draw.rect(screen, PANEL_COLOR, self.panel)
        pygame.draw.rect(screen, BORDER_COLOR, self.panel, 2)
        x = self.panel.x + 20
        y = self.panel.y + 20

        # day and time, then the progress bar of the day
        self.text(screen, game_time.get_text(), x, y, WHITE)
        bar = pygame.Rect(x, y + 36, self.panel.width - 40, 10)
        progress = (game_time.minutes - START_OF_DAY) / (END_OF_DAY - START_OF_DAY)
        pygame.draw.rect(screen, (70, 70, 80), bar)
        pygame.draw.rect(screen, (240, 180, 60),
                         (bar.x, bar.y, int(bar.width * progress), bar.height))

        # gold and held item
        self.text(screen, f"Gold: {inventory.gold}", x, y + 70, GOLD)
        self.text(screen, "Holding: " + inventory.get_selected_name(), x, y + 110, WHITE)

        # short message (sold, can't sell...)
        if self.notice_timer > 0:
            self.text(screen, self.notice, x, y + 160, (150, 255, 150))

        # controls reminder at the bottom of the panel
        for i, line in enumerate(CONTROLS):
            self.text(screen, line, x, self.panel.bottom - 80 + i * 22, GREY, small=True)