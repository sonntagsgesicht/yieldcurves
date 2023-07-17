
from datetime import date as _date, timedelta as _timedelta

DAYS_IN_YEAR = 365.25


class date(_date):
    __slots__ = '_year', '_month', '_day', '_hashcode', 'origin', 'day_count'
    BASE_DATE = _date.today()

    def __add__(self, other):
        dt = super().__add__(other)
        dt = date(dt.year, dt.month, dt.day)
        dt.origin = self
        dt.day_count = self.day_count
        return dt

    def __sub__(self, other):
        td = timedelta(super().__sub__(other).days)
        td.origin = self
        return td

    def __int__(self):
        return int(self - getattr(self, 'origin', self.BASE_DATE))

    def __float__(self):
        if getattr(self, 'day_count', None) is None:
            return int(self) / DAYS_IN_YEAR
        return self.day_count(getattr(self, 'origin', self.BASE_DATE), self)


class timedelta(_timedelta):
    __slots__ = '_days', '_seconds', '_microseconds', '_hashcode', 'origin'

    def __int__(self):
        return self.days

    def __float__(self):
        if getattr(self, 'origin', None) is None:
            return int(self) / DAYS_IN_YEAR
        return float(self.origin + self)
