from collections import defaultdict
from datetime import datetime


class Limiter:
    def __init__(self, duration, amount):
        self.duration = duration
        self.amount = amount
        self.items = defaultdict(lambda: (amount, datetime.now()))

    def use(self, weight=1, key=None):
        now = datetime.now()
        allowance, last = self.items[key]
        allowance += (now - last).total_seconds() * (self.amount / self.duration.total_seconds())
        if allowance > self.amount:
            allowance = self.amount
        if allowance < weight:
            return False
        allowance -= weight
        self.items[key] = (allowance, now)
        return True
