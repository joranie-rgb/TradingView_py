"""Verify the narrow test evaluator fails explicitly instead of approximating."""
import unittest
from zoneinfo import ZoneInfoNotFoundError
from test_review_regressions import Decisions, translate, STRATEGIES


class EvaluatorContract(unittest.TestCase):
    def test_pine_string_escapes_do_not_use_python_carriage_return_semantics(self):
        engine = Decisions('')
        self.assertEqual(engine.expression(r'"\r"'), 'r')
        self.assertEqual(engine.expression(r'"\n\t"'), '\n\t')
        self.assertEqual(engine.expression(r'"\\r"'), '\\r')
        self.assertEqual(engine.expression(r'"\\x0D"'), r'\x0D')

    def test_regex_support_is_limited_to_the_production_control_character(self):
        engine = Decisions('')
        self.assertEqual(engine.expression(r'str.match(value, "\\x0D")', value='r\rr'), '\r')
        self.assertEqual(engine.expression(r'str.match(value, "\\x0D")', value='research'), '')
        with self.assertRaisesRegex(ValueError, 'Unsupported Pine regex'):
            engine.expression('str.match("r", ".*")')

    def test_unclosed_group_has_explicit_diagnostic(self):
        with self.assertRaisesRegex(ValueError, 'Unclosed parenthesis'):
            translate('math.max(1, 2')

    def test_missing_conditional_arm_fails(self):
        with self.assertRaises(ValueError):
            translate('ready ? 1')

    def test_quoted_punctuation_is_not_treated_as_syntax(self):
        engine=Decisions('')
        self.assertEqual(engine.expression('"a?b:c,(d)"'), 'a?b:c,(d)')
        self.assertEqual(engine.expression('ok ? "yes:1" : "no,2"', ok=True), 'yes:1')

    def test_unknown_timezone_does_not_silently_fall_back_to_utc(self):
        engine=Decisions(STRATEGIES[0].read_text(encoding='utf-8'))
        engine.environment['sessionTimezone']='Invalid/Unrecognized_Zone'
        with self.assertRaises(ZoneInfoNotFoundError):
            engine.call('riskDayStamp', 0)
