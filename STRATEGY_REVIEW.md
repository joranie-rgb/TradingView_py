# Code Review of Futures Strategy V7.5

`futures_v7_5.pine` is the reviewed successor to V7.3. It uses confirmed chart
bars, same-close market-order execution, and no higher-timeframe or future-data
requests.
For installation, input behavior, formulas, troubleshooting, and a pre-use
checklist, see `USER_GUIDE.md`.

## Review scope and method

The review traced the complete source pipeline: fixed strategy properties, input
validation, indicator readiness, score construction, setup latching, every entry
gate, sizing arithmetic, order creation and replacement, daily state, session
state, drawdown state, and display output. Documentation claims were checked
against the exact comparisons and state transitions in the source.

No Pine compiler or TradingView broker emulator is available in this repository.
Consequently, syntax and platform-specific fill behavior must still be verified
in TradingView. This is static analysis, not a claim of identical live execution.

## Findings addressed in V7.5

### Verification report

The documentation and source were cross-checked input-by-input and across the
signal, sizing, daily-control, session, order-lifecycle, and display paths. This
review found and resolved the following discrepancy:

| Issue ID | Location/File | Description of Discrepancy | Severity (High/Medium/Low) |
| --- | --- | --- | --- |
| TV-001 | `futures_v7_5.pine` — session-exit cancellation and planned-order state | When a session exit canceled a pending entry while the strategy was still flat, the frozen stop ticks, target ticks, and direction were not cleared because cleanup only handled a filled position closing. The dashboard could therefore show a plan after its order no longer existed, contrary to the documented display semantics. The session cancellation path now records this lifecycle event and clears all pending-plan state before any new submission is evaluated. | Low |
| TV-002 | `futures_v7_5.pine` — non-latching daily-loss liquidation | The entry gate followed the current threshold when the rest-of-day lock was disabled, but forced liquidation followed the internal historical latch. After P&L recovered, a permitted new position was therefore closed on its next confirmed bar even though the daily limit was no longer breached. Liquidation now uses the same effective lock as entry eligibility. | Medium |
| TV-003 | `futures_v7_5.pine` — boundary and administrative-order lifecycle | Next-tick entries could fill after an approved session/date boundary, narrow exit windows could be missed by bar alignment, and administrative exits canceled protective brackets before their market close could fill. Entries now process on the confirmed signal close, session exits detect a bar spanning or following the cutoff, and administrative closes are immediate while existing brackets remain active. | High |
| TV-004 | `futures_v7_5.pine` — external event visibility | The strategy exposed no explicit machine-readable event names for an alert consumer. Entry and administrative events now emit stable `alert()` payloads, and order-generating calls provide stable `alert_message` values. Authentication, idempotency, broker reconciliation, and partial-fill management remain responsibilities of an external service. | Medium |
| TV-005 | `futures_v7_5.pine` — protective order-fill messages | Stop-loss and profit-target fills had no explicit payload, so an order-fill alert could not reliably identify the direction and protective outcome. Every bracket submission and refresh now supplies direction-specific `alert_loss` and `alert_profit` values. | Medium |
| TV-006 | `futures_v7_5.pine` — coincident administrative exits | Daily-loss, maximum-drawdown, and session controls could all submit `strategy.close_all` on the same evaluation. The strategy now selects one deterministic close reason: maximum drawdown, then daily loss, then session. Session state and flat-order cancellation are still processed when another reason has priority. | Medium |
| TV-007 | `futures_v7_5.pine` — ambiguous administrative `alert()` payload | All administrative conditions emitted the same `ADMINISTRATIVE_EXIT` event, forcing a consumer to infer the actual policy trigger. The alert now reports `MAXIMUM_DRAWDOWN_EXIT`, `DAILY_LOSS_EXIT`, or `SESSION_EXIT`, using the same priority as the close request. | Low |

#### TV-001 resolution

The concrete fix records a flat pending-entry cancellation at the point where
the session guard is evaluated, then resets the complete frozen plan after its
state variables are declared:

```pine
bool pendingEntryCancelledAtSessionExit = sessionExitRequired and cancelOrdersAtSessionExit and strategy.position_size == 0

if pendingEntryCancelledAtSessionExit
    plannedStopTicks := na
    plannedTargetTicks := na
    plannedDirection := 0
```

The later full-path alert and administrative-order review identified TV-005
through TV-007 below. Platform compilation and broker-emulator behavior remain
external validation requirements, as described under residual risks.

#### TV-005 through TV-007 resolution

The review traced each order-generating path independently. Protective fills now
identify `LONG_STOP_EXIT`, `LONG_TARGET_EXIT`, `SHORT_STOP_EXIT`, or
`SHORT_TARGET_EXIT`. Administrative controls are reduced to one prioritized
reason before any close request or `alert()` event is emitted, preventing
duplicate close requests and keeping the two alert mechanisms semantically
aligned. The session guard still marks the session processed and can cancel a
flat pending entry even when no session close request is needed.

### 1. Input safety

- Related lengths, RSI bands, contract limits, and backtest dates are checked on
  the first bar. Invalid combinations fail with a specific message.
- Contract inputs have explicit upper bounds, daily loss percentage cannot exceed
  100%, and the commission sizing estimate cannot be lower than the strategy's
  configured USD 5.00 round trip.
- Symbol metadata must expose positive `syminfo.mintick` and
  `syminfo.pointvalue`; otherwise tick conversion and futures sizing are unsafe.
- Inputs cannot prove that a timezone or session is operational for a particular
  market. Those values still require a symbol-specific chart test.

### 2. Logic decoupling and signal retention

V7.3 included market, session, and date eligibility inside its directional
setup. Consequently, a filter transition could manufacture a new setup, or a
genuine technical transition could disappear before a temporary gate opened.

V7.5 separates the pipeline into:

1. technical score and directional setup;
2. a technical transition with a configurable `Signal Validity Bars` latch;
3. indicator filters (ATR and volume);
4. execution-time gates (session and backtest range); and
5. position, cooldown, daily, drawdown, and sizing gates.

A latched signal remains valid only while its underlying directional technical
setup is still true. This avoids executing a stale signal after the premise has
failed. The default three-bar validity should be tested rather than optimized on
the full evaluation sample.

### 3. Chart validation

- Synthetic/nonstandard charts can be rejected.
- Intraday charts can be required because a daily bar cannot reliably intersect
  a narrow session-exit window.
- A maximum chart timeframe rejects bars too coarse for the intended session
  controls. This is a coarse check: users must still confirm that at least one
  bar actually opens inside the exit window.

### 4. Risk controls

- ATR stop distance is rounded outward to whole ticks. Brackets use relative
  `loss`/`profit` ticks and therefore resolve from the actual fill, not the
  previous signal close.
- Per-contract sizing includes a tick buffer and estimated round-trip commission.
- Optional daily-capacity reservation restricts planned quantity using unused
  daily-loss capacity.
- An independent notional exposure cap limits futures leverage. Unlike the
  optional minimum-size account-risk override, daily-capacity and notional hard
  caps cannot be bypassed by disabling **Skip Trade When Minimum Size Exceeds
  Risk**.
- A peak-equity drawdown lock is permanent for the strategy run and can cancel
  orders and close an open position. The daily state resets each risk day.

## Exact execution and state semantics

### Entries and brackets

- Entry conditions are evaluated on confirmed bars. With
  `process_orders_on_close = true`, submitted market orders are processed on the
  confirmed bar's closing tick, preventing boundary drift before fill.
- Entry-session and backtest-date tests require both the signal bar's opening and
  closing timestamps to satisfy their configured boundaries. Same-close
  processing keeps the emulator fill on that qualified closing tick.
- Stop and target tick counts are frozen when the entry is submitted. Plotted
  prices are populated after a new position is observed and use
  `strategy.position_avg_price`.
- The sizing buffer and commission estimate reduce quantity only. They do not
  widen the bracket, and the estimate is separate from commission charged by the
  strategy property.

### Daily controls

- A risk day is identified in the configured timezone, but reset code runs on
  the first available chart bar belonging to the new calendar day. Across a
  market closure at midnight, the baseline is the first available bar rather
  than a synthetic midnight valuation.
- Daily P&L is measured from that baseline. Realized mode uses the change in
  `strategy.netprofit`; marked-to-market mode uses the change in
  `strategy.equity`.
- Filled-trade counting uses the increase in open-plus-closed trade records, not
  submitted signals. It updates after the emulator exposes a fill.
- Crossing the daily-loss threshold records internal `dailyLossLocked` for that
  risk day. With **Lock Trading for Rest of Risk Day** enabled, entry blocking
  and forced liquidation follow that latch. With it disabled, both behaviors
  follow the current threshold and normal operation resumes after P&L recovery.
- Remaining daily-loss capacity is
  `max(daily loss allowance + monitored daily P&L, 0)`. Profits can therefore
  increase it above the original allowance.

### Session and drawdown controls

- The first confirmed bar opening in the exit window marks the session exit as
  processed even if no position exists. Entries then remain blocked until the
  next risk-day reset.
- Daily-loss and drawdown exits submit an immediate same-closing-tick `close_all`
  request while leaving protective brackets active
  until processing. A flat pending session order is canceled when configured.
  These remain emulator actions, not broker-side intrabar controls.
- If several administrative controls trigger together, one close request is
  submitted using drawdown, daily loss, then session priority. The session guard
  still performs its state transition and configured flat-order cancellation.
- Peak equity and drawdown are sampled on chart evaluations and include open P&L.
  Once reached, the drawdown lock never resets during the run, even if forced
  liquidation is disabled.

### Sizing and display

- The account-risk override is optional; daily-capacity and notional caps remain
  hard when enabled. The default 100% notional cap can reject one futures
  contract when `close × syminfo.pointvalue` exceeds strategy equity.
- `effectiveRiskBudget` is a displayed summary. Quantity is computed by
  independently flooring account-risk and daily-capacity quantities and taking
  the smallest cap, which is conservative at integer boundaries.
- Dashboard quantities describe the current bar's prospective order. Planned
  stop and target ticks show `na` while flat unless an entry is pending.

## Documentation corrections from this review

- Clarified that risk-day resets occur on the first available bar after the
  calendar changes, not at an independently evaluated midnight tick.
- Distinguished signal submission, pending market orders, observed fills, and
  filled-trade counting.
- Documented how the internal daily-loss latch controls both entries and forced
  liquidation only when the rest-of-day lock is enabled.
- Documented that session/date eligibility is evaluated on the confirmed signal
  bar and same-close processing prevents emulator boundary drift.
- Added exact RSI boundaries, signal-validity behavior without transition mode,
  default notional-cap implications, administrative-exit behavior, and dashboard
  interpretation.

## Independent second-pass review and verification

After TV-002 through TV-004 and their regression tests were applied, the entire
Pine source and all three documentation files were read again rather than
reviewing only the diff. The second pass retraced initialization, risk-day
transitions, signal retention, quantity caps, pending/filled/closed order state, every
administrative exit, dashboard cleanup, and the documented setup and operating
workflow. It found no additional high-confidence defect that can safely be
corrected without TradingView runtime evidence.

Local verification consists of `python -m unittest discover -s tests -v`,
Python bytecode compilation of the test module, whitespace/error-marker checks,
and a repository-wide scan for unfinished work, obvious credential labels,
dynamic execution, future-data requests, and immediate market-close behavior.
The Pine compile and broker-emulator scenarios remain mandatory external checks,
not local passes; the repository intentionally has no Pine toolchain, dependency
manifest, CI pipeline, deployment target, database, network service, credentials,
or environment configuration.

## Residual risks and platform limits

- Daily-loss and drawdown decisions occur at confirmed chart-bar closes. Same-
  close processing reduces the response interval but gaps, limit moves, alert
  latency, and emulator assumptions can still exceed modeled risk.
- Same-close processing prevents emulator entry fills from drifting past the
  approved signal-bar session or backtest boundary. A live alert consumer must
  independently reject stale or out-of-window messages.
- The cutoff fallback catches the first available confirmed bar that spans or
  follows the configured local cutoff when no bar intersects the narrow exit
  window. Its absolute timestamp comparison also handles bars that cross
  midnight. A market closure still delays evaluation until another chart bar exists.
- Administrative close requests are immediate on the confirmed closing tick and
  do not first cancel active protective brackets. Neither mechanism guarantees an
  attainable live price.
- The drawdown peak includes open P&L and is stricter than a closed-equity-only
  calculation, but is still sampled only when the script evaluates.
- Entry, protective-exit, and reason-specific administrative alerts use the
  published versioned JSON contract. The script still has no webhook receiver,
  broker API, partial-fill handling, authentication, or reconciliation service.
- Test point value, tick size, commission, timezone, session boundaries, and
  continuous-contract roll behavior for every futures symbol.
- TradingView's Pine editor/compiler and broker emulator are authoritative for
  syntax and execution behavior; this repository contains neither.
