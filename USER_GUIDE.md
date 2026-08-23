# Futures V7.4 — End-User Guide

## 1. What this strategy is

`futures_v7_4.pine` is a TradingView Pine Script v6 **strategy** for testing
directional futures entries. It combines EMA trend structure, MACD momentum, RSI
bounds, ATR volatility, and optional relative volume. It also models contract
sizing, brackets, daily limits, session exits, and a strategy-wide drawdown lock.

The script is designed for **confirmed-bar decisions**. It does not calculate on
every tick, processes market orders on the confirmed signal bar's closing tick,
and does not use Bar Magnifier. An entry bar's opening and closing timestamps
must both satisfy its session and date gates, and same-close processing prevents
the eligible order from drifting beyond that closing boundary before fill. The
emulator fill is still not a guarantee of an attainable live price.

This is research and execution-modeling code, not financial advice or a
broker-side risk system. Test it with the exact symbol, contract, session,
timeframe, costs, and roll method that you expect to use. The repository's
`README.md` is the documentation entry point; `STRATEGY_REVIEW.md` records the
static review findings and residual risks. The Pine source is authoritative.

## 2. What the code review found

### Signal logic was previously coupled to trade eligibility

An earlier version put volatility, volume, session, and backtest eligibility in
the setup itself. With `Require New Setup Transition` enabled, a volume or
session filter changing from false to true could incorrectly look like a new
technical setup. Conversely, a genuine technical transition could be rejected
forever because a temporary execution gate was closed on that exact bar.

V7.4 uses a staged pipeline:

1. calculate the technical scores;
2. identify a directional technical transition;
3. retain that transition for `Signal Validity Bars`;
4. independently evaluate ATR, volume, session, and date filters;
5. independently evaluate position state, cooldown, daily controls, drawdown,
   and sizing; and
6. submit an entry only when every execution gate is open.

The retained signal is canceled logically as soon as its underlying directional
technical setup becomes false. Signal retention therefore handles temporary
gating; it does not authorize entries after the technical premise disappears.

### Brackets must be relative to the actual fill

Even with closing-tick processing, an absolute stop calculated around the signal
close can differ from its intended distance when modeled slippage changes the
fill. V7.4 stores the confirmed ATR distance in ticks and supplies it to
`strategy.exit` as relative `loss` and `profit` values. The displayed stop and
target are calculated only after the emulator reports the actual average fill.

### Minimum-size overrides could undermine safety limits

V7.4 distinguishes the optional account-risk override from hard limits. Turning
off `Skip Trade When Minimum Size Exceeds Risk` can permit the configured minimum
quantity to exceed the normal per-trade percentage budget. It **cannot** bypass
the enabled remaining-daily-loss-capacity limit or notional-exposure limit.

### Session settings require compatible chart bars

A narrow session window works only if a chart bar opens inside it. V7.4 therefore
adds an enabled-by-default local-time cutoff fallback that triggers on the first
confirmed bar at or after the cutoff. It also rejects synthetic charts,
non-time-based charts, non-intraday charts, and timeframes above a configured
maximum. No bar-based strategy can act while the market produces no bar.

## 3. Installation

1. Open TradingView and select the intended futures symbol.
2. Open **Pine Editor**.
3. Copy the complete contents of `futures_v7_4.pine` into a new script.
4. Save it, then select **Add to chart**.
5. Resolve every compiler or runtime error before using Strategy Tester results.
6. Open **Strategy Tester → Properties** and confirm the initial capital,
   commission, slippage, margin, order size, and recalculation settings shown by
   TradingView match the source and your test assumptions.
7. Open the strategy's **Inputs** and configure every section described below.

The declared defaults are USD 100,000 initial capital, USD 2.50 commission per
contract per fill, one tick of slippage, no pyramiding, 100% margin, confirmed-
bar calculation, same-close market-order processing, and no Bar Magnifier.
Document any property override and keep the separate round-trip commission sizing
input consistent.

Do not concatenate the script with another `//@version` or `strategy()` block.
There must be one version declaration and one strategy declaration.

## 4. Chart preparation

### Use the correct instrument

- Prefer the exact listed contract when evaluating real execution behavior.
- Continuous contracts can be useful for research, but back-adjustment and
  contract rolls can change indicator history, apparent gaps, and P&L.
- Confirm that TradingView supplies the correct minimum tick and point value.
  The strategy refuses to run if either value is non-positive.

### Use a standard, time-based intraday chart

The safe default is a normal candlestick or OHLC bar chart. Do not use Heikin
Ashi, Renko, Kagi, Line Break, Point & Figure, Range, or another synthetic price
series for execution claims. Keep the timeframe no larger than the configured
`Maximum Chart Timeframe (Minutes)`.

For a `1550-1555` exit window, verify visually whether the selected symbol and
timeframe produce a bar whose opening timestamp is within that window. If not,
the default 15:50 cutoff fallback triggers on the first later bar. Verify that
this fallback bar is still early enough for the intended operating policy.

## 5. Inputs, section by section

### 1. Trade Direction

- **Enable Long Entries** permits bullish orders.
- **Enable Short Entries** permits bearish orders.

Disable one side when testing a long-only or short-only mandate. Disabling a side
does not change how its score is calculated; the opposing score can still stop a
weaker setup from qualifying.

### 2. Trend

- **Fast/Slow EMA Length** define trend alignment. Fast must be shorter than
  slow.
- **EMA Slope Lookback** compares the current fast EMA with its value that many
  bars ago.
- **Minimum EMA Separation in ATR** rejects weak EMA separation after normalizing
  it by current ATR.

A long setup requires fast EMA above slow EMA and a rising fast EMA. A short
setup requires the inverse.

### 3. Momentum

- **RSI Length** controls RSI smoothing.
- **Minimum/Maximum RSI** define an allowed band for each direction rather than a
  single trigger. Longs use `minimum ≤ RSI < maximum`; shorts use
  `minimum < RSI ≤ maximum`.
- **MACD Fast/Slow/Signal Length** control MACD and its histogram.

The RSI minimum must be below its maximum. MACD fast must be below MACD slow.

### 4. Market Filters

- **ATR Length** is used by volatility qualification, stop distance, and sizing.
- **Minimum ATR as Percent of Price** rejects low-volatility bars.
- **Use Relative Volume Filter** requires current volume divided by average
  volume to meet the configured minimum.
- **Volume Average Length** and **Minimum Relative Volume** configure that test.

If volume filtering is enabled on a symbol without usable volume, entries are
blocked rather than treating missing data as acceptable.

### 5. Signal Controls

- **Minimum Signal Score** is the score threshold, from 1 through 12.
- **Require New Setup Transition** requires the technical setup to change from
  false to true.
- **Signal Validity Bars** controls how long that fresh event may wait for other
  gates. `0` means only the transition bar.
- **Cooldown Bars After Position Closes** delays the next entry after a detected
  close. The comparison is strict, so a setting of `5` requires more than five
  bars to have elapsed since the recorded exit bar.

When **Require New Setup Transition** is disabled, every bar on which the setup
remains true is an event. Signal age stays zero and **Signal Validity Bars** has
no practical limiting effect. With transition mode enabled, a validity of `3`
permits ages 0 through 3 (four chart bars total), while the setup remains true.

Long and short scores award:

| Condition | Points |
| --- | ---: |
| EMA directional alignment | 2 |
| Fresh EMA directional cross | 2 |
| Fast EMA directional slope | 1 |
| Price on directional side of fast EMA | 1 |
| Minimum EMA/ATR separation | 1 |
| MACD line on directional side of signal | 1 |
| MACD histogram directional sign | 1 |
| MACD histogram improving in that direction | 1 |
| Fresh MACD directional cross | 1 |
| RSI inside the directional band | 1 |

In addition to reaching the threshold, a setup must beat the opposing score and
meet the mandatory alignment, slope, and RSI conditions. The score alone is not
an entry instruction.

### 6. Position Sizing and Trade Risk

- **Account Risk per Trade (%)** creates the normal cash risk budget from current
  strategy equity.
- **Stop-Loss ATR Multiple** converts ATR to a stop distance.
- **Reward-to-Risk Target** multiplies stop ticks to obtain target ticks.
- **Minimum/Maximum Contracts** bound order quantity.
- **Skip Trade When Minimum Size Exceeds Risk** determines whether normal
  account-risk sizing may be overridden by the minimum quantity.
- **Entry/Slippage Risk Buffer in Ticks** increases sizing risk but does not move
  the bracket farther away.
- **Estimated Round-Trip Commission per Contract** increases sizing risk and is
  not charged a second time. Keep it at least equal to entry plus exit commission.
- **Limit Notional Exposure** and **Maximum Notional Exposure** create a hard
  leverage cap.
- **Cap New Trade Risk at Remaining Daily Loss Capacity** creates a hard quantity
  cap from unused daily-loss capacity.

The main calculations are:

```text
stop ticks = ceil(ATR × stop multiple ÷ minimum tick)
target ticks = ceil(stop ticks × reward/risk)
price risk per contract = (stop ticks + buffer ticks)
                          × minimum tick × point value
risk per contract = price risk per contract + round-trip commission
account quantity = floor(account risk budget ÷ risk per contract)
notional per contract = close × point value
```

Final quantity is the smallest enabled quantity cap, limited by
`Maximum Contracts`. If any enabled hard cap cannot support `Minimum Contracts`,
the displayed calculated quantity becomes zero and the order is rejected.

Notional exposure is not exchange initial margin. At the default 100% cap, one
contract fails when `close × point value` exceeds current equity. Change this only
under a documented leverage policy; it is distinct from the strategy's margin
properties. ATR distance, quantity, and bracket ticks freeze at submission. A
gap changes neither tick distance nor quantity, and buffer/commission inputs
affect sizing without widening the bracket.

### 7. Daily Risk Controls

- **Enable Daily Trade Limit** turns the filled-trade entry gate on or off.
- **Maximum Filled Trades per Day** counts increases in TradingView's combined
  open-plus-closed trade records. It counts observed fills, not submitted orders,
  and is enforced only when **Enable Daily Trade Limit** is on.
- **Enable Daily Loss Limit** turns daily-loss monitoring and its entry gate on
  or off. It also controls whether **Cap New Trade Risk at Remaining Daily Loss
  Capacity** can constrain sizing: when the daily-loss limit is off, that sizing
  cap is inactive even if its own switch is on.
- **Daily Loss Limit Mode** selects percentage of starting equity or fixed cash.
- **Maximum Daily Loss (%)** sets the allowance used in **Percent** mode as a
  percentage of equity at the start of the risk day.
- **Maximum Daily Loss (Cash)** sets the fixed allowance used in **Cash** mode.
- **Include Open P&L** chooses marked-to-market equity or realized net profit for
  daily monitoring.
- **Close Position at Daily Loss Limit** submits an immediate closing-tick market request.
- **Lock Trading for Rest of Risk Day** keeps the daily lock latched after the
  threshold is first reached.
- **Enable Strategy Drawdown Lock** enables a permanent entry lock once the
  configured peak-to-current-equity threshold is reached.
- **Maximum Drawdown from Peak Equity (%)** sets that threshold. Drawdown is
  measured from the highest strategy equity observed in the run, and the lock
  does not reset each day.
- **Close Position at Drawdown Limit** submits an immediate closing-tick market request for an
  open position once the drawdown lock is triggered. Turning it off leaves an
  existing position to other exit logic but does not restore new entries.

If maximum drawdown, daily loss, and the session policy require an exit on the
same bar, the script submits only one close request. Priority is maximum
drawdown, then daily loss, then session. Session processing and configured
flat-order cancellation still occur even when another close reason has priority.

The calendar risk day changes at midnight in the configured timezone, but reset
code runs on the first available chart bar in that new day. If the market is
closed at midnight, the baseline is captured on that first bar. A threshold can
be exceeded between confirmed-bar evaluations and a close need not fill at it.

The loss threshold records an internal flag for the risk day. When **Lock Trading
for Rest of Risk Day** is enabled, that flag blocks entries and causes enabled
forced liquidation for the rest of the day. When it is disabled, both the entry
gate and forced-liquidation condition follow the current threshold instead, so
P&L recovery restores normal operation. Remaining capacity is allowance plus
monitored P&L, floored at zero, so profits can raise capacity above the initial
allowance.

### 8. Session Management

- **Session and Daily Reset Timezone** must be a valid timezone appropriate for
  the venue and intended risk day.
- **Entry Session** gates new entries only.
- **Session Exit Trigger Window** requests a close on the first confirmed bar
  detected inside the window.
- **Use Session Exit Cutoff Fallback** also triggers the exit on the first
  confirmed bar that reaches, spans, or begins after the configured local cutoff.
- **Session Exit Cutoff Hour/Minute** define that fallback in the session
  timezone using a 24-hour clock. Keep the cutoff aligned with the start of the
  trigger window unless a deliberately later fallback is required.
- **Cancel Pending Orders at Session Exit** cancels outstanding strategy orders
  while flat. For an open position, protective brackets remain active while the
  immediate administrative close is processed.

Keep the cutoff fallback enabled so the first confirmed bar reaching or after the
cutoff triggers even when no bar opens in the narrow window. The request is
processed on the trigger bar's closing tick, but its live attainability and price
are not guaranteed. Absolute timestamps allow a bar that opens before midnight
and closes after midnight to detect a cutoff it spans. The first confirmed
exit-window or cutoff bar marks the session processed even while flat, blocking
entries until the next risk day.

### 9. Backtest Integrity

- **Block Nonstandard Chart Types** should normally remain enabled.
- **Require Intraday Chart** should remain enabled when session controls matter.
- **Maximum Chart Timeframe** prevents accidental tests on bars too coarse for
  the intended execution model.
- **Backtest Date Range** limits entry eligibility. Start must precede end.

The date filter does not liquidate an already-open position at the end date.
Existing bracket and administrative exit logic remains responsible for it. The
filter requires the signal bar to open at or after the start and close at or
before the end. The entry-session gate similarly requires both endpoints to be
inside the configured session. Same-close order processing then keeps an emulator
entry on that eligible closing tick, but a live alert consumer must enforce its
own cutoff.

### 10. Display

- **Signal Markers** show bars where an entry order was submitted, not guaranteed
  fills.
- **Active Stop and Target** appear after the fill is observed and are derived
  from the actual average fill.
- **Dashboard** shows current position, daily P&L, effective risk budget,
  per-contract risk, calculated quantity, scores, signal age, daily capacity,
  notional cap, drawdown-lock state, and TradingView's reported minimum tick,
  point value, and cash tick value. Compare all three metadata values with the
  venue's contract specification; display does not prove that the feed is right.

`na` in signal age means no qualifying setup event has occurred in the loaded
history. Zero calculated quantity means at least one enabled sizing constraint
cannot support the configured minimum quantity. Dashboard sizing values are
prospective current-bar values, not an audit record of the open trade. Planned
stop/target ticks clear after the strategy observes the position close.

## 6. Recommended validation workflow

1. **Compile first.** Fix all Pine compiler and runtime errors.
2. **Verify metadata.** Independently calculate the cash value of one tick as
   `syminfo.mintick × syminfo.pointvalue` and compare it with the contract spec.
3. **Verify bar alignment.** Confirm chart bars enter both the entry session and
   exit window in the selected timezone.
4. **Use realistic costs.** Synchronize the fixed `$2.50` per-side strategy
   commission with the sizing estimate and set realistic slippage.
5. **Inspect individual trades.** Check signal bar, same-close fill, fill-relative
   bracket, quantity, commission, and exit reason.
6. **Test gaps.** Inspect overnight, news, limit, and roll periods rather than
   relying only on averages.
7. **Run sensitivity tests.** Change costs, slippage, timeframe, session, and
   signal-validity assumptions. A robust result should not depend on one exact
   value.
8. **Separate development and evaluation data.** Avoid selecting parameters on
   the same full history used to report performance.
9. **Forward test.** Use paper trading before considering live execution.
10. **Reconcile alerts and broker behavior.** Strategy fills are emulator events;
    independently verify any external alert-to-order integration. Create a
    TradingView strategy alert that includes order-fill events and/or `alert()`
    calls as required. Treat all alert payloads as untrusted, authenticate the
    receiver, reject duplicates/stale timestamps, enforce session and quantity
    limits again, and reconcile broker acknowledgements and fills outside this
    script. Entry messages are `LONG_ENTRY` and `SHORT_ENTRY`; protective fills
    are `LONG_STOP_EXIT`, `LONG_TARGET_EXIT`, `SHORT_STOP_EXIT`, and
    `SHORT_TARGET_EXIT`;
    administrative fills and `alert()` events identify `DAILY_LOSS_EXIT`,
    `MAXIMUM_DRAWDOWN_EXIT`, or `SESSION_EXIT`. When controls coincide, only the
    prioritized administrative reason is emitted.

## 7. Troubleshooting

### “Use a standard OHLC chart”

Switch from a synthetic chart to normal candles or bars, or disable the block
only for visual research. Do not treat synthetic-chart fills as executable.

### “Intraday chart” or “timeframe exceeds maximum”

Choose a time-based intraday interval at or below the configured maximum. Then
re-check exit-window alignment.

### Strategy shows signals but no trade

The plotted entry marker appears only when an order is submitted. If no marker is
shown, inspect score, signal age, session, ATR/volume filters, cooldown, daily
trade count, daily-loss lock, drawdown lock, effective risk budget, notional cap,
and calculated quantity.

### Calculated quantity is zero

At least one hard cap cannot support one minimum contract. Review risk per
contract, remaining daily capacity, notional exposure, equity, and the minimum
contract setting. Do not raise a cap merely to force a trade.

### Session exit did not occur

Check timezone, exchange holidays, session template, timeframe, bar opening
times, and whether a bar actually opened inside the trigger window. Remember
that the immediate close is submitted after the confirmed trigger bar and is processed on
that bar's closing tick by the emulator.

### Results change when timeframe changes

This is expected. EMA, RSI, MACD, ATR, signal validity, cooldown, session
intersection, and the broker emulator's intrabar assumptions all operate on chart
bars. A “bar” is not a fixed unit of elapsed time across timeframes.

## 8. Pre-use checklist

- [ ] Pine Editor compiles the unmodified V7.4 source.
- [ ] Chart is standard, time-based, intraday, and within the maximum timeframe.
- [ ] Exact contract or continuous-contract methodology is documented.
- [ ] Tick size and point value match the exchange contract specification.
- [ ] Commission estimate matches the strategy commission assumption.
- [ ] Slippage and sizing buffer are realistic for the market and order size.
- [ ] Timezone, entry session, risk-day reset, and exit bar alignment are verified.
- [ ] Minimum size does not unintentionally override the normal account-risk cap.
- [ ] Daily-capacity and notional hard caps behave as expected.
- [ ] Drawdown lock behavior has been tested on historical losses.
- [ ] Backtest end behavior and any open position are understood.
- [ ] Trade-by-trade fills and brackets have been inspected.
- [ ] Out-of-sample and paper-trading results have been reviewed.
- [ ] Live broker-side risk controls exist independently of this script.

## 9. Known limitations

The authoritative condensed list of review findings and limitations is maintained
in `STRATEGY_REVIEW.md`. In particular, no bar-close strategy can guarantee an
intrabar daily-loss threshold, gap price, partial fill, or live liquidation
price. TradingView's Pine compiler and broker emulator are authoritative for
actual script behavior.
