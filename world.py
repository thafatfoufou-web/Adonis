import pygame

TILE_SIZE = 32

COLORS = {
    "1": (60, 120, 60),   # grass
    "2": (90, 90, 90),    # wall
}


class TileMap:
    def __init__(self, path):
        self.rows = []
        with open(path) as f:
            for line in f:
                if line.strip():  # skip empty lines
                    self.rows.append(line.split())

    def draw(self, screen):
        for y, row in enumerate(self.rows):
            for x, char in enumerate(row):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, COLORS[char], rect)

    def get_tile(self, tx, ty):
        # outside the map counts as a wall
        if ty < 0 or ty >= len(self.rows):
            return "2"
        if tx < 0 or tx >= len(self.rows[ty]):
            return "2"
        return self.rows[ty][tx]

    def is_solid(self, tx, ty):
        return self.get_tile(tx, ty) == "2"

    def collides(self, rect):
        # first and last tile covered by the rectangle
        left = rect.left // TILE_SIZE
        right = (rect.right - 1) // TILE_SIZE
        top = rect.top // TILE_SIZE
        bottom = (rect.bottom - 1) // TILE_SIZE

        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if self.is_solid(tx, ty):
                    return True
        return False