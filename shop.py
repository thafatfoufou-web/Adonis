import pygame
from assets import load_image
from inventory import ITEMS
import theme
from controls import INTERACT_KEYS, UP_KEYS, DOWN_KEYS

SHOP_STOCK = ["cauliflower_seeds", "carrot_seeds", "pumpkin_seeds"]

PANEL_WIDTH = 480
PANEL_HEIGHT = 270
ROW_HEIGHT = 40
ROW_SPACING = 46
ICON_SIZE = 32   # icons are drawn at their real size (32x32), so the pixels stay sharp


class Shop:
    """The shop window: a list of items the player can buy with gold."""

    def __init__(self):
        """Create a closed shop."""
        self.is_open = False
        self.cursor = 0
        self.message = ""

    def open(self):
        """Open the shop with the cursor on the first item."""
        self.is_open = True
        self.cursor = 0
        self.message = ""

    def close(self):
        """Close the shop."""
        self.is_open = False

    def get_panel(self, screen):
        """Return the rectangle of the shop window, centered on the screen."""
        panel = pygame.Rect(0, 0, PANEL_WIDTH, PANEL_HEIGHT)
        panel.center = screen.get_rect().center
        return panel

    def get_row_rect(self, panel, index):
        """Return the rectangle of one item row, used for drawing and for clicks."""
        row_x = panel.x + 20
        row_y = panel.y + 70 + index * ROW_SPACING
        row_width = panel.width - 40
        return pygame.Rect(row_x, row_y, row_width, ROW_HEIGHT)

    def get_close_rect(self, panel):
        """Return the rectangle of the X button, at the top right of the window."""
        return pygame.Rect(panel.right - 44, panel.y + 16, 28, 28)

    def handle_key(self, key, inventory):
        """React to a key: Esc closes, up / down keys move, E / Space / Enter buy."""
        if key == pygame.K_ESCAPE:
            self.close()
        elif key in UP_KEYS:
            self.cursor = (self.cursor - 1) % len(SHOP_STOCK)
        elif key in DOWN_KEYS:
            self.cursor = (self.cursor + 1) % len(SHOP_STOCK)
        elif key in INTERACT_KEYS:
            self.buy(SHOP_STOCK[self.cursor], inventory)

    def handle_hover(self, pos, screen):
        """Move the cursor to the item row under the mouse."""
        panel = self.get_panel(screen)
        for index in range(len(SHOP_STOCK)):
            if self.get_row_rect(panel, index).collidepoint(pos):
                self.cursor = index

    def handle_click(self, pos, screen, inventory):
        """React to a left click: an item row buys it, the X or outside closes."""
        panel = self.get_panel(screen)
        if self.get_close_rect(panel).collidepoint(pos) or not panel.collidepoint(pos):
            self.close()
            return
        for index in range(len(SHOP_STOCK)):
            row = self.get_row_rect(panel, index)
            if row.collidepoint(pos):
                self.cursor = index
                self.buy(SHOP_STOCK[index], inventory)

    def buy(self, item_id, inventory):
        """Buy one item if the player has enough gold and room in the inventory."""
        price = ITEMS[item_id]["buy_price"]
        if inventory.gold < price:
            self.message = "Not enough gold"
        elif not inventory.add_item(item_id):
            self.message = "Inventory full"
        else:
            inventory.gold -= price
            self.message = "Bought " + ITEMS[item_id]["name"]

    def draw(self, screen, font, small_font, inventory):
        """Draw the shop window: title, gold, item rows, message and controls hint."""
        panel = self.get_panel(screen)
        theme.draw_frame(screen, panel)
        theme.draw_inset(screen, panel.inflate(-16, -16))

        theme.draw_text(screen, font, "Shop", theme.TEXT, (panel.x + 24, panel.y + 22))

        # the X button, to close the shop with the mouse
        close = self.get_close_rect(panel)
        theme.draw_inset(screen, close, theme.DANGER)
        theme.draw_text(screen, font, "X", theme.TEXT, close.center, "center")

        gold_text = "Gold: " + str(inventory.gold)
        theme.draw_text(screen, font, gold_text, theme.ACCENT, (close.left - 16, panel.y + 22), "topright")

        for i, item_id in enumerate(SHOP_STOCK):
            data = ITEMS[item_id]
            row = self.get_row_rect(panel, i)
            if i == self.cursor:
                theme.draw_inset(screen, row, theme.INSET_LIGHT)
                pygame.draw.rect(screen, theme.ACCENT, row, 2)

            icon = load_image(data["icon"], (ICON_SIZE, ICON_SIZE), data["color"])
            screen.blit(icon, (row.x + 8, row.y + (ROW_HEIGHT - ICON_SIZE) // 2))

            theme.draw_text(screen, font, data["name"], theme.TEXT, (row.x + 52, row.centery), "midleft")
            price_text = str(data["buy_price"]) + " g"
            theme.draw_text(screen, font, price_text, theme.ACCENT, (row.right - 14, row.centery), "midright")

        if self.message:
            color = theme.GOOD if self.message.startswith("Bought") else theme.BAD
            theme.draw_text(screen, small_font, self.message, color, (panel.x + 24, panel.bottom - 44))



def sell_selected(inventory):
    """Sell one item of the selected slot and return a message to display."""
    slot = inventory.get_selected()
    if slot is None:
        return "Nothing to sell"
    price = ITEMS[slot["id"]].get("sell_price")
    if price is None:
        return "Can't sell this"
    inventory.gold += price
    inventory.remove_one_selected()
    return "Sold for " + str(price) + " gold"