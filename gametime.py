START_OF_DAY = 6 * 60       # 6:00, in minutes
END_OF_DAY = 24 * 60        # 24:00
NIGHT_START = 18 * 60       # darkness begins at 18:00
MINUTES_PER_SECOND = 20     # game minutes per real second (lower it later)
MAX_DARKNESS = 150          # max alpha of the night layer (0-255)


class GameTime:
    def __init__(self):
        self.day = 1
        self.minutes = START_OF_DAY

    def update(self, dt):
        # returns True if a new day just started
        self.minutes += MINUTES_PER_SECOND * dt
        if self.minutes >= END_OF_DAY:
            self.new_day()
            return True
        return False

    def new_day(self):
        self.day += 1
        self.minutes = START_OF_DAY

    def get_text(self):
        hours = int(self.minutes // 60)
        mins = int(self.minutes % 60)
        return f"Day {self.day}  {hours:02d}:{mins:02d}"

    def get_darkness(self):
        if self.minutes < NIGHT_START:
            return 0
        progress = (self.minutes - NIGHT_START) / (END_OF_DAY - NIGHT_START)
        return int(progress * MAX_DARKNESS)