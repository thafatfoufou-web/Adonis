"""Drawing helpers for the wooden look of the interface (colors are in config.py)."""

import pygame
import config


def draw_frame(screen, rect):
    """Draw a wooden frame: dark outline, wood, a light edge top-left and a dark edge bottom-right."""
    pygame.draw.rect(screen, config.OUTLINE, rect)
    inner = rect.inflate(-4, -4)
    pygame.draw.rect(screen, config.WOOD, inner)
    pygame.draw.line(screen, config.WOOD_LIGHT, inner.topleft, (inner.right - 1, inner.top))
    pygame.draw.line(screen, config.WOOD_LIGHT, inner.topleft, (inner.left, inner.bottom - 1))
    pygame.draw.line(screen, config.WOOD_DARK, (inner.left, inner.bottom - 1), (inner.right - 1, inner.bottom - 1))
    pygame.draw.line(screen, config.WOOD_DARK, (inner.right - 1, inner.top), (inner.right - 1, inner.bottom - 1))


def draw_inset(screen, rect, color=config.INSET):
    """Draw a sunken area with a thin dark outline."""
    pygame.draw.rect(screen, config.OUTLINE, rect)
    pygame.draw.rect(screen, color, rect.inflate(-2, -2))


def draw_panel(screen, rect, border=config.PANEL_BORDER):
    """Draw a wooden frame with a sunken area inside and return that inside rectangle."""
    draw_frame(screen, rect)
    inner = rect.inflate(-2 * border, -2 * border)
    draw_inset(screen, inner)
    return inner


def draw_text(screen, font, content, color, pos, anchor="topleft", shadow=True):
    """Draw text with a small dark shadow and return the rectangle it covers.

    anchor says which point of the text goes at pos, for example "center" or "topright".
    """
    label = font.render(content, True, color)
    rect = label.get_rect()
    setattr(rect, anchor, pos)
    if shadow:
        shadow_label = font.render(content, True, config.OUTLINE)
        screen.blit(shadow_label, (rect.x + 1, rect.y + 1))
    screen.blit(label, rect)
    return rect
