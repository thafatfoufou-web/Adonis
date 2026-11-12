import pygame

# ---- the colors of the whole interface: change them here to change the mood ----
OUTLINE = (34, 23, 18)        # darkest brown: outlines and text shadows
WOOD = (118, 82, 54)          # panel frames
WOOD_LIGHT = (156, 114, 78)   # top and left edge of a frame (where the light hits)
WOOD_DARK = (84, 56, 38)      # bottom and right edge of a frame
INSET = (58, 40, 31)          # dark sunken areas: slots, rows, the inside of a panel
INSET_LIGHT = (86, 61, 46)    # a slightly lighter sunken area: selected slot or row
TEXT = (248, 236, 210)        # main text, a warm white
TEXT_DIM = (196, 176, 146)    # hints and small labels
ACCENT = (244, 200, 92)       # gold: selection, prices, gold amount
ACCENT_DARK = (176, 126, 40)  # the edge of the coin
GOOD = (150, 210, 120)        # good news ("Bought", "Sold")
BAD = (232, 128, 112)         # bad news ("Not enough gold")
DANGER = (150, 64, 52)        # the close button


def draw_frame(screen, rect):
    """Draw a wooden frame: dark outline, wood, a light edge top-left, a dark edge bottom-right."""
    pygame.draw.rect(screen, OUTLINE, rect)
    inner = rect.inflate(-4, -4)
    pygame.draw.rect(screen, WOOD, inner)
    pygame.draw.line(screen, WOOD_LIGHT, inner.topleft, (inner.right - 1, inner.top))
    pygame.draw.line(screen, WOOD_LIGHT, inner.topleft, (inner.left, inner.bottom - 1))
    pygame.draw.line(screen, WOOD_DARK, (inner.left, inner.bottom - 1), (inner.right - 1, inner.bottom - 1))
    pygame.draw.line(screen, WOOD_DARK, (inner.right - 1, inner.top), (inner.right - 1, inner.bottom - 1))


def draw_inset(screen, rect, color=INSET):
    """Draw a sunken area with a thin dark outline."""
    pygame.draw.rect(screen, OUTLINE, rect)
    pygame.draw.rect(screen, color, rect.inflate(-2, -2))


def draw_panel(screen, rect, border=8):
    """Draw a wooden frame with a sunken area inside, and return that inside rectangle."""
    draw_frame(screen, rect)
    inner = rect.inflate(-2 * border, -2 * border)
    draw_inset(screen, inner)
    return inner


def draw_text(screen, font, content, color, pos, anchor="topleft", shadow=True):
    """Draw a text with a small dark shadow, so it stays readable on any background.

    pos is where the anchor of the text goes: for example anchor="center" puts
    the middle of the text at pos, and anchor="topright" puts its top right corner there.
    Return the rectangle the text covers.
    """
    label = font.render(content, True, color)
    rect = label.get_rect()
    setattr(rect, anchor, pos)
    if shadow:
        shadow_label = font.render(content, True, OUTLINE)
        screen.blit(shadow_label, (rect.x + 1, rect.y + 1))
    screen.blit(label, rect)
    return rect