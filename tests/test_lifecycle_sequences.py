"""Sequence contracts for source decisions; these do not emulate broker fills.

Fixtures supply observed fills/valuations. Pine's hosted runtime must establish
when those observations actually become available.
"""
from datetime import datetime
import unittest

from test_review_regressions import Decisions, STRATEGIES, INDICATOR


class LifecycleSequences(unittest.TestCase):
    def test_entry_partial_partial_full_and_new_entry(self):
        for path in STRATEGIES:
            engine = Decisions(path.read_text(encoding='utf-8'))
            counted = None
            entries, exits = [], []
            # Observed timestamp, current size, previous size, new closed records.
            for entry_time, size, previous, closed in [
                (1000, 3, 0, 0), (1000, 2, 3, 1), (1000, 1, 2, 1),
                (1000, 0, 1, 1), (1000, 0, 0, 0), (2000, 2, 0, 0),
            ]:
                fresh = engine.call('freshEntry', entry_time, counted)
                entries.append(fresh)
                if fresh:
                    counted = entry_time
                exits.append(engine.call('fullPositionExit', size, previous, closed))
            self.assertEqual(entries, [True, False, False, False, False, True])
            self.assertEqual(exits, [False, False, False, True, False, False])

    def test_day_reset_carries_gap_and_first_bar_costs(self):
        stamp = lambda value: int(datetime.fromisoformat(value).timestamp()*1000)
        for path in STRATEGIES:
            engine = Decisions(path.read_text(encoding='utf-8'))
            engine.environment['sessionTimezone'] = 'America/New_York'
            previous_day = engine.call('riskDayStamp', stamp('2026-10-29T23:59:00-04:00'))
            today = engine.call('riskDayStamp', stamp('2026-10-30T00:00:00-04:00'))
            changed = engine.call('dayChanged', today, previous_day)
            baseline = engine.call('dailyBaseline', changed, 100000, 97995)
            self.assertEqual(97995-baseline, -2005)
            # Same entry may be exposed again after partial liquidation. It is
            # neither a new entry nor an entry belonging to today's calendar.
            old_entry = stamp('2026-10-29T15:00:00-04:00')
            self.assertNotEqual(engine.call('riskDayStamp', old_entry), today)
            self.assertFalse(engine.call('freshEntry', old_entry, old_entry))

    def test_pending_setup_touch_breach_expiry_and_new_date(self):
        engine = Decisions(INDICATOR)
        self.assertEqual(engine.call('setupCancellation', True, False,
            engine.call('setupInvalidated', 1, 95, 101, 95), False), '')
        self.assertEqual(engine.call('setupCancellation', True, False,
            engine.call('setupInvalidated', 1, 94.75, 101, 95), False), 'SWEEP EXTREME BROKEN')
        self.assertEqual(engine.call('setupCancellation', True, False, False, True), 'SETUP EXPIRED')
        self.assertEqual(engine.call('setupCancellation', True, True, False, False), 'SESSION RESET')
        # A newly armed setup belongs to the new date, not the expired arm.
        self.assertEqual(engine.call('setupCancellation', True, False, False, False), '')

    def test_missing_conversion_never_produces_affordable_quantity(self):
        for path in STRATEGIES:
            engine = Decisions(path.read_text(encoding='utf-8'))
            self.assertEqual(engine.call('affordableContracts', 100000, None), 0)
            self.assertEqual(engine.call('capContracts', 10, 10, 10, 0, 10), 0)
