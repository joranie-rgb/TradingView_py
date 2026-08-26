"""Static contract tests for safety-critical Pine source invariants.

TradingView does not distribute a local Pine compiler.  These tests do not
pretend to compile or simulate Pine; they protect reviewable configuration and
state-machine decisions that could otherwise regress unnoticed.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "futures_v7_4.pine").read_text(encoding="utf-8")


class StrategyContractTests(unittest.TestCase):
    def test_execution_model_is_conservative(self) -> None:
        for setting in (
            "pyramiding = 0",
            "calc_on_order_fills = false",
            "calc_on_every_tick = false",
            "process_orders_on_close = true",
            "use_bar_magnifier = false",
        ):
            self.assertIn(setting, SOURCE)

    def test_daily_exit_uses_effective_not_historical_lock(self) -> None:
        assignment = re.search(
            r"bool dailyLossExitRequired = (?P<expression>[^\n]+)", SOURCE
        )
        self.assertIsNotNone(assignment)
        expression = assignment.group("expression")
        self.assertIn("dailyLossEntryLock", expression)
        self.assertNotIn("dailyLossLocked", expression)

    def test_hard_caps_participate_in_final_quantity(self) -> None:
        self.assertRegex(
            SOURCE,
            r"int allowedContracts = math\.min\(math\.min\(math\.min\("
            r"riskSizingContracts, dailyCapacityContracts\), "
            r"notionalBasedContracts\), maximumContracts\)",
        )

    def test_brackets_are_fill_relative_tick_distances(self) -> None:
        exits = re.findall(r'strategy\.exit\("(?:Long|Short) Exit"[^\n]+', SOURCE)
        self.assertGreaterEqual(len(exits), 4)
        for exit_call in exits:
            self.assertIn("loss = plannedStopTicks", exit_call)
            self.assertIn("profit = plannedTargetTicks", exit_call)

    def test_session_exit_has_bar_alignment_fallback(self) -> None:
        self.assertIn("useSessionExitCutoffFallback and barReachesSessionExitCutoff", SOURCE)
        self.assertIn("int sessionExitCutoffTimestamp = timestamp(sessionTimezone", SOURCE)
        self.assertIn("time_close >= sessionExitCutoffTimestamp", SOURCE)
        self.assertNotIn("localBarCloseMinute", SOURCE)

    def test_entry_boundaries_include_the_closing_tick(self) -> None:
        self.assertIn(
            "time >= backtestStartTime and time_close <= backtestEndTime", SOURCE
        )
        self.assertIn(
            "not na(time_close(timeframe.period, entrySession, sessionTimezone))",
            SOURCE,
        )
        self.assertIn(
            "insideEntrySession = barOpensInsideEntrySession and "
            "barClosesInsideEntrySession",
            SOURCE,
        )

    def test_administrative_closes_are_immediate_and_do_not_cancel_brackets(self) -> None:
        section = SOURCE[
            SOURCE.index("int administrativeExitReason") : SOURCE.index(
                "bool entryWindowOpen"
            )
        ]
        self.assertEqual(section.count("immediately = true"), 3)
        self.assertNotRegex(section, r"if (?:dailyLoss|maximumDrawdown)ExitRequired\n\s+strategy\.cancel_all")

    def test_strategy_exposes_alert_events(self) -> None:
        self.assertEqual(SOURCE.count("alert.freq_once_per_bar_close"), 5)
        for event in (
            "LONG_ENTRY",
            "SHORT_ENTRY",
            "DAILY_LOSS_EXIT",
            "MAXIMUM_DRAWDOWN_EXIT",
            "SESSION_EXIT",
        ):
            self.assertIn(f'alert("{event}"', SOURCE)
        for fill_event in (
            "LONG_ENTRY",
            "SHORT_ENTRY",
            "DAILY_LOSS_EXIT",
            "MAXIMUM_DRAWDOWN_EXIT",
            "SESSION_EXIT",
        ):
            self.assertIn(f'alert_message = "{fill_event}"', SOURCE)

    def test_protective_fills_expose_direction_and_outcome(self) -> None:
        exits = re.findall(r'strategy\.exit\("(?:Long|Short) Exit"[^\n]+', SOURCE)
        self.assertGreaterEqual(len(exits), 4)
        for direction in ("LONG", "SHORT"):
            direction_exits = [call for call in exits if f'"{direction.title()} Exit"' in call]
            self.assertGreaterEqual(len(direction_exits), 2)
            for exit_call in direction_exits:
                self.assertIn(f'alert_profit = "{direction}_TARGET_EXIT"', exit_call)
                self.assertIn(f'alert_loss = "{direction}_STOP_EXIT"', exit_call)

    def test_coincident_administrative_exits_submit_one_close(self) -> None:
        self.assertIn(
            "int administrativeExitReason = maximumDrawdownExitRequired ? 1 : "
            "dailyLossExitRequired ? 2 : sessionExitRequired ? 3 : 0",
            SOURCE,
        )
        self.assertNotIn("if dailyLossExitRequired\n", SOURCE)
        self.assertNotIn("if maximumDrawdownExitRequired\n", SOURCE)
        self.assertIn("strategy.position_size != 0 and administrativeExitReason == 3", SOURCE)

    def test_workflow_specific_inputs_follow_their_controlling_toggle(self) -> None:
        dependencies = {
            "Volume Average Length": "useVolumeFilter",
            "Signal Validity Bars": "requireNewSetup",
            "Maximum Notional Exposure (% of Equity)": "useNotionalExposureLimit",
            "Maximum Filled Trades per Day": "useDailyTradeLimit",
            "Daily Loss Limit Mode": "useDailyLossLimit",
            "Entry Session": "useEntrySession",
            "Session Exit Trigger Window": "useSessionExit",
            "Backtest Start": "useBacktestDateFilter",
        }
        for label, controller in dependencies.items():
            label_position = SOURCE.index(f'"{label}"')
            declaration = SOURCE[label_position : label_position + 500]
            self.assertIn(f"active = {controller}", declaration)

    def test_loss_mode_exposes_only_the_selected_value(self) -> None:
        self.assertIn(
            '"Maximum Daily Loss (%)", minval = 0.01, maxval = 100, '
            'step = 0.05, group = GROUP_DAILY, active = useDailyLossLimit and '
            'dailyLossMode == "Percent"',
            SOURCE,
        )
        self.assertIn(
            '"Maximum Daily Loss (Cash)", minval = 1, step = 50, '
            'group = GROUP_DAILY, active = useDailyLossLimit and dailyLossMode == "Cash"',
            SOURCE,
        )

    def test_disabled_direction_cannot_veto_active_workflow(self) -> None:
        self.assertIn("enableLongEntries and calculationsReady", SOURCE)
        self.assertIn("(not enableShortEntries or longScore > shortScore)", SOURCE)
        self.assertIn("enableShortEntries and calculationsReady", SOURCE)
        self.assertIn("(not enableLongEntries or shortScore > longScore)", SOURCE)

    def test_dashboard_reports_disabled_and_direction_specific_states(self) -> None:
        for label in (
            '"Trade workflow"',
            '"ENTRIES DISABLED"',
            '"Daily trade limit"',
            '"Active scores"',
            '"Active signal age"',
            '"Daily loss capacity"',
            '"Drawdown lock"',
        ):
            self.assertIn(label, SOURCE)


if __name__ == "__main__":
    unittest.main()
