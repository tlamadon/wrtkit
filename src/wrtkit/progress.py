"""Progress indicators for terminal output."""

import sys
import threading
import time
from contextlib import contextmanager
from typing import Iterator, Optional


class Spinner:
    """A terminal spinner for indicating progress during long operations."""

    # Different spinner styles
    DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    BRAILLE = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
    SIMPLE = ["-", "\\", "|", "/"]
    ARROWS = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"]

    def __init__(
        self,
        message: str = "Working",
        style: Optional[list[str]] = None,
        interval: float = 0.1,
        stream: object = sys.stderr,
    ) -> None:
        """
        Initialize the spinner.

        Args:
            message: Message to display alongside the spinner
            style: List of characters to cycle through (default: DOTS)
            interval: Time between spinner updates in seconds
            stream: Output stream (default: stderr)
        """
        self.message = message
        self.frames = style or self.DOTS
        self.interval = interval
        self.stream = stream
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._current_frame = 0

    def _spin(self) -> None:
        """Internal method to animate the spinner."""
        while not self._stop_event.is_set():
            frame = self.frames[self._current_frame % len(self.frames)]
            # Clear line and write spinner
            self.stream.write(f"\r\033[K{frame} {self.message}")
            self.stream.flush()
            self._current_frame += 1
            time.sleep(self.interval)

    def start(self) -> "Spinner":
        """Start the spinner animation."""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        return self

    def stop(self, final_message: Optional[str] = None) -> None:
        """
        Stop the spinner animation.

        Args:
            final_message: Optional message to display after stopping
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

        # Clear the spinner line
        self.stream.write("\r\033[K")

        if final_message:
            self.stream.write(f"{final_message}\n")

        self.stream.flush()

    def update(self, message: str) -> None:
        """Update the spinner message while running."""
        self.message = message

    def __enter__(self) -> "Spinner":
        """Context manager entry."""
        return self.start()

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit."""
        if exc_type is not None:
            self.stop(f"✗ {self.message} - failed")
        else:
            self.stop()


class ProgressBar:
    """A simple terminal progress bar."""

    def __init__(
        self,
        total: int,
        message: str = "Progress",
        width: int = 30,
        stream: object = sys.stderr,
    ) -> None:
        """
        Initialize the progress bar.

        Args:
            total: Total number of items
            message: Message to display
            width: Width of the progress bar in characters
            stream: Output stream (default: stderr)
        """
        self.total = total
        self.message = message
        self.width = width
        self.stream = stream
        self.current = 0

    def update(self, current: Optional[int] = None, message: Optional[str] = None) -> None:
        """
        Update the progress bar.

        Args:
            current: Current progress (if None, increments by 1)
            message: Optional new message
        """
        if current is not None:
            self.current = current
        else:
            self.current += 1

        if message is not None:
            self.message = message

        self._render()

    def _render(self) -> None:
        """Render the progress bar."""
        if self.total == 0:
            percent = 100
        else:
            percent = int((self.current / self.total) * 100)

        filled = int(self.width * self.current / max(self.total, 1))
        bar = "█" * filled + "░" * (self.width - filled)

        self.stream.write(f"\r\033[K{self.message} [{bar}] {self.current}/{self.total} ({percent}%)")
        self.stream.flush()

    def finish(self, final_message: Optional[str] = None) -> None:
        """
        Complete the progress bar.

        Args:
            final_message: Optional final message to display
        """
        self.stream.write("\r\033[K")
        if final_message:
            self.stream.write(f"{final_message}\n")
        self.stream.flush()


@contextmanager
def spinner(message: str, success_message: Optional[str] = None) -> Iterator[Spinner]:
    """
    Context manager for displaying a spinner during an operation.

    Args:
        message: Message to display while spinning
        success_message: Message to display on success (default: "✓ {message}")

    Yields:
        The Spinner instance

    Example:
        with spinner("Fetching config") as s:
            # do something slow
            s.update("Fetching network config")
            # do more
    """
    s = Spinner(message)
    try:
        s.start()
        yield s
        if success_message is None:
            success_message = f"✓ {message}"
        s.stop(success_message)
    except Exception:
        s.stop(f"✗ {message} - failed")
        raise


@contextmanager
def progress_bar(total: int, message: str, success_message: Optional[str] = None) -> Iterator[ProgressBar]:
    """
    Context manager for displaying a progress bar.

    Args:
        total: Total number of items
        message: Message to display
        success_message: Message to display on completion

    Yields:
        The ProgressBar instance

    Example:
        with progress_bar(10, "Applying commands") as bar:
            for cmd in commands:
                execute(cmd)
                bar.update()
    """
    bar = ProgressBar(total, message)
    try:
        bar._render()
        yield bar
        if success_message is None:
            success_message = f"✓ {message} - done"
        bar.finish(success_message)
    except Exception:
        bar.finish(f"✗ {message} - failed")
        raise
