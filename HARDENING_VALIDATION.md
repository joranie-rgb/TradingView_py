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
The current suite has 62 passing tests. New coverage includes New York midnight,
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

## Acceptance scope after November 15

Hosted historical lifecycle assertions and forced-order accounting reconciliation
are recorded in [the hosted test report](tests/hosted/RESULTS_2026-11-11.md).
The run found and corrected hourly session alignment in all three scripts.
The [November 15 guard-test report](tests/hosted/RESULTS_2026-11-15.md) records
hosted compilation of the updated accounting fixture, rejection of five-minute
MNQ, one-minute Heikin Ashi MNQ and one-minute NQ on bar zero, and recovery on
standard one-minute MNQ. The valid and recovered runs reconciled USD 28.00 gross
less USD 25.00 commission to USD 3.00 emulator net across three closed records.
Screenshots and a portable source digest accompany the report. Currency, point
value and tick-size guards retain independent local coverage; those metadata
fields were not individually falsified in the hosted run.

Local checks, hosted source compilation and the final repository audit are
complete for the behavior patch. The [release candidate](RELEASE_NOTES.md)
renames those validated sources to V7.5.3, V7.4.2 and LSM v1.1.1. The renamed sources completed [final hosted compilation and message checks](tests/hosted/RELEASE_CHECKS_2026-11-15.md).
Those checks found an alert identity corruption defect in V7.5.3; the correction
and successful native-helper/full-strategy reruns are documented there. Historical reports retain their tested versions and
source digests. No GitHub Release or TradingView publication has been made.

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

The fixes are packaged in the patch versions listed in RELEASE_NOTES.md.
On November 6,
the Word guide was synchronized with session-day validation, calendar-boundary
exclusion, the DATE BOUNDARY BAR display state, and the hosted smoke-test status.
All seven pages were rendered through LibreOffice and inspected for wrapping,
clipping, table layout, page breaks, and readable footers.

No signal-performance optimization or improved win-rate claim has been made.
Any later filter optimization requires a frozen baseline, chronological holdout,
cost assumptions, sample counts, expectancy, drawdown, and uncertainty estimates.

## Released layout and manual alerts

On November 15, 2026, both old V7.4b chart instances were removed, while the
released strategies, both LSM instances and both Morning Thesis monitors were
retained. The layout was saved. All four replacement manual-review alerts were
Active, and their saved versions, intervals, messages, triggers, expiration and
notification channels were inspected individually. Webhooks were disabled.
See the [deployment and alert verification record](tests/hosted/DEPLOYMENT_ALERTS_2026-11-15.md)
for exact settings and screenshots. This later deployment created real manual
notification alerts; the earlier compilation reports describe canceled drafts.
Live delivery and external receiver testing remain **UNVERIFIED**.

Live delivery observations are tracked separately in the
[live-delivery ledger](tests/hosted/LIVE_DELIVERY_2026-11-15.md). Active saved
configuration and historical alert logs are not evidence of current delivery.

On November 15, the live observation window captured V7.5.3 SESSION_EXIT at
18:01 and V7.4.2 SESSION_EXIT at 18:05 New York time. Both log entries and
browser toasts were observed; the user confirmed mobile push and sound for
each. V7.5.3 JSON parsed with correct versions and preserved identity. These
are administrative events only: entry/fill delivery and both LSM directions
remain unverified. See the ledger for screenshots, payload and pending cases.

A subsequent November 15 check at 18:25 New York time found all four alerts
Active, no log filters selected, and no newer LSM or strategy entry/fill events.
The [live-delivery ledger](tests/hosted/LIVE_DELIVERY_2026-11-15.md) preserves
follow-up log/status screenshots; pending delivery scopes are unchanged.

The [November 16 regular-session check](tests/hosted/LIVE_DELIVERY_2026-11-16.md)
found zero Active alerts and only two older inactive alerts in the current
account view, with no filters selected. No new LSM or entry/fill delivery was
observed. Current replacement-alert availability is unresolved; November 15
evidence remains historical and must not be presented as current Active status.

The [November 16 reconciliation](tests/hosted/ALERT_RECONCILIATION_2026-11-16.md)
recovered all four original Active alerts after browser reload without recreation.
It records regular-session short entry/exit logs, native fill-message expansion,
a live V7.4.2 toast and broad user confirmation of strategy push/sound receipt.
LSM delivery, per-event device receipt and exhaustive order paths remain pending
or unverified; the report includes a brief V7.5.3 pause/restart coverage gap.

The [11:13 LSM SHORT event](tests/hosted/LSM_SHORT_DELIVERY_2026-11-16.md) has
resolved log-message values and event-specific user confirmation of mobile push
and sound. Browser-toast delivery for this event remains unverified; LSM LONG
remains pending. A newer V7.4.2 trigger timestamp was visible, but its event type
and payload were unavailable in the current log view.

The [11:35 V7.4.2 LONG_ENTRY report](tests/hosted/LONG_ENTRY_DELIVERY_2026-11-16.md)
adds intent/fill log messages, expanded fill placeholders, a directly observed
notification card and event-specific user confirmation of push/sound. LSM LONG,
V7.5.3 long examples, long exits and exhaustive paths remain pending/unverified.

The [November 17 live check](tests/hosted/LIVE_DELIVERY_2026-11-17.md) records
new dated short entry/stop/target messages, a retrospective target-fill card,
and a newly inspected November 16 V7.4.2 long-stop fill. The user broadly
confirmed push/sound in response to the grouped event question; individual
receipts, devices and latency remain unverified. LSM LONG remains pending.

The same report's November 17 approximately 13:27 follow-up adds V7.4.2
11:35 short-entry intent/expanded fill and 12:17:53 expanded stop-exit log
evidence. All four alerts were Active; LSM LONG still had no trigger and
V7.5.3/LSM SHORT latest-trigger values were unchanged. Push, sound and browser
toast for these new events remain unverified: the earlier grouped confirmation
does not cover them. Per-event receipt/latency, V7.5.3 long-side examples,
exhaustive paths and external receiver/broker reconciliation remain unverified.
Earlier pending statements above retain their historical observation scope.
