"""Story progress: a set of named flags that say what has happened so far."""


class Story:
    """Remembers which story events happened, as flags like "met_mira" or "hive_built"."""

    def __init__(self):
        """Start with no flag set."""
        self.flags = set()

    def set(self, flag):
        """Mark a story event as done."""
        self.flags.add(flag)

    def set_many(self, flags):
        """Mark several story events as done."""
        for flag in flags:
            self.set(flag)

    def clear(self, flag):
        """Mark a story event as not done (nothing happens if it was not set)."""
        self.flags.discard(flag)

    def has(self, flag):
        """Return True if the story event happened."""
        return flag in self.flags