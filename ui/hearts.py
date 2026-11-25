"""Hearts: the picture of friendship, full or empty (drawn on the Villagers page of the quest book)."""

import pygame
import config
from core.assets import load_image

_cache = {}


def get_heart(size, filled):
    """Return a heart picture of size x size pixels: the normal one, or a dim grey one for an empty heart."""
    key = (size, filled)
    if key in _cache:
        return _cache[key]
    heart = load_image(config.HEART_IMAGE, (size, size), config.ACCENT)
    if not filled:
        heart = heart.copy()
        for x in range(size):
            for y in range(size):
                r, g, b, a = heart.get_at((x, y))
                if a > 0:
                    grey = int((r + g + b) / 3 * 0.55)
                    heart.set_at((x, y), (grey, grey, grey, min(a, 150)))
    _cache[key] = heart
    return heart


def draw_hearts(screen, pos, filled, total=None, size=16, gap=2):
    """Draw a row of hearts from pos (top left): the first `filled` are full, the others empty."""
    if total is None:
        total = config.AFFECTION["max_hearts"]
    for i in range(total):
        screen.blit(get_heart(size, i < filled), (pos[0] + i * (size + gap), pos[1]))
