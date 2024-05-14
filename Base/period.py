import bisect
import datetime


class Period:
    def __init__(self, cutoff: datetime.timedelta, maxtime: datetime.datetime):
        self.times = []
        self.cutoff = cutoff
        self.maxtime = maxtime

    def append(self, time: datetime.datetime):
        ltimes = len(self.times)
        end = min(time + self.cutoff, self.maxtime)

        def check_in(i):
            if self.times[i][0] <= time <= self.times[i][1]:
                self.times[i] = (self.times[i][0], max(end, self.times[i][1]))
                return True
            return False

        def maybe_merge(i):
            if ltimes > i + 1:
                if self.times[i][1] >= self.times[i + 1][0]:
                    self.times[i] = (self.times[i][0], self.times[i + 1][1])
                    self.times.pop(i + 1)

        if ltimes == 0:
            self.times.append((time, end))
            return

        i = bisect.bisect(self.times, (time,))
        if i >= 1 and check_in(i - 1):
            maybe_merge(i - 1)
        elif i < ltimes and check_in(i):
            maybe_merge(i)
        else:
            self.times.insert(i, (time, end))
            maybe_merge(i)

    def extend(self, times):
        for time in times:
            self.append(time)

    def calc_total(self) -> datetime.timedelta:
        return sum((t2 - t1 for t1, t2 in self.times), start=datetime.timedelta())
