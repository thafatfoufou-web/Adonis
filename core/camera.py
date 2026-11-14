"""The camera: which part of the world is visible, and world/screen conversions."""


class Camera:
    """Decides which part of the world is visible and converts between world and screen.

    World coordinates are pixels on the whole map (game logic).
    Screen coordinates are pixels on the window (mouse and HUD).
    """

    def __init__(self, view_size, map_size, padding=(0, 0, 0, 0)):
        """Create the camera for a window of view_size and a map of map_size pixels."""
        self.view_w, self.view_h = view_size
        self.x = 0
        self.y = 0
        self.set_bounds(map_size, padding)

    def set_bounds(self, map_size, padding=(0, 0, 0, 0)):
        """Set how far the camera can scroll; padding is (left, top, right, bottom) past the map edge."""
        pad_left, pad_top, pad_right, pad_bottom = padding
        self.min_x = -pad_left
        self.min_y = -pad_top
        self.max_x = map_size[0] + pad_right - self.view_w
        self.max_y = map_size[1] + pad_bottom - self.view_h

    def clamp(self, value, low, high):
        """Keep value between low and high, or return the middle if the map is smaller than the screen."""
        if high < low:
            return (low + high) / 2
        return max(low, min(value, high))

    def follow(self, point):
        """Center the camera on a world point without leaving the map, in whole pixels."""
        x = self.clamp(point[0] - self.view_w / 2, self.min_x, self.max_x)
        y = self.clamp(point[1] - self.view_h / 2, self.min_y, self.max_y)
        self.x = int(round(x))
        self.y = int(round(y))

    def to_world(self, screen_pos):
        """Convert a screen position (the mouse) to a world position."""
        return (screen_pos[0] + self.x, screen_pos[1] + self.y)

    def to_screen(self, world_pos):
        """Convert a world position to a screen position."""
        return (world_pos[0] - self.x, world_pos[1] - self.y)

    def visible_tiles(self, tile_size):
        """Return (first_col, first_row, last_col, last_row) of the visible tiles; last values are excluded."""
        first_col = self.x // tile_size
        first_row = self.y // tile_size
        last_col = (self.x + self.view_w) // tile_size + 1
        last_row = (self.y + self.view_h) // tile_size + 1
        return first_col, first_row, last_col, last_row
