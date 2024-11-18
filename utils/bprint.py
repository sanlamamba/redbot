"""
A module to print messages with timestamps. 
"""

from datetime import datetime


class Bprint:
    """A class to print messages with timestamps."""

    def log(self, *args, **kwargs):
        """Print a message with a timestamp."""
        print(f"[{datetime.now()}]", *args, **kwargs)

    def error(self, *args, **kwargs):
        """Print an error message with a timestamp."""
        print(f"[{datetime.now()}] [ERROR]", *args, **kwargs)

    def info(self, *args, **kwargs):
        """Print an info message with a timestamp."""
        print(f"[{datetime.now()}] [INFO]", *args, **kwargs)

    def warning(self, *args, **kwargs):
        """Print a warning message with a timestamp."""
        print(f"[{datetime.now()}] [WARNING]", *args, **kwargs)

    def success(self, *args, **kwargs):
        """Print a success message with a timestamp."""
        print(f"[{datetime.now()}] [SUCCESS]", *args, **kwargs)


bprint = Bprint()
