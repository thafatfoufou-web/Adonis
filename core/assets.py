"""Image loading with a cache and colored placeholders for missing files."""

import os
import pygame

_cache = {}
_warned = set()


def make_placeholder(size, color):
    """Return a plain colored surface, used when an image file does not exist."""
    surface = pygame.Surface(size)
    surface.fill(tuple(color))
    return surface


def load_image(path, size, fallback_color):
    """Load an image scaled to size (hard pixel edges) and cache it.

    A missing file gives a colored square and prints the missing path once.
    """
    key = (path, size)
    if key in _cache:
        return _cache[key]

    if path is not None and os.path.exists(path):
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.scale(image, size)
    else:
        if path is not None and path not in _warned:
            print("[assets] missing image: " + path + " (placeholder used)")
            _warned.add(path)
        image = make_placeholder(size, fallback_color)

    _cache[key] = image
    return image


def load_font(path, size):
    """Load a .ttf font at size. A missing or broken file gives pygame's default font and prints a warning once."""
    key = ("font", path, size)
    if key in _cache:
        return _cache[key]
    font = None
    if path is not None and os.path.exists(path):
        try:
            font = pygame.font.Font(path, size)
        except Exception as error:
            print("[assets] could not load font " + path + ": " + str(error))
    elif path is not None and path not in _warned:
        print("[assets] missing font: " + path + " (default font used)")
        _warned.add(path)
    if font is None:
        font = pygame.font.Font(None, size + 4)
    _cache[key] = font
    return font

