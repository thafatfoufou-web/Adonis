"""The in-game clock: days, minutes and the darkness of the night."""

import config


class GameTime:
    """Counts the day number and the minutes since midnight."""

    def __init__(self):
        """Start on day 1 at the beginning of the day."""
        self.day = 1
        self.minutes = config.START_OF_DAY

    def update(self, dt):
        """Advance the clock by dt real seconds. Return True if midnight was reached and a new day started."""
        self.minutes += config.MINUTES_PER_SECOND * dt
        if self.minutes >= config.END_OF_DAY:
            self.new_day()
            return True
        return False

    def new_day(self):
        """Start the next day at the beginning of the day."""
        self.day += 1
        self.minutes = config.START_OF_DAY

    def get_text(self):
        """Return the text shown on the clock, like 'Day 2  14:30'."""
        hours = int(self.minutes // 60)
        mins = int(self.minutes % 60)
        return f"{self.get_season_name()} {self.get_season_day()}  {hours:02d}:{mins:02d}"

    def get_season_name(self):
        """Return the name of the current season, like 'Spring' (the year repeats after Winter)."""
        index = ((self.day - 1) // config.SEASON_LENGTH) % len(config.SEASON_NAMES)
        return config.SEASON_NAMES[index]

    def get_season_day(self):
        """Return the day of the current season, from 1 to config.SEASON_LENGTH."""
        return (self.day - 1) % config.SEASON_LENGTH + 1
    
    def is_night(self):
        """Return True once the night has started (the screen starts to get dark)."""
        return self.minutes >= config.NIGHT_START

    def get_darkness(self):
        """Return the opacity (0-255) of the night layer: 0 during the day, growing until midnight."""
        if self.minutes < config.NIGHT_START:
            return 0
        progress = (self.minutes - config.NIGHT_START) / (config.END_OF_DAY - config.NIGHT_START)
        return int(progress * config.MAX_DARKNESS)
    
