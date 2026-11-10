import os
import pygame

SHEET = "assets/tiles/tiles-grass-32x32.png"
OUT = "assets/tiles/sheet"
T = 32  # tile size

sheet = pygame.image.load(SHEET)
os.makedirs(OUT, exist_ok=True)

count = 0
for row in range(sheet.get_height() // T):
    for col in range(sheet.get_width() // T):
        tile = sheet.subsurface(pygame.Rect(col * T, row * T, T, T)).copy()
        # skip completely empty (transparent) squares
        if pygame.mask.from_surface(tile).count() == 0:
            continue
        pygame.image.save(tile, f"{OUT}/grass_{col}_{row}.png")
        count += 1

print(count, "tiles saved in", OUT)