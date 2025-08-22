import sys
import time
from typing import Iterator, Optional

class ProgressBar:
    def __init__(self, total: int, description: str = "", width: int = 50):
        self.total = total
        self.description = description
        self.width = width
        self.current = 0
        self.start_time = time.time()
    
    def update(self, amount: int = 1) -> None:
        self.current = min(self.current + amount, self.total)
        self._render()
    
    def set_progress(self, current: int) -> None:
        self.current = min(current, self.total)
        self._render()
    
    def _render(self) -> None:
        percent = (self.current / self.total) * 100 if self.total > 0 else 0
        filled = int((self.current / self.total) * self.width) if self.total > 0 else 0
        bar = "█" * filled + "░" * (self.width - filled)
        
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0
        eta = (self.total - self.current) / rate if rate > 0 else 0
        
        sys.stdout.write(f"\r{self.description} |{bar}| {percent:.1f}% ({self.current}/{self.total}) ETA: {eta:.0f}s")
        sys.stdout.flush()
    
    def finish(self) -> None:
        self.current = self.total
        self._render()
        sys.stdout.write("\n")
        sys.stdout.flush()

def create_progress_bar(total: int, description: str = "") -> ProgressBar:
    return ProgressBar(total, description)