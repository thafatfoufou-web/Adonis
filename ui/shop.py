"""The shop window (buying seeds) and the shipping box (selling crops)."""

import pygame
import config
from core.assets import load_image
from systems.items import ITEMS, get_buy_price, get_sell_price
from ui import theme


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
        panel = pygame.Rect(0, 0, *config.SHOP_PANEL_SIZE)
        panel.center = screen.get_rect().center
        return panel

    def get_row_rect(self, panel, index):
        """Return the rectangle of one item row, used for drawing and for clicks."""
        row_x = panel.x + 20
        row_y = panel.y + 70 + index * config.SHOP_ROW_SPACING
        row_width = panel.width - 40
        return pygame.Rect(row_x, row_y, row_width, config.SHOP_ROW_HEIGHT)

    def get_close_rect(self, panel):
        """Return the rectangle of the X button at the top right of the window."""
        return pygame.Rect(panel.right - 44, panel.y + 16, 28, 28)

    def handle_key(self, key, inventory):
        """Esc closes, up/down move the cursor, the interact keys buy."""
        if key == pygame.K_ESCAPE:
            self.close()
        elif key in config.UP_KEYS:
            self.cursor = (self.cursor - 1) % len(config.SHOP_STOCK)
        elif key in config.DOWN_KEYS:
            self.cursor = (self.cursor + 1) % len(config.SHOP_STOCK)
        elif key in config.INTERACT_KEYS:
            self.buy(config.SHOP_STOCK[self.cursor], inventory)

    def handle_hover(self, pos, screen):
        """Move the cursor to the item row under the mouse."""
        panel = self.get_panel(screen)
        for index in range(len(config.SHOP_STOCK)):
            if self.get_row_rect(panel, index).collidepoint(pos):
                self.cursor = index

    def handle_click(self, pos, screen, inventory):
        """A click on an item row buys it; a click on the X or outside the window closes the shop."""
        panel = self.get_panel(screen)
        if self.get_close_rect(panel).collidepoint(pos) or not panel.collidepoint(pos):
            self.close()
            return
        for index in range(len(config.SHOP_STOCK)):
            row = self.get_row_rect(panel, index)
            if row.collidepoint(pos):
                self.cursor = index
                self.buy(config.SHOP_STOCK[index], inventory)

    def buy(self, item_id, inventory):
        """Buy one item if the player has enough gold and room, and set the result message."""
        price = get_buy_price(item_id)
        if inventory.gold < price:
            self.message = "Not enough gold"
        elif not inventory.add_item(item_id):
            self.message = "Inventory full"
        else:
            inventory.gold -= price
            self.message = "Bought " + ITEMS[item_id]["name"]

    def draw(self, screen, font, small_font, inventory):
        """Draw the window: title, gold, item rows, X button and the last message."""
        panel = self.get_panel(screen)
        theme.draw_frame(screen, panel)

        theme.draw_text(screen, font, "Shop", config.TEXT, (panel.x + 26, panel.y + 20))

        close = self.get_close_rect(panel)
        theme.draw_button(screen, small_font, close, "X", False)

        gold_text = "Gold: " + str(inventory.gold)
        theme.draw_text(screen, font, gold_text, config.ACCENT, (close.left - 16, panel.y + 20), "topright")

        for i, item_id in enumerate(config.SHOP_STOCK):
            data = ITEMS[item_id]
            row = self.get_row_rect(panel, i)
            selected = i == self.cursor
            theme.draw_button_base(screen, row, selected)

            icon_size = (config.ICON_SIZE, config.ICON_SIZE)
            icon = load_image(data["icon"], icon_size, data["color"])
            screen.blit(icon, (row.x + 8, row.y + (config.SHOP_ROW_HEIGHT - config.ICON_SIZE) // 2 - 1))

            name_color, shadow = theme.get_label_color(selected)
            theme.draw_text(screen, font, data["name"], name_color, (row.x + 52, row.centery - 1), "midleft", shadow)
            price_text = str(get_buy_price(item_id)) + " g"
            price_color = name_color if theme.get_skin() == "grave" else config.ACCENT
            theme.draw_text(screen, font, price_text, price_color, (row.right - 14, row.centery - 1), "midright", shadow)

        if self.message:
            color = config.GOOD if self.message.startswith("Bought") else config.BAD
            theme.draw_text(screen, small_font, self.message, color, (panel.x + 26, panel.bottom - 40))


def sell_selected(inventory):
    """Sell one item of the selected slot and return the message to display."""
    slot = inventory.get_selected()
    if slot is None:
        return "Nothing to sell"
    price = get_sell_price(slot["id"])
    if price is None:
        return "Can't sell this"
    inventory.gold += price
    inventory.remove_one_selected()
    return "Sold for " + str(price) + " gold"