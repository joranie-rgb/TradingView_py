"""Calendar regressions use IANA zones, not a UTC approximation of Pine."""
from datetime import datetime
from zoneinfo import ZoneInfo
import unittest

from test_review_regressions import Decisions, STRATEGIES, INDICATOR


class CalendarBoundaries(unittest.TestCase):
    def test_strategy_rejects_entries_from_candles_mixing_dates(self):
        for path in STRATEGIES:
            engine=Decisions(path.read_text(encoding='utf-8'))
            engine.environment['sessionTimezone']='America/New_York'
            opening=int(datetime.fromisoformat('2026-10-29T23:30:00-04:00').timestamp()*1000)
            day=engine.call('riskDayStamp', opening)
            for closing, expected in [('2026-10-30T00:00:00-04:00',False), ('2026-10-30T00:30:00-04:00',True)]:
                close_time=int(datetime.fromisoformat(closing).timestamp()*1000)
                crossing=engine.assignment('crossesRiskDay', currentRiskDay=day, time_close=close_time)
                self.assertEqual(crossing,expected)
                self.assertEqual(engine.assignment('executionTimeQualified',useEntrySession=False,
                    insideEntrySession=True,insideBacktestRange=True,crossesRiskDay=crossing),not expected)

    def test_crossing_midnight_and_exact_midnight_close(self):
        engine = Decisions(INDICATOR)
        engine.environment['zone'] = 'America/New_York'
        stamp = lambda text: int(datetime.fromisoformat(text).timestamp()*1000)
        opening = stamp('2026-10-29T23:30:00-04:00')
        self.assertEqual(engine.call('calendarDate', opening), engine.call('calendarDate', stamp('2026-10-30T00:00:00-04:00')-1))
        self.assertNotEqual(engine.call('calendarDate', opening), engine.call('calendarDate', stamp('2026-10-30T00:30:00-04:00')-1))

    def test_new_york_midnight_differs_from_utc_midnight(self):
        for path in STRATEGIES:
            engine = Decisions(path.read_text(encoding="utf-8"))
            engine.environment["sessionTimezone"] = "America/New_York"
            before = int(datetime.fromisoformat("2026-10-29T03:59:00+00:00").timestamp()*1000)
            after = before+60000
            self.assertTrue(engine.call("dayChanged", engine.call("riskDayStamp", after), engine.call("riskDayStamp", before)))
            self.assertEqual(engine.call("riskDayStamp", after), after)

    def test_dst_days_have_23_and_25_hours(self):
        for path in STRATEGIES:
            engine = Decisions(path.read_text(encoding="utf-8"))
            engine.environment["sessionTimezone"] = "America/New_York"
            for first, second, hours in [("2026-03-08", "2026-03-09", 23), ("2026-11-01", "2026-11-02", 25)]:
                stamps = [int(datetime.fromisoformat(day).replace(tzinfo=ZoneInfo("America/New_York")).timestamp()*1000) for day in (first, second)]
                days = [engine.call("riskDayStamp", stamp) for stamp in stamps]
                self.assertEqual((days[1]-days[0])/3600000, hours)

    def test_repeated_fall_hour_does_not_reset_day(self):
        for path in STRATEGIES:
            engine = Decisions(path.read_text(encoding="utf-8"))
            engine.environment["sessionTimezone"] = "America/New_York"
            repeated = [int(datetime(2026,11,1,1,30,tzinfo=ZoneInfo("America/New_York"),fold=fold).timestamp()*1000) for fold in (0,1)]
            self.assertEqual(engine.call("riskDayStamp", repeated[0]), engine.call("riskDayStamp", repeated[1]))
