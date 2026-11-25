"""The shop window (buying seeds) and the shipping box (selling crops)."""

import pygame
import config
from core.assets import load_image
from entities.cow import Cow
from systems.items import ITEMS, get_buy_price, get_sell_price
from ui import theme


class Shop:
    """The shop window: a list of things the player can buy with gold. The list grows with the story."""

    def __init__(self):
        """Create a closed shop."""
        self.is_open = False
        self.tab = 0
        self.tab_rects = []
        self.cursor = 0
        self.scroll = 0
        self.message = ""
        self.story = None
        self.cows = None

    def open(self, story, cows):
        """Open the shop with the cursor on the first entry. story decides what is on the shelf; cows is the herd (a cow bought here joins it)."""
        self.is_open = True
        self.tab = 0
        self.tab_rects = []
        self.cursor = 0
        self.scroll = 0
        self.message = ""
        self.story = story
        self.cows = cows

    def close(self):
        """Close the shop."""
        self.is_open = False

    def get_unlocked(self):
        """Return every entry of config.SHOP_STOCK whose story flag is set, whatever its tab."""
        if self.story is None:
            return []
        return [entry for entry in config.SHOP_STOCK
                if "requires" not in entry or self.story.has(entry["requires"])]

    def get_tabs(self):
        """Return the names of the tabs that have something to buy, in the order of config.SHOP_TABS."""
        unlocked = self.get_unlocked()
        tabs = []
        for name in config.SHOP_TABS:
            if any(entry["tab"] == name for entry in unlocked):
                tabs.append(name)
        return tabs

    def get_stock(self):
        """Return the entries of the tab that is open."""
        tabs = self.get_tabs()
        if not tabs:
            return []
        self.tab = min(self.tab, len(tabs) - 1)
        tab_name = tabs[self.tab]
        return [entry for entry in self.get_unlocked() if entry["tab"] == tab_name]

    def change_tab(self, step):
        """Open the next tab (step 1) or the previous one (step -1), starting at its first row."""
        tabs = self.get_tabs()
        if not tabs:
            return
        self.tab = (self.tab + step) % len(tabs)
        self.cursor = 0
        self.scroll = 0
        self.message = ""

    def get_panel(self, screen):
        """Return the rectangle of the shop window, centered on the screen."""
        panel = pygame.Rect(0, 0, *config.SHOP_PANEL_SIZE)
        panel.center = screen.get_rect().center
        return panel

    def get_row_rect(self, panel, slot):
        """Return the rectangle of one visible row (slot 0 is the top row), used for drawing and for clicks."""
        row_x = panel.x + 20
        row_y = panel.y + config.SHOP_ROWS_Y + slot * config.SHOP_ROW_SPACING
        row_width = panel.width - 40
        return pygame.Rect(row_x, row_y, row_width, config.SHOP_ROW_HEIGHT)

    def get_close_rect(self, panel):
        """Return the rectangle of the X button at the top right of the window."""
        return pygame.Rect(panel.right - 44, panel.y + 16, 28, 28)

    def layout_tabs(self, panel, small_font):
        """Work out the rectangle of every tab button: each is as wide as its name, and the extra room is shared."""
        tabs = self.get_tabs()
        gap = 4
        padding = 14
        available = panel.width - 40 - gap * (len(tabs) - 1)
        widths = [small_font.size(name)[0] + padding for name in tabs]
        extra = 0
        if tabs:
            extra = max(0, (available - sum(widths)) // len(tabs))
        self.tab_rects = []
        tab_x = panel.x + 20
        for width in widths:
            tab_rect = pygame.Rect(tab_x, panel.y + config.SHOP_TAB_Y, width + extra, config.SHOP_TAB_HEIGHT)
            self.tab_rects.append(tab_rect)
            tab_x += tab_rect.width + gap

    def get_visible_indexes(self, stock):
        """Return the stock indexes of the rows shown now, for example 5, 6, 7, 8, 9."""
        first = self.scroll
        last = min(self.scroll + config.SHOP_VISIBLE_ROWS, len(stock))
        return list(range(first, last))

    def keep_cursor_visible(self):
        """Scroll the list so that the row under the cursor is on screen."""
        if self.cursor < self.scroll:
            self.scroll = self.cursor
        last_visible = self.scroll + config.SHOP_VISIBLE_ROWS - 1
        if self.cursor > last_visible:
            self.scroll = self.cursor - config.SHOP_VISIBLE_ROWS + 1

    def handle_wheel(self, wheel_y):
        """Scroll the list with the mouse wheel (wheel_y is positive when the wheel goes up)."""
        stock = self.get_stock()
        biggest_scroll = max(0, len(stock) - config.SHOP_VISIBLE_ROWS)
        self.scroll = self.scroll - wheel_y
        self.scroll = max(0, min(self.scroll, biggest_scroll))
        # keep the cursor on a row that is still visible
        last_visible = self.scroll + config.SHOP_VISIBLE_ROWS - 1
        self.cursor = max(self.scroll, min(self.cursor, last_visible))

    def handle_key(self, key, inventory):
        """Esc closes, up/down move the cursor, left/right change the tab, the interact keys buy."""
        stock = self.get_stock()
        if key == pygame.K_ESCAPE:
            self.close()
        elif not stock:
            return
        elif key in config.UP_KEYS:
            self.cursor = (self.cursor - 1) % len(stock)
            self.keep_cursor_visible()
        elif key in config.DOWN_KEYS:
            self.cursor = (self.cursor + 1) % len(stock)
            self.keep_cursor_visible()
        elif key in config.LEFT_KEYS:
            self.change_tab(-1)
        elif key in config.RIGHT_KEYS:
            self.change_tab(1)
        elif key in config.INTERACT_KEYS:
            self.buy(stock[self.cursor], inventory)

    def handle_hover(self, pos, screen):
        """Move the cursor to the item row under the mouse."""
        panel = self.get_panel(screen)
        stock = self.get_stock()
        for index in self.get_visible_indexes(stock):
            slot = index - self.scroll
            if self.get_row_rect(panel, slot).collidepoint(pos):
                self.cursor = index

    def handle_click(self, pos, screen, inventory):
        """A click on a tab opens it, a click on an item row buys it; a click on the X or outside the window closes the shop."""
        panel = self.get_panel(screen)
        if self.get_close_rect(panel).collidepoint(pos) or not panel.collidepoint(pos):
            self.close()
            return
        for i, tab_rect in enumerate(self.tab_rects):
            if tab_rect.collidepoint(pos):
                if i != self.tab:
                    self.change_tab(i - self.tab)
                return
        stock = self.get_stock()
        for index in self.get_visible_indexes(stock):
            slot = index - self.scroll
            row = self.get_row_rect(panel, slot)
            if row.collidepoint(pos):
                self.cursor = index
                self.buy(stock[index], inventory)

    def get_name(self, entry):
        """Return the name shown for an entry."""
        if entry.get("kind") == "cow":
            return entry.get("name", "Cow")
        return ITEMS[entry["item"]]["name"]

    def get_price(self, entry):
        """Return the price of an entry."""
        if entry.get("kind") == "cow":
            return entry["price"]
        return get_buy_price(entry["item"])

    def is_sold_out(self, entry):
        """Return True for a cow when the pen is full."""
        return entry.get("kind") == "cow" and len(self.cows) >= len(config.COW_START_TILES)

    def buy(self, entry, inventory):
        """Buy one entry if the player has enough gold and room, and set the result message."""
        price = self.get_price(entry)
        name = self.get_name(entry)
        if self.is_sold_out(entry):
            self.message = "The pen is full"
        elif inventory.gold < price:
            self.message = "Not enough gold"
        elif entry.get("kind") == "cow":
            taken = {cow.tile for cow in self.cows}
            free = [tile for tile in config.COW_START_TILES if tile not in taken]
            self.cows.append(Cow(free[0]))
            inventory.gold -= price
            self.message = "Bought a " + name + ". It went to the pen."
        elif not inventory.add_item(entry["item"]):
            self.message = "Inventory full"
        else:
            inventory.gold -= price
            self.message = "Bought " + name

    def draw(self, screen, font, small_font, inventory):
        """Draw the window: title, gold, tabs, item rows, X button and the last message."""
        panel = self.get_panel(screen)
        theme.draw_frame(screen, panel)

        theme.draw_text(screen, font, "Shop", config.TEXT, (panel.x + 26, panel.y + 20))

        close = self.get_close_rect(panel)
        theme.draw_button(screen, small_font, close, "X", False)

        gold_text = "Gold: " + str(inventory.gold)
        theme.draw_text(screen, font, gold_text, config.ACCENT, (close.left - 16, panel.y + 20), "topright")

        tabs = self.get_tabs()
        self.layout_tabs(panel, small_font)
        for i, tab_name in enumerate(tabs):
            tab_rect = self.tab_rects[i]
            tab_selected = i == self.tab
            theme.draw_button_base(screen, tab_rect, tab_selected)
            tab_color, tab_shadow = theme.get_label_color(tab_selected)
            theme.draw_text(screen, small_font, tab_name, tab_color, (tab_rect.centerx, tab_rect.centery - 1), "center", tab_shadow)

        stock = self.get_stock()
        if not stock:
            theme.draw_text(screen, small_font, config.SHOP_EMPTY_TEXT, config.TEXT_DIM, (panel.x + 26, panel.y + config.SHOP_TAB_Y))
        for index in self.get_visible_indexes(stock):
            entry = stock[index]
            slot = index - self.scroll
            row = self.get_row_rect(panel, slot)
            selected = index == self.cursor
            theme.draw_button_base(screen, row, selected)

            icon_size = (config.ICON_SIZE, config.ICON_SIZE)
            if entry.get("kind") == "cow":
                icon = load_image(entry["icon"], icon_size, config.COW_COLOR)
            else:
                data = ITEMS[entry["item"]]
                icon = load_image(data["icon"], icon_size, data["color"])
            screen.blit(icon, (row.x + 8, row.y + (config.SHOP_ROW_HEIGHT - config.ICON_SIZE) // 2 - 1))

            name = self.get_name(entry)
            if entry.get("kind") == "cow":
                name += "  (" + str(len(self.cows)) + "/" + str(len(config.COW_START_TILES)) + ")"
            name_color, shadow = theme.get_label_color(selected)
            theme.draw_text(screen, font, name, name_color, (row.x + 52, row.centery - 1), "midleft", shadow)
            price_text = "Full" if self.is_sold_out(entry) else str(self.get_price(entry)) + " g"
            price_color = name_color if theme.get_skin() == "grave" else config.ACCENT
            theme.draw_text(screen, font, price_text, price_color, (row.right - 14, row.centery - 1), "midright", shadow)

        if len(stock) > config.SHOP_VISIBLE_ROWS:
            first = self.scroll + 1
            last = min(self.scroll + config.SHOP_VISIBLE_ROWS, len(stock))
            position_text = str(first) + "-" + str(last) + " / " + str(len(stock))
            theme.draw_text(screen, small_font, position_text, config.TEXT_DIM, (panel.right - 26, panel.bottom - 40), "topright")

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