"""Drawing helpers for the pixel-art interface (colors and sizes are in config.py).

The pieces (panel, button, slot, bar) are small pictures in assets/ui. Each one is stretched
to any size with a "nine-slice": the 4 corners stay as they are, the 4 edges stretch in one
direction and the middle stretches in both. If a picture file is missing, a plain colored
rectangle is drawn instead, so the game still runs.

The interface has two skins: "calm" (cream and tan) and "grave" (flesh buttons, for the dark
moments of the story). Change it with set_skin("grave") and back with set_skin("calm").
"""

import os
import pygame
import config

ART_FOLDER = "assets/ui/"

# piece name -> (file, borders (left, top, right, bottom) in pixels, shrink factor)
# The borders are the parts of the picture that must never be stretched.
PIECES = {
    "panel":       ("66x37container.png",         (5, 5, 5, 7), 1),
    "button":      ("90X27container.png",         (5, 5, 5, 6), 1),
    "button_down": ("90x27containerPressed.png",  (5, 5, 5, 5), 1),
    "slot":        ("inventorySlot.png",          (4, 4, 4, 5), 1),
    "slot_down":   ("inventorySlotPressed.png",   (4, 4, 4, 4), 1),
    "bar":         ("96x12ProgressBar.png",       (2, 2, 2, 2), 1),
    "dialogue_zoe":   ("90X27containerZoe.png",      (5, 5, 5, 6), 1),   # colored dialogue boxes, see config.DIALOGUE_STYLES
    "dialogue_maya":  ("90X27containerMaya.png",     (5, 5, 5, 6), 1),
    "dialogue_cyrus": ("90X27containerZoeCyrus.png", (5, 5, 5, 6), 1),
    "dialogue_tom":    ("90X27containerTom.png",         (5, 5, 5, 6), 1),
    "dialogue_jonas":  ("90X27containerJonas.png",       (5, 5, 5, 6), 1),
    "dialogue_ariane": ("90X27containerJonasAriane.png", (5, 5, 5, 6), 1),   # the green box (the file name is a leftover)
    "dialogue_clover": ("90X27containerClover.png",      (5, 5, 5, 6), 1),
    "dialogue_elder":  ("90X27containerElder.png",       (5, 5, 5, 6), 1),   # grey box shared by Walter and Martha
}


# the flesh pictures are drawn 16 times too big in their files, so they are shrunk back by 16
GRAVE_PIECES = {
    "button":      ("Button_Flesh.png",         (3, 3, 3, 3), 16),
    "button_down": ("Button_Flesh_Pressed.png", (3, 3, 3, 3), 16),
}

# colors used when a picture file is missing: (fill, edge)
FALLBACK_COLORS = {
    "panel":       ((255, 240, 205), (131, 66, 39)),
    "button":      ((232, 207, 166), (170, 121, 89)),
    "button_down": ((220, 185, 138), (170, 121, 89)),
    "slot":        ((232, 207, 166), (170, 121, 89)),
    "slot_down":   ((220, 185, 138), (170, 121, 89)),
    "bar":         ((204, 134, 105), (159, 67, 42)),
    "dialogue_zoe":   ((157, 199, 222), (170, 121, 89)),
    "dialogue_maya":  ((252, 144, 85), (170, 121, 89)),
    "dialogue_cyrus": ((114, 114, 132), (170, 121, 89)),
    "dialogue_tom":    ((159, 105, 105), (170, 121, 89)),
    "dialogue_jonas":  ((255, 220, 114), (170, 121, 89)),
    "dialogue_ariane": ((109, 142, 113), (170, 121, 89)),
    "dialogue_clover": ((225, 148, 102), (170, 121, 89)),
    "dialogue_elder":  ((195, 194, 193), (170, 121, 89)),

}

_skin = "calm"
_images = {}          # file name -> loaded picture (or None if the file does not exist)
_sliced = {}          # (file name, size) -> stretched picture


def set_skin(name):
    """Choose the look of the buttons: "calm" or "grave"."""
    global _skin
    _skin = name


def get_skin():
    """Return the current skin name."""
    return _skin


def get_piece(name):
    """Return (picture, borders) of a piece for the current skin; the picture is None if its file is missing."""
    table = PIECES
    if _skin == "grave" and name in GRAVE_PIECES:
        table = GRAVE_PIECES
    file_name, borders, shrink = table[name]
    borders = tuple(b * config.UI_PIXEL_SCALE for b in borders)

    if file_name not in _images:
        path = ART_FOLDER + file_name
        if os.path.exists(path):
            picture = pygame.image.load(path).convert_alpha()
            # draw every interface pixel as big as a world pixel (config.UI_PIXEL_SCALE)
            size = (picture.get_width() * config.UI_PIXEL_SCALE // shrink,
                    picture.get_height() * config.UI_PIXEL_SCALE // shrink)
            if size != picture.get_size():
                picture = pygame.transform.scale(picture, size)
            _images[file_name] = picture
        else:
            print("[theme] missing picture: " + path + " (plain rectangle used)")
            _images[file_name] = None
    return _images[file_name], borders, file_name


def nine_slice(image, size, borders):
    """Return the picture stretched to size, keeping its corners and borders sharp."""
    left, top, right, bottom = borders
    width = max(size[0], left + right + 1)
    height = max(size[1], top + bottom + 1)
    image_width, image_height = image.get_size()

    source_x = [0, left, image_width - right, image_width]
    source_y = [0, top, image_height - bottom, image_height]
    target_x = [0, left, width - right, width]
    target_y = [0, top, height - bottom, height]

    result = pygame.Surface((width, height), pygame.SRCALPHA)
    for row in range(3):
        for column in range(3):
            source_w = source_x[column + 1] - source_x[column]
            source_h = source_y[row + 1] - source_y[row]
            target_w = target_x[column + 1] - target_x[column]
            target_h = target_y[row + 1] - target_y[row]
            if source_w <= 0 or source_h <= 0 or target_w <= 0 or target_h <= 0:
                continue
            part = image.subsurface((source_x[column], source_y[row], source_w, source_h))
            if (source_w, source_h) != (target_w, target_h):
                part = pygame.transform.scale(part, (target_w, target_h))
            result.blit(part, (target_x[column], target_y[row]))
    return result


def draw_piece(screen, rect, name):
    """Draw a piece (panel, button, slot...) stretched to fill rect."""
    image, borders, file_name = get_piece(name)

    if image is None:
        fill, edge = FALLBACK_COLORS[name]
        pygame.draw.rect(screen, fill, rect, border_radius=4)
        pygame.draw.rect(screen, edge, rect, 2, border_radius=4)
        return

    key = (file_name, rect.size)
    if key not in _sliced:
        _sliced[key] = nine_slice(image, rect.size, borders)
    screen.blit(_sliced[key], rect.topleft)


def draw_frame(screen, rect):
    """Draw a cream panel."""
    draw_piece(screen, rect, "panel")


def draw_menu_button(screen, rect, hovered=False):
    """Draw the square button with three lines that opens the pause menu."""
    draw_piece(screen, rect, "button_down" if hovered else "button")
    color = config.ACCENT if hovered else config.TEXT
    for offset in (-8, 0, 8):
        line = pygame.Rect(0, 0, 26, 4)
        line.center = (rect.centerx, rect.centery - 1 + offset)
        pygame.draw.rect(screen, color, line)

def draw_panel(screen, rect, border=config.PANEL_BORDER):
    """Draw a cream panel and return the rectangle inside its border, where the content goes."""
    draw_frame(screen, rect)
    return rect.inflate(-2 * border, -2 * border)


def draw_inset(screen, rect):
    """Draw a sunken tan area (the name box, the bar's trough)."""
    draw_piece(screen, rect, "slot_down")


def draw_slot(screen, rect, selected=False):
    """Draw one inventory slot; the selected one is sunken and has a red-brown outline."""
    draw_piece(screen, rect, "slot_down" if selected else "slot")
    if selected:
        pygame.draw.rect(screen, config.ACCENT, rect, 2, border_radius=3)


def draw_button_base(screen, rect, selected=False):
    """Draw a button without a label (used for the shop rows). The selected one looks pressed."""
    draw_piece(screen, rect, "button_down" if selected else "button")


def get_label_color(selected):
    """Return (text color, shadow wanted) for a label on a button, depending on the skin."""
    if _skin == "grave":
        return config.GRAVE_TEXT, True
    if selected:
        return config.ACCENT, False
    return config.TEXT, False


def draw_button(screen, font, rect, label, selected=False):
    """Draw a button with its label centered. A small arrow shows the selected one."""
    draw_button_base(screen, rect, selected)
    color, shadow = get_label_color(selected)
    draw_text(screen, font, label, color, (rect.centerx, rect.centery - 1), "center", shadow)

    if selected:
        x = rect.left + 14
        y = rect.centery - 1
        points = [(x, y - 5), (x, y + 5), (x + 6, y)]
        pygame.draw.polygon(screen, color, points)


def draw_bar(screen, rect, fraction, low=False):
    """Draw a bar: a sunken trough with the picture of the bar inside, filled up to fraction (0 to 1).

    low=True tints the fill red (used when the energy is almost empty).
    """
    draw_inset(screen, rect)
    inner = rect.inflate(-12, -12)
    width = int(inner.width * max(0.0, min(1.0, fraction)))
    if width < 8:
        return

    fill_rect = pygame.Rect(inner.x, inner.y, width, inner.height)
    image, borders, file_name = get_piece("bar")
    if image is None:
        pygame.draw.rect(screen, config.ACCENT, fill_rect)
        return

    fill = nine_slice(image, fill_rect.size, borders)
    if low:
        fill.fill((255, 110, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(fill, fill_rect.topleft)


def draw_text(screen, font, content, color, pos, anchor="topleft", shadow=False):
    """Draw text and return the rectangle it covers.

    anchor says which point of the text goes at pos, for example "center" or "topright".
    shadow=True adds a small dark shadow; use it for light text drawn on the world or on a picture.
    """
    label = font.render(content, True, color)
    rect = label.get_rect()
    setattr(rect, anchor, pos)
    if shadow:
        shadow_label = font.render(content, True, config.SHADOW)
        screen.blit(shadow_label, (rect.x + 1, rect.y + 1))
    screen.blit(label, rect)
    return rect


def draw_name_label(screen, font, text, midbottom):
    """Draw a name (above a villager) in cream letters on a small dark plate, so it reads on any ground."""
    label = font.render(text, True, config.NPC_NAME_COLOR)
    plate = pygame.Surface((label.get_width() + 6, label.get_height()), pygame.SRCALPHA)
    pygame.draw.rect(plate, (*config.LABEL_BG, 140), plate.get_rect(), border_radius=3)
    plate.blit(label, (3, 0))
    screen.blit(plate, plate.get_rect(midbottom=midbottom))


_cursor = None


def use_pixel_cursor():
    """Hide the system mouse cursor if the pixel arrow exists (call once after the window is created)."""
    if os.path.exists(ART_FOLDER + "mouse.png"):
        pygame.mouse.set_visible(False)


def draw_cursor(screen):
    """Draw the pixel mouse arrow (assets/ui/mouse.png) at the mouse position.

    The system cursor must be hidden for this, with pygame.mouse.set_visible(False).
    """
    global _cursor
    if _cursor is None:
        path = ART_FOLDER + "mouse.png"
        if os.path.exists(path):
            _cursor = pygame.image.load(path).convert_alpha()
        else:
            _cursor = False
    if _cursor:
        screen.blit(_cursor, pygame.mouse.get_pos())