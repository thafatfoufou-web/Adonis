"""Item definitions and prices, read from data/items.json."""

import json
import config


def load_items(path):
    """Read the item file and return a dictionary: item id -> item data."""
    with open(path) as f:
        items = json.load(f)

    for item in items.values():
        item["color"] = tuple(item["color"])
    return items


ITEMS = load_items(config.ITEMS_FILE)


def get_buy_price(item_id):
    """Return the shop price of an item, or None if the shop does not sell it."""
    return ITEMS[item_id].get("buy_price")


def get_sell_price(item_id):
    """Return what the shipping box pays for an item, or None if it cannot be sold."""
    return ITEMS[item_id].get("sell_price")
