import json
import pygame
from world import TILE_SIZE


def load_npcs(path):
    with open(path) as f:
        data = json.load(f)
    return [NPC(entry) for entry in data["npcs"]]


class NPC:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.color = tuple(data["color"])
        self.schedule = data["schedule"]  # sorted by hour
        first = self.schedule[0]["tile"]
        self.tile = (first[0], first[1])

    def update(self, minutes):
        # the last schedule entry whose hour has passed wins
        hour = minutes / 60
        tile = self.schedule[0]["tile"]
        for entry in self.schedule:
            if hour >= entry["hour"]:
                tile = entry["tile"]
        self.tile = (tile[0], tile[1])

    def get_rect(self):
        rect = pygame.Rect(0, 0, 24, 24)
        rect.center = (self.tile[0] * TILE_SIZE + TILE_SIZE // 2,
                       self.tile[1] * TILE_SIZE + TILE_SIZE // 2)
        return rect

    def draw(self, screen, font):
        rect = self.get_rect()
        pygame.draw.rect(screen, self.color, rect)
        label = font.render(self.name, True, (255, 255, 255))
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.y - 18))