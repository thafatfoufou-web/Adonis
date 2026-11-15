"""The mood of the world: a tinted layer drawn over the game world, under the interface."""

import pygame
import config


def blend(color, strength):
    """Mix a color with white. At strength 0 the result is white (multiplying by it changes nothing)."""
    return tuple(round(255 + (c - 255) * strength) for c in color)


class Mood:
    """A cool, darker tint with a soft mist at the bottom, laid over the bright tiles.

    The tint is multiplied with the picture, so shadows stay dark and the interface,
    drawn afterwards, is not affected. Layers are built once per strength and kept.
    """

    def __init__(self, size):
        """Create the mood for a screen of this size."""
        self.size = size
        self.cache = {}

    def build(self, strength):
        """Return the two layers for a strength: the tint (multiplied) and the mist (drawn normally)."""
        width, height = self.size
        top = blend(config.MOOD_TOP, strength)
        bottom = blend(config.MOOD_BOTTOM, strength)

        tint = pygame.Surface(self.size)
        for y in range(height):
            ratio = y / (height - 1)
            color = tuple(round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
            pygame.draw.line(tint, color, (0, y), (width, y))

        mist = pygame.Surface(self.size, pygame.SRCALPHA)
        mist_height = config.MOOD_MIST_HEIGHT
        for i in range(mist_height):
            alpha = round(config.MOOD_MIST_ALPHA * strength * i / (mist_height - 1))
            y = height - mist_height + i
            pygame.draw.line(mist, (*config.MOOD_MIST, alpha), (0, y), (width, y))
        return tint, mist

    def draw(self, screen, strength):
        """Darken and cool the screen. strength goes from 0 (nothing) to 1 (full)."""
        if strength <= 0:
            return
        key = round(strength, 2)
        if key not in self.cache:
            self.cache[key] = self.build(key)
        tint, mist = self.cache[key]
        screen.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
        screen.blit(mist, (0, 0))