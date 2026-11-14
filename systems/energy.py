"""The player's energy: actions spend it, sleeping restores it."""

import config


class Energy:
    """How tired the player is: every action costs some, sleeping gives it back."""

    def __init__(self):
        """Start with full energy."""
        self.maximum = config.MAX_ENERGY
        self.value = config.MAX_ENERGY

    def can_afford(self, cost):
        """Return True if there is enough energy for an action."""
        return self.value >= cost

    def spend(self, cost):
        """Use some energy (never below 0)."""
        self.value = max(0, self.value - cost)

    def restore(self, fraction):
        """Set the energy to a fraction of the maximum: 1.0 is full, 0.8 is 80%."""
        self.value = round(self.maximum * fraction)

    def get_fraction(self):
        """Return the energy as a number between 0 and 1, for the bar."""
        return self.value / self.maximum
