import datetime
import time


class Timer:
    begin = 0
    end = 0
    spend = 0

    def __init__(self):
        self.start()

    def start(self):
        self.begin = time.perf_counter()

    def stop(self):
        self.end = time.perf_counter()
        self.spend = self.end - self.begin

    def strftime(self, __format: str = '%H:%M:%S'):
        spend = int(self.spend)
        return datetime.time(
            int(spend / 60 / 60),
            int(spend / 60) % 60,
            spend % 60
        ).strftime(__format)
