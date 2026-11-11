# Lifecycle hardening and verification

This work follows the approved October 29 hardening specification. Hosted smoke
tests are recorded below; no improved trading performance is claimed.

## Calendar policy

All scripts attribute a candle to its opening calendar date in the configured
timezone. A candle containing prices from two dates cannot submit a new strategy
entry or arm/confirm an indicator setup. The indicator cancels an existing arm
on that candle and displays DATE BOUNDARY BAR. Existing strategy positions retain
their protective and administrative exit logic; date boundaries do not cancel
those protections.

For classification, subtract one millisecond from the closing timestamp. A bar
ending exactly at midnight belongs wholly to the preceding interval. This avoids
excluding a normal last candle merely because its endpoint is midnight.

Daily-loss baselines continue to use the previous available valuation. They
include first-bar losses and closure gaps, but are not independently sampled
midnight account balances. The November 11 hosted forced-order fixture reconciles closing-tick fills and
commissions for one long, partial-exit and re-entry sequence. This is bounded
emulator evidence, not an independently sampled midnight broker balance.

## Validation and contracts

- Indicator session days must be unique digits from 1 through 7, at most seven
  characters. Invalid timezone strings still fail in Pine's timestamp/session
  functions; no fallback timezone is substituted.
- Strategy Alert Instance ID is nonblank, at most 64 characters, and uses ASCII
  letters, digits, underscore, or hyphen. Control characters and identity
  separators are rejected before alerts can be produced. Existing operators
  using spaces or punctuation must choose a valid deployment label.
- Schema 2 event IDs remain opaque. Identical intent/fill payloads preserve their
  ID; account or canonical configuration changes distinguish events. Freshness
  is measured from submission while signal time preserves the original setup.
- The repository has no broker receiver. Local payload tests establish
  serialization and timestamp contracts, not durable deduplication, rejection of
  expired entries, network delivery, authentication, or broker reconciliation.

## Local evidence

Run `python -B -m unittest discover -s tests -v` and `git diff --check`.
The current suite has 55 passing tests. New coverage includes New York midnight,
spring and fall daylight-saving changes, repeated local hours, partial/full exit
sequences, missing currency conversion, reset baselines, date-spanning candles,
payload identity and expiration, and explicit evaluator failures.

Calendar tests require IANA timezone data. Linux CI uses the system database;
Windows Python needs an available timezone database such as the `tzdata` package.
The bundled local runtime supplies it. Unknown zones raise an error; UTC is not
silently substituted.

The bounded test evaluator executes selected source expressions and straight-line
serialization helpers. It is not Pine, a full script interpreter, a security
sandbox, an order simulator, or a historical/live equivalence proof.

## Acceptance scope after November 11

Hosted historical lifecycle assertions and forced-order accounting reconciliation
are recorded in [the hosted test report](tests/hosted/RESULTS_2026-11-11.md).
The run found and corrected hourly session alignment in all three scripts.
Local checks, hosted source compilation and the final repository audit are
complete for this patch. Script versions remain unreleased; this PR is not a
published script release.

External receiver testing is **UNVERIFIED**. No receiver implementation or broker
integration exists in this repository. Durable deduplication, expired-alert
rejection, authentication, delivery retries and broker fill reconciliation were
not tested. Per the user's November 11 scope instruction, this does not block
repository completion. Live alert delivery, Bar Replay playback, exhaustive
short-side/FX/margin liquidation cases, and statistical improvement are also
not established by these historical fixtures.

On October 30, the browser confirmed Logged in as joranie. The exact indicator
and both strategy sources from commit 2c11b54 were pasted into Pine Editor and
accepted onto the chart with their expected script titles and no compiler
diagnostics displayed. The indicator rendered EMAs, sweep markers and its panel
on AAPL five-minute candles. The compatibility strategy completed evaluation on
CME_MINI:MNQ1! five-minute candles, September 6 through October 30, 2026: 103
trades, net P&L -439.50 USD, maximum drawdown 1,452.50 USD, profit factor 0.942.
This is one default-settings smoke test, not a holdout or performance improvement.

The October 30 structured-alert strategy attempt remained inconclusive: its
report displayed Updating report and its invalid-ID result did not resolve.

On November 6, the old validation tab no longer existed. A fresh authenticated
tab loaded the user's existing MNQ layout. The exact futures_v7_5.pine source
from merged commit 9fe8eeb was temporarily added to Chart #1 (MNQ, one-minute
hollow candles, back adjustment enabled). TradingView displayed The report has
been updated successfully, rendered the strategy's current EMA outputs, and
completed the October 25 through November 6, 2026 report with USD 100,000 initial
capital, USD 2.50 commission per contract per fill and one tick slippage:

| Metric | Hosted result |
| --- | ---: |
| Closed trades | 30 |
| Net P&L | -578.00 USD |
| Maximum drawdown | 1,145.50 USD |
| Profitable trades | 9 / 30 (30%) |
| Profit factor | 0.744 |
| Expectancy | -19.27 USD |

Changing Alert Instance ID to bad:id then produced the expected hosted error:
Error on bar 0: Alert Instance ID accepts only letters, digits, underscore, and
hyphen. The ID was restored to research-1; execution recovered and reproduced
the same completed report. The temporary validation instance was removed, and
the layout's pre-existing strategy report returned. No test alert was created.

This verifies successful execution, rejection of a malformed identity, and
recovery after correction. It does not prove all lifecycle cases, alert delivery,
external receiver behavior, statistical improvement, or production readiness.

These are unreleased changes to the existing versioned files. Before a release,
bump the script versions after any remaining hosted corrections. On November 6,
the Word guide was synchronized with session-day validation, calendar-boundary
exclusion, the DATE BOUNDARY BAR display state, and the hosted smoke-test status.
All seven pages were rendered through LibreOffice and inspected for wrapping,
clipping, table layout, page breaks, and readable footers.

No signal-performance optimization or improved win-rate claim has been made.
Any later filter optimization requires a frozen baseline, chronological holdout,
cost assumptions, sample counts, expectancy, drawdown, and uncertainty estimates.
