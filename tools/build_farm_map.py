"""Builds maps/farm_big.txt (60 x 46 tiles). Run it from the project folder:  python tools/build_farm_map.py

The map is made by code so the roads, the pond and the walls always fit together
(each road tile is chosen from its neighbours). The decoration is random but uses
a fixed seed, so you get the same map every time. Edit the "LAYOUT" part, run again.

Tile ids (see data/tiles.json):
  1 grass   2 brick wall   4 shipping box   5 road   6 water   7 / 9 bush   8 fence
  10-19 road pieces   20-27 pond edges   30-37 border wall   40/41 hedge
  50 lily   51 azalea   52 stepping stones   80-84 fence pieces
"""
import random

W, H = 60, 46
grid = [["1"] * W for _ in range(H)]
roads = set()      # road cells, the right piece is chosen at the end
water = set()
blocked = set()    # tiles where no bush or flower may be added
near_road = set()  # tiles next to a road: flowers are welcome there, bushes are not


def fill(x0, y0, x1, y1, tile):
    """Put a tile on every cell of a rectangle (both corners included)."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grid[y][x] = tile


def block(x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            blocked.add((x, y))


def road(points):
    """Add a road through the given corner points (straight lines between them)."""
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        for x in range(min(ax, bx), max(ax, bx) + 1):
            for y in range(min(ay, by), max(ay, by) + 1):
                roads.add((x, y))


def pond(x0, y0, x1, y1):
    """A rectangular pond with rounded corners: 8 edge pieces and water in the middle."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            top, bottom = y == y0, y == y1
            left, right = x == x0, x == x1
            if top and left:      tile = "20"
            elif top and right:   tile = "22"
            elif bottom and left: tile = "25"
            elif bottom and right: tile = "27"
            elif top:    tile = "21"
            elif left:   tile = "23"
            elif right:  tile = "24"
            elif bottom: tile = "26"
            else:        tile = "6"
            grid[y][x] = tile
            water.add((x, y))
    block(x0 - 1, y0 - 1, x1 + 1, y1 + 1)


def fence_rect(x0, y0, x1, y1, gaps=()):
    """A fence around a rectangle. gaps = cells left open (gates)."""
    for x in range(x0, x1 + 1):
        grid[y0][x] = "8"
        grid[y1][x] = "8"
    for y in range(y0, y1 + 1):
        grid[y][x0] = "80"
        grid[y][x1] = "80"
    grid[y0][x0], grid[y0][x1] = "81", "82"     # top corners (go right/down, left/down)
    grid[y1][x0], grid[y1][x1] = "83", "84"     # bottom corners (go right/up, left/up)
    for gx, gy in gaps:
        grid[gy][gx] = "1"


# ---------------------------------------------------------------- LAYOUT
# 1. the border: a wall all around, then hedges (4 rows on top, 3 at the bottom,
#    2 columns on the sides) so nothing walkable is hidden behind the HUD
for x in range(W):
    grid[0][x] = "31"
    grid[H - 1][x] = "36"
for y in range(H):
    grid[y][0] = "33"
    grid[y][W - 1] = "34"
grid[0][0], grid[0][W - 1] = "30", "32"
grid[H - 1][0], grid[H - 1][W - 1] = "35", "37"
for y in range(1, H - 1):
    for x in range(1, W - 1):
        if y <= 3 or y >= H - 3 or x == 1 or x == W - 2:
            grid[y][x] = "41" if (x + 2 * y) % 3 == 0 else "40"
block(0, 0, W - 1, 3)
block(0, H - 3, W - 1, H - 1)
block(0, 0, 1, H - 1)
block(W - 2, 0, W - 1, H - 1)

# 2. the two houses (they are in data/buildings.json): keep the ground in front free
block(2, 0, 7, 9)          # farmhouse
block(10, 0, 15, 9)        # shop
grid[9][8] = "4"           # shipping box, next to the farmhouse
block(7, 8, 9, 10)

# 3. the roads: a main street, and a loop around the village green
road([(5, 8), (5, 12)])            # farmhouse door -> garden gate
road([(13, 8), (13, 10)])          # shop door -> street
road([(5, 10), (46, 10)])          # main street
road([(24, 10), (24, 31), (46, 31), (46, 10)])   # the loop
road([(35, 31), (35, 36)])         # path south to the little pond

# 4. ponds
pond(31, 17, 41, 24)               # the big pond, in the middle of the loop
pond(32, 37, 38, 41)               # a small one in the south, at the end of the path

# 5. the home garden, fenced, under the farmhouse (the gate lines up with the path)
fence_rect(3, 12, 14, 22, gaps=[(5, 12), (14, 17), (14, 18)])
block(2, 11, 15, 23)

# 6. stepping stones: from the garden gate to the loop, and from the loop to the pond
for x in range(15, 24):
    grid[17 + (x % 2)][x] = "52"
for x in range(25, 31):
    grid[20 + (x % 2)][x] = "52"

# 7. the flower beds next to the shop (Mira's stall): lilies and azaleas
for y in range(5, 9):
    for x in range(17, 23):
        if (x * 3 + y * 5) % 11 != 0:
            grid[y][x] = "50" if (x + y) % 2 == 0 else "51"
block(17, 4, 23, 9)

# flowers at the foot of the houses, and a small garden between them
for tile in [(3, 8), (7, 8), (10, 8), (11, 8), (15, 8), (16, 8), (8, 5), (9, 5), (8, 6), (9, 6), (8, 7), (9, 7)]:
    grid[tile[1]][tile[0]] = "50" if (tile[0] + tile[1]) % 2 == 0 else "51"

# the open farmland (nothing is added here, it is for the player)
block(4, 25, 21, 40)
# the places where the villagers stand (see data/npcs.json)
for tile in [(2, 8), (20, 9), (23, 12), (29, 26), (9, 10), (43, 20), (14, 9)]:
    block(tile[0], tile[1], tile[0], tile[1])

# ---------------------------------------------------------------- roads: pick each piece
PIECES = {  # (north, east, south, west) -> tile id
    (1, 0, 1, 0): "5", (0, 1, 0, 1): "10",
    (0, 1, 1, 0): "11", (0, 0, 1, 1): "12", (1, 1, 0, 0): "13", (1, 0, 0, 1): "14",
    (0, 1, 1, 1): "15", (1, 1, 0, 1): "16", (1, 1, 1, 0): "17", (1, 0, 1, 1): "18",
    (1, 1, 1, 1): "19",
    (1, 0, 0, 0): "5", (0, 0, 1, 0): "5", (0, 1, 0, 0): "10", (0, 0, 0, 1): "10",
    (0, 0, 0, 0): "5",
}
for (x, y) in roads:
    key = tuple(int(c in roads) for c in [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)])
    grid[y][x] = PIECES[key]
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            near_road.add((x + dx, y + dy))

# ---------------------------------------------------------------- decoration
rng = random.Random(11)


def scatter(tiles, zone, clusters, size, spread=1, flowers=False):
    """Drop small groups of the given tiles inside zone = (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = zone
    for _ in range(clusters):
        cx, cy = rng.randint(x0, x1), rng.randint(y0, y1)
        placed, tries = 0, 0
        while placed < size and tries < 40:
            tries += 1
            x = cx + rng.randint(-spread, spread)
            y = cy + rng.randint(-spread, spread)
            if not (x0 <= x <= x1 and y0 <= y <= y1):
                continue
            if grid[y][x] != "1" or (x, y) in blocked:
                continue
            if not flowers and (x, y) in near_road:
                continue
            grid[y][x] = rng.choice(tiles)
            placed += 1


BUSH = ["7", "9"]
FLOWER = ["50", "51"]
# the forest on the east side, bushes between the houses and around the pond
scatter(BUSH, (48, 5, 57, 42), 26, 5)
scatter(BUSH, (24, 4, 47, 9), 6, 4)
scatter(BUSH, (26, 12, 45, 29), 7, 3)
scatter(BUSH, (24, 33, 47, 42), 9, 4)
scatter(BUSH, (2, 24, 23, 42), 4, 2)    # only a few on the edge of the farmland
# flowers: everywhere in small groups, more by the pond and in the forest
scatter(FLOWER, (2, 4, 57, 42), 60, 5, spread=2, flowers=True)
scatter(FLOWER, (26, 12, 45, 29), 22, 5, spread=2, flowers=True)   # around the pond
scatter(FLOWER, (4, 24, 22, 41), 8, 3, spread=2, flowers=True)     # a few on the farmland

# a bush in every walkable pocket that the player could not reach (closed by bushes or houses)
SOLID = {"2", "4", "6", "7", "8", "9", "40", "41"} | {str(i) for i in range(20, 38)} | {str(i) for i in range(80, 85)}
seen, todo = {(2, 8)}, [(2, 8)]
while todo:
    x, y = todo.pop()
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in seen and grid[ny][nx] not in SOLID:
            # the houses block these tiles too: shop and farmhouse hitboxes
            if (2 <= nx <= 7 and 5 <= ny <= 7) or (10 <= nx <= 15 and 5 <= ny <= 7):
                continue
            seen.add((nx, ny))
            todo.append((nx, ny))
for y in range(H):
    for x in range(W):
        in_house = (2 <= x <= 7 and y <= 7) or (10 <= x <= 15 and y <= 7)
        if grid[y][x] not in SOLID and (x, y) not in seen and not in_house:
            grid[y][x] = rng.choice(BUSH)

# ---------------------------------------------------------------- write the file
with open("maps/farm_big.txt", "w") as f:
    for row in grid:
        f.write(" ".join(row) + "\n")
print("maps/farm_big.txt written:", W, "x", H)
