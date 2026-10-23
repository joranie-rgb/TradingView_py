"""Behavior checks for decision expressions extracted from the actual Pine files.

This deliberately small evaluator supports the pure expression subset used by
the helpers below. It is NOT a Pine compiler, order emulator, or full-script
simulator. Wiring checks complement numeric edge cases; hosted validation is
still required for fills, sessions, drawings, and realtime rollback.
"""
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import math
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
STRATEGIES = [ROOT / "futures_v7_4.pine", ROOT / "futures_v7_5.pine"]
INDICATOR = (ROOT / "liquidity_structure_v1.pine").read_text(encoding="utf-8")


def top_level(text, target):
    """Find unquoted punctuation outside parentheses, respecting escapes."""
    depth, quote, escaped = 0, None, False
    for i, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and char == target:
            return i
    return -1


def translate(expression):
    expression = expression.strip()
    # Translate parenthesized subexpressions too, including a conditional used
    # as one string-concatenation operand. Preserve quoted message punctuation.
    rebuilt, i, quote, escaped = [], 0, None, False
    while i < len(expression):
        char = expression[i]
        if quote:
            rebuilt.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
            rebuilt.append(char)
        elif char == "(":
            depth, end, inner_quote, inner_escape = 1, i+1, None, False
            while depth:
                current = expression[end]
                if inner_quote:
                    if inner_escape:
                        inner_escape = False
                    elif current == "\\":
                        inner_escape = True
                    elif current == inner_quote:
                        inner_quote = None
                elif current in "\"'":
                    inner_quote = current
                elif current == "(":
                    depth += 1
                elif current == ")":
                    depth -= 1
                end += 1
            inner = expression[i+1:end-1]
            args = []
            while (comma := top_level(inner, ",")) != -1:
                args.append(translate(inner[:comma]))
                inner = inner[comma+1:]
            args.append(translate(inner))
            rebuilt.append("(" + ", ".join(args) + ")")
            i = end-1
        else:
            rebuilt.append(char)
        i += 1
    expression = "".join(rebuilt)
    question = top_level(expression, "?")
    if question != -1:
        # Helpers use right-associative ternaries; nested conditional arms are
        # parenthesized. Locate the corresponding top-level colon.
        colon = top_level(expression[question + 1:], ":") + question + 1
        if colon <= question:
            raise ValueError(expression)
        return ("(" + translate(expression[question + 1:colon]) + " if "
                + translate(expression[:question]) + " else "
                + translate(expression[colon + 1:]) + ")")
    return expression


def pine_string(value, pattern=None):
    if isinstance(value, bool):
        return str(value).lower()
    if pattern:
        return format(value, ".16f").rstrip("0").rstrip(".") or "0"
    return str(value)


class Decisions:
    def __init__(self, source, fx=1):
        self.source = source
        def dt(value):
            return datetime.fromtimestamp(value / 1000, timezone.utc)
        self.environment = {
            "na": lambda value: value is None,
            "int": int,
            "math": SimpleNamespace(floor=math.floor, ceil=math.ceil, min=min, max=max),
            "strategy": SimpleNamespace(convert_to_account=lambda value: value * fx),
            "str": SimpleNamespace(tostring=pine_string, replace_all=lambda value, old, new: value.replace(old, new)),
            "sessionTimezone": "UTC",
            "year": lambda value, zone: dt(value).year,
            "month": lambda value, zone: dt(value).month,
            "dayofmonth": lambda value, zone: dt(value).day,
            "timestamp": lambda zone, y, m, day, hour, minute: int(
                datetime(y, m, day, hour, minute, tzinfo=timezone.utc).timestamp() * 1000),
        }
        functions = re.findall(r"^(\w+)\(([^\n]*)\) =>\n((?:    [^\n]*\n?)+)", source, re.M)
        self.functions = {name: (params, body) for name, params, body in functions}
        for name in self.functions:
            self.environment[name] = lambda *args, name=name: self.call(name, *args)

    def expression(self, expression, **variables):
        # Input is repository-owned helper code. Empty builtins constrain this
        # local test interpreter; unsupported Pine constructs fail explicitly.
        return eval(translate(expression), {"__builtins__": {}}, self.environment | variables)

    def call(self, name, *args):
        params, body = self.functions[name]
        names = [param.strip().split()[-1] for param in params.split(",") if param.strip()]
        if len(names) != len(args):
            raise ValueError(name)
        variables = dict(zip(names, args))
        result = None
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            assignment = re.fullmatch(r"(?:(?:string|int|float|bool) )?(\w+) (?:=|:=) (.+)", line)
            if assignment:
                variables[assignment.group(1)] = self.expression(assignment.group(2), **variables)
            else:
                result = self.expression(line, **variables)
        return result

    def assignment(self, name, **variables):
        expression = re.search(rf"^\s*(?:float|int|bool) {name} = (.+)$", self.source, re.M).group(1)
        return self.expression(expression, **variables)


class StrategyBehaviorTests(unittest.TestCase):
    def test_script_short_titles_fit_platform_limit(self):
        for path in [*STRATEGIES, ROOT / "liquidity_structure_v1.pine"]:
            short_title = re.search(r'shorttitle = "([^"]+)"', path.read_text(encoding="utf-8")).group(1)
            self.assertLessEqual(len(short_title), 10, path.name)

    def test_midnight_including_2359_has_exactly_one_reset(self):
        for path in STRATEGIES:
            with self.subTest(source=path.name):
                source = path.read_text(encoding="utf-8")
                engine = Decisions(source)
                times = [int(datetime.fromisoformat(t).replace(tzinfo=timezone.utc).timestamp()*1000)
                         for t in ["2026-10-23T23:58", "2026-10-23T23:59", "2026-10-24T00:00", "2026-10-24T00:01"]]
                days = [engine.call("riskDayStamp", t) for t in times]
                self.assertTrue(all(day is not None for day in days))
                self.assertEqual([engine.call("dayChanged", b, a) for a, b in zip(days, days[1:])], [False, True, False])
                self.assertIn("int currentRiskDay = riskDayStamp(time)", source)
                self.assertNotIn('"0000-2359"', source)

    def test_actual_session_endpoints_exclude_partial_bars(self):
        for path in STRATEGIES:
            source = path.read_text(encoding="utf-8")
            engine = Decisions(source)
            for bar_open, bar_close, expected in [(900, 960, False), (900, 945, True), (920, 946, False), (899, 930, False)]:
                with self.subTest(source=path.name, endpoints=(bar_open, bar_close)):
                    self.assertEqual(engine.call("barWithinSession", bar_open, bar_close, 900, 945), expected)
            self.assertFalse(engine.call("barWithinSession", 900, 930, None, None))
            self.assertIn("barWithinSession(time, time_close, entrySessionOpen, entrySessionClose)", source)

    def test_partial_exit_retains_plan_and_does_not_count_another_entry(self):
        for path in STRATEGIES:
            source = path.read_text(encoding="utf-8")
            engine = Decisions(source)
            with self.subTest(source=path.name):
                self.assertFalse(engine.call("fullPositionExit", 1, 2, 1))
                self.assertTrue(engine.call("fullPositionExit", 0, 2, 1))
                self.assertTrue(engine.call("fullPositionExit", 0, 0, 1))  # round trip between evaluations
                self.assertFalse(engine.call("fullPositionExit", 0, 0, 0))
                self.assertTrue(engine.call("freshEntry", 1000, None))
                self.assertFalse(engine.call("freshEntry", 1000, 1000))  # partial exit, same entry
                self.assertTrue(engine.call("freshEntry", 2000, 1000))
                self.assertFalse(engine.call("freshEntry", None, 1000))
                self.assertIn("bool positionJustClosed = fullPositionExit(", source)
                self.assertIn("if riskDayStamp(observedEntryTime) == currentRiskDay", source)
                self.assertNotIn("strategy.opentrades + strategy.closedtrades", source)

    def test_first_bar_losses_are_measured_from_previous_valuation(self):
        for path in STRATEGIES:
            source = path.read_text(encoding="utf-8")
            engine = Decisions(source)
            with self.subTest(source=path.name):
                baseline = engine.call("dailyBaseline", True, 100000, 98000)
                self.assertEqual(98000-baseline, -2000)
                self.assertEqual(engine.call("dailyBaseline", True, None, 100000), 100000)
                self.assertIn("dailyBaseline(newRiskDay, strategy.equity[1], strategy.equity)", source)
                self.assertIn("dailyBaseline(newRiskDay, strategy.netprofit[1], strategy.netprofit)", source)

    def test_currency_conversion_is_applied_before_budget_comparison(self):
        for path in STRATEGIES:
            engine = Decisions(path.read_text(encoding="utf-8"), fx=1.2)
            symbol = SimpleNamespace(mintick=.25, pointvalue=2)
            with self.subTest(source=path.name):
                risk = engine.assignment("modeledPriceRisk", stopTicks=20, sizingBufferTicks=2, syminfo=symbol)
                self.assertAlmostEqual(risk, 13.2)
                self.assertAlmostEqual(engine.assignment("contractNotional", close=100, syminfo=symbol), 240)
                self.assertEqual(engine.call("affordableContracts", 26, risk+5), 1)

    def test_margin_reserve_and_each_quantity_cap_are_effective(self):
        for path in STRATEGIES:
            engine = Decisions(path.read_text(encoding="utf-8"))
            symbol = SimpleNamespace(mintick=.25, pointvalue=2)
            margin = engine.assignment("marginPerContract", close=100, sizingBufferTicks=2, syminfo=symbol, roundTripCommission=5)
            self.assertEqual(margin, 206)
            self.assertEqual(engine.call("affordableContracts", 205, margin), 0)
            self.assertEqual(engine.call("affordableContracts", 412, margin), 2)
            self.assertEqual(engine.call("affordableContracts", -1, margin), 0)
            self.assertEqual(engine.call("affordableContracts", 1000, None), 0)
            for i in range(5):
                caps = [10]*5
                caps[i] = 0
                self.assertEqual(engine.call("capContracts", *caps), 0)
            self.assertEqual(engine.assignment("allowedContracts", riskSizingContracts=10, dailyCapacityContracts=8,
                                             notionalBasedContracts=9, marginBasedContracts=2, maximumContracts=10), 2)

    def test_separation_is_mandatory_for_both_directions(self):
        for path in STRATEGIES:
            source = path.read_text(encoding="utf-8")
            engine = Decisions(source)
            for direction in ["long", "short"]:
                variables = dict(enableLongEntries=True, enableShortEntries=True, calculationsReady=True,
                                 emaSeparationQualified=False, longScore=12 if direction=="long" else 0,
                                 shortScore=12 if direction=="short" else 0, minimumSignalScore=7,
                                 bullishAlignment=True, bearishAlignment=True, fastEmaRising=True,
                                 fastEmaFalling=True, rsiSupportsLong=True, rsiSupportsShort=True)
                self.assertFalse(engine.assignment(direction+"TechnicalSetup", **variables))
                variables['emaSeparationQualified']=True
                self.assertTrue(engine.assignment(direction+"TechnicalSetup", **variables))


class IndicatorBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.engine = Decisions(INDICATOR)

    def test_both_side_penetration_is_independent_of_consumed_flags(self):
        self.assertTrue(self.engine.call("penetratedLevel", 94, 95, -1, 1))
        self.assertTrue(self.engine.call("penetratedLevel", 101, 100, 1, 1))
        self.assertFalse(self.engine.call("penetratedLevel", 101, None, 1, 1))
        self.assertIn("bullSweep and not piercedHigh", INDICATOR)
        self.assertIn("bearSweep and not piercedLow", INDICATOR)
        self.assertNotIn("bullSweep and not tookHigh", INDICATOR)
        long_condition = re.search(r"if (allowLong and .+)$", INDICATOR, re.M).group(1)
        for low_used, high_used in [(False, False), (False, True), (True, False)]:
            took_low = self.engine.assignment("tookLow", lowUsed=low_used, piercedLow=True)
            self.assertFalse(self.engine.expression(long_condition, allowLong=True,
                bullSweep=took_low, piercedHigh=True, swingHigh=100, close=96))

    def test_opening_bar_can_arm_after_prior_date_is_cancelled(self):
        self.assertEqual(self.engine.call("setupCancellation", True, True, False, False), "SESSION RESET")
        self.assertEqual(self.engine.call("setupCancellation", True, False, False, False), "")
        arm_line = next(line for line in INDICATOR.splitlines() if "if armedDirection == 0 and" in line)
        self.assertNotIn("newDay", arm_line)
        self.assertIn("armedDate := dateKey", INDICATOR)
        self.assertIn("dateKey != armedDate", INDICATOR)
        condition = arm_line.strip()[3:]
        self.assertTrue(self.engine.expression(condition, armedDirection=0, longSignal=False,
            shortSignal=False, ready=True, inSession=True, newDay=True))

    def test_targets_remain_favorable_for_both_directions(self):
        for direction in [-1, 1]:
            for risk, multiple, tick in [(1.25,.1,.25), (2,2,.25), (.01,.1,.01), (1.3,2,.25)]:
                with self.subTest(direction=direction, risk=risk, multiple=multiple):
                    ticks = self.engine.call("targetDistanceTicks", risk, multiple, tick)
                    distance = ticks*tick
                    self.assertGreaterEqual(ticks, 1)
                    self.assertGreaterEqual(distance+1e-12, risk*multiple)
                    self.assertGreater(direction*((100+direction*distance)-100), 0)
        self.assertIn("armedDirection * targetDistanceTicks(candidateRisk, targetR, tick) * tick", INDICATOR)

    def test_invalidation_is_monotonic_and_panel_uses_it(self):
        self.assertTrue(self.engine.call("setupInvalidated", 1, 94, 110, 95))
        self.assertFalse(self.engine.call("setupInvalidated", 1, 95, 110, 95))
        self.assertTrue(self.engine.call("setupInvalidated", -1, 90, 101, 100))
        self.assertEqual(self.engine.call("setupCancellation", True, False, True, False), "SWEEP EXTREME BROKEN")
        self.assertEqual(self.engine.call("setupCancellation", True, False, False, True), "SETUP EXPIRED")
        self.assertIn('state := displayCancellation != "" ? displayCancellation', INDICATOR)
        self.assertIn("string pendingCancellation = setupCancellation(", INDICATOR)
        self.assertIn("setupInvalidated(armedDirection, low, high, sweepExtreme), bar_index - armedBar > validityBars)", INDICATOR)

    def test_each_setup_gets_a_separate_drawing_object(self):
        self.assertIn("if armedLongNow or armedShortNow\n        armedLine := line.new(", INDICATOR)
        self.assertIn("line.set_x2(armedLine, bar_index)", INDICATOR)
        self.assertNotIn('plot(armedDirection != 0 ? breakLevel', INDICATOR)
        self.assertIn("max_lines_count = 100", INDICATOR)


class AlertIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT/"futures_v7_5.pine").read_text(encoding="utf-8")
        cls.engine = Decisions(cls.source)

    def test_instances_and_configurations_produce_distinct_event_ids(self):
        event = ("CME_MINI:MNQ1!", "1", 123456, "LONG_ENTRY")
        same = self.engine.call("eventIdentity", "account-a", "config-a", *event)
        self.assertEqual(same, self.engine.call("eventIdentity", "account-a", "config-a", *event))
        self.assertNotEqual(same, self.engine.call("eventIdentity", "account-b", "config-a", *event))
        self.assertNotEqual(same, self.engine.call("eventIdentity", "account-a", "config-b", *event))

    def test_configuration_covers_every_behavior_input(self):
        inputs = set(re.findall(r"^(?:bool|int|float|string) (\w+) = input\.", self.source, re.M))
        excluded = {"showSignalMarkers", "showRiskLevels", "showDashboard", "alertInstanceId"}
        config = self.source.split("var string configurationId = array.join(array.from(",1)[1].split('\n), "|")',1)[0]
        for name in inputs-excluded:
            self.assertRegex(config, rf"\b{name}\b")

    def test_serialized_payload_matches_the_schema_2_field_contract(self):
        schema_text = (ROOT/"ALERT_SCHEMA.md").read_text(encoding="utf-8")
        schema = json.loads(re.search(r"```json\n(.*?)\n```", schema_text, re.S).group(1))
        self.engine.environment.update({
            "syminfo": SimpleNamespace(tickerid='EX:SYMBOL', ticker='SYMBOL"\\\n', prefix='EX'),
            "timeframe": SimpleNamespace(period="1"),
            "currentRiskDay": 1792713600000, "alertInstanceId": "account-a", "configurationId": "true|9|21",
        })
        for event, action, direction, qty, stop, target, reason in [
            ("LONG_ENTRY", "ENTER", "LONG", 2, 10, 20, ""),
            ("SESSION_EXIT", "EXIT", "FLAT", 0, None, None, "SESSION_CUTOFF"),
        ]:
            with self.subTest(event=event):
                payload = json.loads(self.engine.call("alertPayload", event, action, direction, qty,
                    stop, target, 1792747800000, 1792747800000, None, reason))
                self.assertEqual(set(payload), set(schema["required"]))
                self.assertEqual(set(payload), set(schema["properties"]))
                self.assertEqual(payload["schema_version"], schema["properties"]["schema_version"]["const"])
                self.assertEqual(payload["strategy_version"], schema["properties"]["strategy_version"]["const"])
                self.assertEqual(payload["symbol"], 'SYMBOL"\\\n')
                self.assertEqual(payload["instance_id"], "account-a")
                self.assertEqual(payload["configuration_id"], "true|9|21")
                self.assertEqual(payload["planned_bracket_ticks"], {"stop": stop, "target": target})
                self.assertIsInstance(payload["risk_day_id"], int)


if __name__ == "__main__":
    unittest.main()
