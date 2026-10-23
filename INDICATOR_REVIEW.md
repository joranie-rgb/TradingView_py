# Liquidity + Structure Monitor v1.0

## Review scope, October 23, 2026

Reviewed repository main at `0976004`, including `futures_v7_4.pine` and
`futures_v7_5.pine`, and the supplied TradingView screenshot. The local checkout
was fast-forwarded from `e4c5eef` before creating this indicator.

The screenshot shows Fut V7.5.1, FutuV7.4b, Morning Thesis Monitor v1.1, and
Morning Thesis Monitor v1.2.1. Their exact sources are absent from main. V7.5 in
this repository is not proof of V7.5.1 behavior. The monitor's baseline,
checkpoint, yield comparison, and evidence persistence cannot be audited from
pixels. The new indicator does not reproduce those macro/evidence features.

## Findings that affect the design

1. The screenshot contains two chart timeframes and several script revisions.
   Signals, tables, and strategy trades can originate from different scripts.
   Version and timeframe labels should remain explicit during comparison.
2. Large evidence tables use substantial chart area and become difficult to
   read when the layout is scaled. The replacement has eight rows, selectable
   corners and text sizes, and optional pivot/reference plots.
3. The repository strategy calculates EMA/MACD/RSI scores. It has no confirmed
   swing sweep followed by a structure-break state machine, despite the chart
   layout's liquidity/structure name. Several score contributions reuse related
   EMA/MACD evidence; the score is not a calibrated probability of success.
4. The screenshot is approximately 06:20 New York time. Repository V7.5 defaults
   to 09:30-15:45 entries and a 15:50 cutoff. An overnight move need not generate
   an eligible strategy entry. This does not explain an entire empty report.
5. The report shows $50K, whereas the source declares $100K initial capital.
   With a $2 point value and price 29,143.25, notional is $58,286.50 per contract.
   At $50K equity and the default 100% notional cap, the quantity cap floors to
   zero. Verify actual Strategy Properties and symbol metadata before attributing
   the empty report to a signal bug. The source also declares 100% margin.
6. V7.5's session check tests whether session-generated opening and closing
   timestamps exist. It does not compare the actual chart close to the generated
   session close. A bar overlapping a partial session boundary can therefore
   pass that check; a cutoff may independently block it. The new indicator
   explicitly compares actual endpoints. Existing strategy files were left
   unchanged because this request creates an indicator.
7. V7.5 can emit an entry `alert()` and an order-fill alert. Selecting both event
   types requires receiver deduplication. This indicator uses two selectable
   `alertcondition()` events and has no order-fill event stream.

## New signal rules

`liquidity_structure_v1.pine` is a separate Pine v6 **indicator**. It has no
strategy orders, account sizing, fill model, P&L, or position tracking.

1. Confirm a swing using three bars on each side by default. A pivot becomes
   available after its right-hand bars close. Its line begins when known; no
   marker is shifted backward onto the pivot's original bar.
2. A bullish sweep penetrates an unused confirmed low by at least one tick and
   closes above it. A bearish sweep penetrates a confirmed high and closes below
   it. A bar penetrating both sides is ambiguous and arms neither direction.
3. Freeze the opposite swing and sweep extreme when arming. The opposite swing
   must still lie beyond the sweep candle's close. Only one direction can be
   armed. A swept pivot is consumed even if a setup cannot be armed; another
   pivot must confirm before that side can arm again.
4. On a **later** bar, require a close at least one tick beyond the frozen
   structure level. Confirm trend/body/extension/volume/cooldown/reference-risk
   gates on that same closing bar. If a gate blocks confirmation, the setup
   remains eligible within its lifetime and needs a qualifying later close
   beyond the level; an additional crossover is not required.
5. Cancel before signaling if price breaks the original sweep extreme, the setup
   exceeds 12 bars, the bar is outside the session, or the local calendar date
   changes. A touch equal to the sweep extreme does not cancel. A bar that both
   invalidates the extreme and breaks structure cannot confirm that old setup.
6. Default trend context is the **previous completed 4h candle** and its 9/21
   EMAs. Bullish means close > fast > slow; bearish means close < fast < slow.
   Mixed context blocks confirmation when enabled. Chart EMAs must also align.
   HTF values use the documented `[1]` plus `barmerge.lookahead_on` pattern.
7. The signal candle must have the correct body direction, body >= 0.25 ATR,
   and close within 2 ATR of the fast EMA. Volume filtering is optional and off
   by default. Missing volume blocks signals only if that filter is enabled.
8. Reference stop is two ticks beyond the original sweep extreme, with a
   permitted distance of 0.5-3 ATR from the signal close. Target is 2R, rounded to
   the symbol's tick size. These are frozen **reference prices**, not orders.

The setup's age is measured in chart bars. Twelve 1m bars and twelve 1h bars
represent different opportunities. A 1h chart computes its own 1h structure;
it does not reconstruct all 1m signals. Keeping the same 4h context on both
charts makes trend context comparable, but signal timing will differ.

## Install and compare

1. Copy the complete new Pine file into a new TradingView Pine Editor indicator,
   save it, and select **Add to chart**. Compilation in TradingView is required.
2. For comparison, hide other versions temporarily so each signal is attributable.
   Keep the original strategies saved. The indicator does not populate Strategy
   Tester and does not connect to the visible order ticket.
3. Start on standard time-based MNQ candles. Defaults use the weekday New York
   session 09:30-16:00. To study the screenshot's early morning period, change
   the session to your chosen hours or disable session filtering. The disabled
   setting means all hours actually present in the chart dataset.
4. Use the same 4h context input on the 1m and 1h charts. Selecting a context
   timeframe equal to or below the chart raises an error while HTF filtering is
   enabled. Context filtering can be disabled without requesting HTF data.
5. Select the indicator's long or short alert condition, with **Once Per Bar
   Close**. Both conditions already require a confirmed signal bar. Messages
   include symbol, timeframe, close, reference stop, and reference target.
   Recreate alerts after changing source or inputs; TradingView alerts retain a
   snapshot. Sweep dots are setup markers, not signal alerts.

The panel's main state describes the current bar and its first relevant blocker.
Its last-event row retains the latest sweep, cancellation, or signal; the last
reference row retains the latest confirmed signal prices. These can refer to
different events. Reference lines start on the next bar, expire after the
configured display age, and have a gap between plans. They do not disappear on
target/stop touches, track exits, or prevent later signals. No account position
is inferred. Reloads and input changes rebuild chart history; it is not an
external archive.

Only wholly contained session bars qualify. On 1h charts, bars straddling a
09:30 or 16:00 boundary can be excluded according to chart alignment. Overnight
sessions are supported for membership but pending setups intentionally reset at
local midnight, including when session filtering is disabled. Session day digits
follow TradingView's 1=Sunday through 7=Saturday syntax.

## Verification and remaining validation

No local Pine compiler is provided by this repository. Local source inspection
and existing strategy contract tests cannot establish that the new indicator
compiles or performs correctly in TradingView. No profit, win-rate, or improved
return claim has been established. No settings were optimized against the image.

Local verification completed: all 20 existing strategy contract checks passed
using `python -m unittest discover -s tests -v` with the bundled Python runtime;
`git diff --check` passed. These tests cover the unchanged V7.5 strategy, not the
new indicator's signal engine. TradingView compilation and the Replay scenarios
below remain outstanding.

Before relying on the indicator, compile it and use Bar Replay to check:

| Scenario | Expected result |
| --- | --- |
| Pivot right-hand bars incomplete | No eligible new pivot or backdated sweep marker. |
| Wick through low and close above; opposite high still above close | Long setup armed; no same-bar signal. |
| Sweep candle already closes through opposite structure | No setup armed from that sweep. |
| One candle penetrates both pivots | Neither direction arms. |
| Later close breaks frozen structure with all gates met | One closing-bar L/S marker; arm consumed. |
| Break occurs with mixed/opposing HTF trend | No signal; HTF blocker displayed if higher-priority gates pass. |
| Gate later passes before expiry and close remains beyond break level | Signal can confirm without a second crossover. |
| Invalidating extreme and structure break in the same bar | Invalidation wins; old setup emits no signal. |
| Age exactly 12 / age 13 | Eligible / expired with default lifetime. |
| Signal at bar N, cooldown=5 | Earliest later signal is N+6. |
| Signal just before session end; next bar straddles end | No outside-session confirmation. |
| Date rolls over without outside-session bars in dataset | Pending setup clears. |
| Reuse already swept pivot | No repeated arm until another pivot confirms. |
| Missing volume with filter off / on | Ignore volume / block confirmation. |
| Stop outside min/max ATR distance | Block confirmation and display reason. |
| Toggle panel, pivot, EMA and reference visibility | Visual settings do not alter signal history. |
| Reload after realtime bars become historical | Closed-bar markers should agree, barring feed/history revisions. |
| Compare 1m and 1h charts | Same completed 4h context; separate chart structure and signals. |

Official references:
- [Confirmed higher-timeframe data](https://www.tradingview.com/pine-script-docs/faq/other-data-and-timeframes/)
- [Bar confirmation and realtime state](https://www.tradingview.com/pine-script-docs/concepts/bar-states/)
- [Time-based sessions and generated endpoints](https://www.tradingview.com/pine-script-docs/concepts/sessions/)
- [Alert snapshots and indicator conditions](https://www.tradingview.com/pine-script-docs/concepts/alerts/)
