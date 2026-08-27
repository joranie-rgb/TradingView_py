# TradingView Futures Strategy V7.5

This repository contains a TradingView Pine Script v6 strategy for researching
directional futures entries. It combines EMA, MACD, RSI, ATR, and optional
relative-volume signals with fill-relative brackets, equity-based sizing, daily
controls, session management, and a permanent peak-equity drawdown lock.

## Repository map

| File | Purpose |
| --- | --- |
| [`futures_v7_5.pine`](futures_v7_5.pine) | Authoritative executable strategy source. |
| [`ALERT_SCHEMA.md`](ALERT_SCHEMA.md) | Versioned JSON alert contract, event semantics, and receiver obligations. |
| [`USER_GUIDE.md`](USER_GUIDE.md) | Installation, complete input reference, formulas, operating workflow, and troubleshooting. |
| [`STRATEGY_REVIEW.md`](STRATEGY_REVIEW.md) | Code-review findings, execution semantics, safety boundaries, and residual risks. |
| [`CODE_REVIEW_AND_FEATURE_ROADMAP.md`](CODE_REVIEW_AND_FEATURE_ROADMAP.md) | Current feature assessment and prioritized roadmap for future releases. |
| [`tests/test_strategy_contract.py`](tests/test_strategy_contract.py) | Local static regression checks for safety-critical source invariants. |

If prose and behavior ever differ, the Pine source and TradingView's compiler
and broker emulator are authoritative. This repository does not contain a Pine
compiler or an automated execution simulator.

## Quick start

1. Read the [review and limitations](STRATEGY_REVIEW.md).
2. Follow the [installation and chart-preparation guide](USER_GUIDE.md#3-installation).
3. Copy the entire Pine file into TradingView's Pine Editor and compile it.
4. Validate tick value, point value, contract notional, costs, timezone, session
   intersection, and same-close fills for the exact symbol and timeframe.
5. Inspect trades individually and forward-test with paper trading. Do not treat
   Strategy Tester results as a broker-side risk guarantee.

## Fixed strategy properties

The source declares these baseline properties:

- USD 100,000 initial capital;
- USD 2.50 cash commission per contract per fill;
- one tick of modeled broker-emulator slippage;
- no pyramiding;
- 100% long and short margin;
- confirmed-bar calculations, same-close market-order processing, and no Bar Magnifier.

TradingView can expose property overrides in the user interface. Record any
override with the results it produced, and keep the sizing input for estimated
round-trip commission synchronized with the actual commission model.

## Scope and safety

This is research and execution-modeling code, not financial advice, an alert
receiver, broker integration, or broker-side risk system. The strategy emits
versioned JSON order-fill messages and `alert()` events for an independently
secured TradingView alert. Daily-loss, drawdown, and session exits are immediate
closing-tick market requests generated after a qualifying bar is confirmed. See
the [published payload schema](ALERT_SCHEMA.md). These requests are not intrabar
stop orders or guarantees of the fill price.

## Local validation

The executable runtime is TradingView's hosted Pine v6 environment; there is no
database, backend, package dependency, secret, environment variable, deployment
manifest, or local service in this repository. Run the repository's dependency-
free static contract checks with:

```bash
python -m unittest discover -s tests -v
```

Then compile the complete source in TradingView Pine Editor and perform the
symbol-specific broker-emulator checks in the user guide. The local tests guard
important textual/state-machine invariants but are not a Pine compiler or a
substitute for trade-by-trade emulator validation.
