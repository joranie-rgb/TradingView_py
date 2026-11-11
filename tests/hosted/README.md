# Hosted Pine lifecycle checks

Run `python -B tests/hosted/build_fixtures.py` from the repository. The builder
copies the indicator state machine and the strategy's observation/reset/counting
block directly from production, records SHA256 digests (UTF-8, LF-normalized),
and fails if expected source anchors disappear. Checked-in generated files are
verified by the local test suite. Regenerate after changing production sources.

In TradingView Pine Editor, paste each generated `.pine` file into an isolated
untitled draft. Use CME_MINI:MNQ1!, standard one-minute candles, Electronic
Trading Hours and back adjustment enabled. Add the fixture to the chart, wait
for evaluation, then inspect its table and any runtime error. Remove temporary
instances afterward. Do not create alerts, connect a broker, or use these test
fixtures for trading.

- `indicator_lifecycle.pine` instruments the full indicator. Check one minute
  and one hour. PASS requires at least one arm, signal and cancellation; no
  runtime error alone is insufficient. Native first-bar checks cover equal
  touches, breaches, cancellation priority, expiry, calendar/DST classification
  and session-end calculation. Historical assertions check event ordering,
  session/date exclusion, frozen levels, separate drawing IDs and target ticks.
- `accounting_reconciliation.pine` forces 3-contract entry, 1-contract partial
  close, remainder close, 2-contract re-entry and full close across midnight.
  The default anchor is November 10, 2026, 23:57 America/New_York. Load history
  containing it; choose another anchor at 23:57 on a traded date if unavailable,
  and record that change. Initial capital is $500,000 to afford three MNQ
  contracts at 100% margin. The strategy uses $2.50 per contract per fill,
  one tick slippage, same-close processing and no recalculation on fills.
  PASS requires two observed entries, one partial, two full exits, three closed
  records and gross less all commissions equal to emulator net within one cent.
  It also checks partial/full cooldown and previous-valuation midnight reset.

The accounting fixture copies production observation logic, but deliberately
replaces signal selection and brackets with controlled test orders. Its `plan`
sentinel tests lifecycle handling; it is not a test of every production bracket
or liquidation path. First-bar helper cases are synthetic Pine assertions;
observed chart transitions and emulator orders are historical hosted execution.
Neither fixture is Bar Replay playback, live forward testing or external
receiver validation. See [recorded results](RESULTS_2026-11-11.md).
