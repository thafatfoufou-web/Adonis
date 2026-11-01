import pygame
from inventory import ITEMS

SHOP_STOCK = ["turnip_seeds"]  # add item ids here to sell more things


class Shop:
    def __init__(self):
        self.is_open = False
        self.cursor = 0
        self.message = ""

    def open(self):
        self.is_open = True
        self.cursor = 0
        self.message = ""

    def close(self):
        self.is_open = False

    def handle_key(self, key, inventory):
        if key == pygame.K_ESCAPE:
            self.close()
        elif key == pygame.K_UP:
            self.cursor = (self.cursor - 1) % len(SHOP_STOCK)
        elif key == pygame.K_DOWN:
            self.cursor = (self.cursor + 1) % len(SHOP_STOCK)
        elif key == pygame.K_RETURN:
            self.buy(SHOP_STOCK[self.cursor], inventory)

    def buy(self, item_id, inventory):
        price = ITEMS[item_id]["buy_price"]
        if inventory.gold < price:
            self.message = "Not enough gold"
        elif not inventory.add_item(item_id):
            self.message = "Inventory full"
        else:
            inventory.gold -= price
            self.message = "Bought " + ITEMS[item_id]["name"]

    def draw(self, screen, font, small_font, inventory):
        panel = pygame.Rect(0, 0, 420, 260)
        panel.center = screen.get_rect().center
        pygame.draw.rect(screen, (30, 30, 40), panel)
        pygame.draw.rect(screen, (255, 220, 60), panel, 3)

        title = font.render("Shop", True, (255, 255, 255))
        screen.blit(title, (panel.x + 20, panel.y + 15))
        gold = font.render(f"Gold: {inventory.gold}", True, (255, 220, 60))
        screen.blit(gold, (panel.right - gold.get_width() - 20, panel.y + 15))

        for i, item_id in enumerate(SHOP_STOCK):
            data = ITEMS[item_id]
            row = pygame.Rect(panel.x + 20, panel.y + 70 + i * 40, panel.width - 40, 34)
            if i == self.cursor:
                pygame.draw.rect(screen, (70, 70, 90), row)
            pygame.draw.rect(screen, data["color"], (row.x + 6, row.y + 6, 22, 22))
            name = font.render(data["name"], True, (255, 255, 255))
            screen.blit(name, (row.x + 40, row.y + 6))
            price = font.render(f"{data['buy_price']} g", True, (255, 220, 60))
            screen.blit(price, (row.right - price.get_width() - 10, row.y + 6))

        msg = small_font.render(self.message, True, (255, 150, 150))
        screen.blit(msg, (panel.x + 20, panel.bottom - 60))
        hint = small_font.render("Up/Down: choose   Enter: buy   Esc: close", True, (180, 180, 180))
        screen.blit(hint, (panel.x + 20, panel.bottom - 30))


def sell_selected(inventory):
    # sells one item of the selected slot, returns a message to display
    slot = inventory.get_selected()
    if slot is None:
        return "Nothing to sell"
    price = ITEMS[slot["id"]].get("sell_price")
    if price is None:
        return "Can't sell this"
    inventory.gold += price
    inventory.remove_one_selected()
    return f"Sold for {price} gold"