# Code Review of Futures Strategy V7.4

`futures_v7_4.pine` is the reviewed successor to V7.3. It uses confirmed chart
bars, next-tick order execution, and no higher-timeframe or future-data requests.
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

## Findings addressed in V7.4

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

V7.4 separates the pipeline into:

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
  `process_orders_on_close = false`, a submitted market order normally becomes
  eligible on the next available tick.
- Entry-session and backtest-date tests use the **signal bar's opening time**.
  They do not constrain the eventual fill. A pending order is not canceled merely
  because the next bar is outside either window.
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
- Crossing the daily-loss threshold always latches internal `dailyLossLocked`
  for that risk day. Turning off **Lock Trading for Rest of Risk Day** allows
  entries after monitored P&L recovers, but enabled forced liquidation continues
  to request an exit for any position while the internal latch remains set.
- Remaining daily-loss capacity is
  `max(daily loss allowance + monitored daily P&L, 0)`. Profits can therefore
  increase it above the original allowance.

### Session and drawdown controls

- The first confirmed bar opening in the exit window marks the session exit as
  processed even if no position exists. Entries then remain blocked until the
  next risk-day reset.
- Daily-loss and drawdown exits cancel protective orders before submitting a
  next-tick `close_all` market request. A session exit does so only when its
  cancellation option is enabled. These are not broker-side intrabar controls.
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
- Documented the persistent internal daily-loss latch and the narrower effect of
  disabling its entry lock.
- Documented that session/date eligibility applies to submission, not fill, and
  that the date filter does not cancel a pending order.
- Added exact RSI boundaries, signal-validity behavior without transition mode,
  default notional-cap implications, administrative-exit behavior, and dashboard
  interpretation.

## Residual risks and platform limits

- Daily-loss and drawdown decisions occur at confirmed chart-bar closes. Gaps,
  limit moves, latency, and emulator assumptions can exceed modeled risk.
- A market order placed on the last eligible bar can fill outside the entry
  session or backtest date range.
- Session exit detection requires a chart bar whose opening time lies in the
  configured window. Use a sufficiently small timeframe and schedule the window
  before the required flat time.
- Canceling protective orders and requesting an administrative market close does
  not guarantee its price or make the interval before its fill risk-free.
- The drawdown peak includes open P&L and is stricter than a closed-equity-only
  calculation, but is still sampled only when the script evaluates.
- Market orders, brackets, `strategy.cancel_all`, and `strategy.close_all` are
  broker-emulator abstractions. The script defines no `alertcondition`, webhook,
  broker API, partial-fill handling, or order-reconciliation layer.
- Test point value, tick size, commission, timezone, session boundaries, and
  continuous-contract roll behavior for every futures symbol.
- TradingView's Pine editor/compiler and broker emulator are authoritative for
  syntax and execution behavior; this repository contains neither.
