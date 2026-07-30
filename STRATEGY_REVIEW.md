# Review of Futures Strategy V7.4

`futures_v7_4.pine` is the reviewed successor to V7.3. It retains confirmed-bar,
next-tick order execution and does not request higher-timeframe or future data.
For installation, input-by-input behavior, formulas, troubleshooting, and a
pre-use checklist, see `USER_GUIDE.md`.

## Review findings addressed

### 1. Input safety

- Related lengths, RSI bands, contract limits, and backtest dates are checked on
  the first bar. Invalid combinations fail with a specific message.
- Contract inputs have explicit upper bounds, daily loss percentage cannot exceed
  100%, and the commission sizing estimate cannot be lower than the strategy's
  configured $5.00 round trip.
- Symbol metadata must expose positive `syminfo.mintick` and
  `syminfo.pointvalue`; otherwise tick conversion and futures sizing are unsafe.
- Inputs cannot prove that an IANA timezone or session window is operational for
  a particular market. Those values still require a symbol-specific chart test.

### 2. Logic decoupling and signal retention

V7.3 included market, session, and date eligibility inside `longSetup` and
`shortSetup`. Consequently, a filter transition could manufacture a new setup,
or a genuine technical transition could disappear before a temporary gate
opened.

V7.4 separates the pipeline into:

1. technical score and directional setup;
2. a technical transition with a configurable `Signal Validity Bars` latch;
3. indicator filters (ATR and volume);
4. execution-time gates (session and backtest range); and
5. position, cooldown, daily, drawdown, and sizing gates.

A latched signal remains valid only while its underlying directional technical
setup is still true. This avoids executing a stale signal after the market has
reversed. The default three-bar validity is deliberately short and should be
tested rather than optimized on the full backtest sample.

### 3. Chart validation

- Synthetic/nonstandard charts can be rejected.
- Intraday charts can be required because a daily bar cannot reliably intersect
  a narrow session-exit window.
- A maximum chart timeframe rejects bars too coarse for the configured session
  controls. This is a coarse safety check: users must still ensure that at least
  one bar actually opens inside the exit window.

### 4. Enhanced risk controls

- ATR stop distance is rounded outward to whole ticks. Brackets use relative
  `loss`/`profit` ticks and therefore resolve from the actual fill, not the
  previous signal close.
- Per-contract sizing includes a tick buffer and estimated round-trip commission.
- Optional daily-capacity reservation restricts new planned risk to the smaller
  of normal trade risk and unused daily-loss capacity. This is a hard cap when
  enabled.
- An independent notional exposure cap limits futures leverage. Unlike the
  optional minimum-size account-risk override, the daily-capacity and notional
  hard caps cannot be bypassed by disabling
  `Skip Trade When Minimum Size Exceeds Risk`.
- A peak-equity drawdown lock is permanent for the strategy run and can cancel
  orders and close an open position. The daily loss lock still resets each risk
  day.

## Important limits

- All daily-loss and drawdown decisions occur at confirmed chart-bar closes;
  they are not intrabar broker-side controls.
- Gaps, limit moves, partial fills, and live latency can exceed modeled risk.
- A market order placed on the last eligible bar normally fills on the next
  available tick, which can be outside the configured entry session.
- The drawdown peak uses strategy equity, including open P&L. This is intentionally
  stricter than a closed-equity-only calculation.
- Session exit detection still requires a chart bar whose opening time lies in
  the configured window. Use a sufficiently small timeframe and schedule the
  window before the required flat time.
- Test `syminfo.pointvalue`, tick size, commission, timezone, session boundaries,
  and continuous-contract roll behavior for every traded futures symbol.
- TradingView's Pine editor/compiler is the authoritative syntax and execution
  check; this repository does not include a Pine compiler.
