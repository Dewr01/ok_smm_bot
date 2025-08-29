# modules/ratelimit.py
import time
from collections import deque


class RateLimiter:
    """
    Простая скользящая квота: max_calls за interval_sec.
    """

    def __init__(self, max_calls: int = 10, interval_sec: float = 1.0):
        self.max_calls = max_calls
        self.interval = interval_sec
        self.calls = deque()

    def acquire(self):
        now = time.time()
        while self.calls and (now - self.calls[0]) > self.interval:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            sleep_for = self.interval - (now - self.calls[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self.calls.append(time.time())
