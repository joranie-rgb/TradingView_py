# Code Review, Feature Assessment, and Recommended Roadmap

## 1. Purpose and scope

This document reviews the current `futures_v7_4.pine` strategy and proposes a
prioritized feature roadmap. It is an assessment and planning document only; it
does not change the strategy's trading logic, risk policy, order behavior, or
alerts.

The review covers strategy configuration, signals and execution gates, position
sizing, risk controls, order lifecycles, alerts, observability, documentation,
and tests. TradingView's Pine compiler and broker emulator remain authoritative;
static review cannot prove fill ordering, live alert timing, or symbol-specific
behavior.

## 2. Executive assessment

The repository is compact, well documented, and safety-conscious. The strategy
has a clear pipeline from technical setup through execution eligibility and
position sizing, with independent daily-loss, notional-exposure, session, and
drawdown controls. Static regression tests protect important source invariants.

No high-confidence defect requiring an immediate code correction was identified
in this assessment. The best near-term opportunities are improved observability,
more informative alert payloads, and automated validation. Those features should
precede additional entry and exit parameters because they make future behavior
easier to understand and verify without first increasing the optimization
surface.

## 3. Current strengths

### 3.1 Explicit execution model

The strategy explicitly disables pyramiding, fill-triggered recalculation,
tick-by-tick recalculation, and Bar Magnifier. It enables same-close market-order
processing and requires confirmed-bar decisions, making its assumptions visible
instead of relying on platform defaults.

### 3.2 Separation of technical intent and trade eligibility

Technical setups are calculated independently from volatility, volume, session,
date, cooldown, sizing, and risk gates. A new setup can remain eligible for a
bounded number of bars, but only while its underlying directional premise remains
true. A filter transition therefore cannot manufacture a technical transition.

### 3.3 Layered position sizing

Final quantity is constrained by account risk, remaining daily-loss capacity,
notional exposure, and the configured maximum contract count. Daily-capacity and
notional limits remain hard caps even when the optional minimum-size account-risk
override is enabled.

### 3.4 Fill-relative protective brackets

Stop and target distances are frozen in ticks when an entry is submitted and are
attached to the entry order. Displayed levels are subsequently calculated from
the observed average fill price, avoiding a bracket anchored to the earlier
signal close.

### 3.5 Deterministic administrative exits

Maximum drawdown, daily loss, and session exit conditions are reduced to one
prioritized administrative reason. This prevents duplicate close requests and
keeps order-fill messages and `alert()` events semantically aligned.

### 3.6 Useful static regression suite

The dependency-free tests protect strategy properties, hard sizing caps, boundary
checks, fill-relative exits, session fallback behavior, administrative-exit
priority, alert coverage, and input dependencies.

## 4. Constraints and review risks

The following are platform or modeling limitations rather than confirmed code
defects:

1. **Confirmed-bar risk response.** Daily-loss and drawdown decisions cannot
   react inside a bar. Gaps, limit moves, and alert latency can exceed modeled
   loss.
2. **Emulator-dependent order lifecycle.** Same-close entry, protective bracket,
   and administrative-exit ordering must be verified in TradingView.
3. **First-bar daily reset.** The risk-day baseline is established on the first
   available bar of a new calendar day, not at an independently evaluated
   midnight tick.
4. **Symbol metadata is necessary but insufficient.** Valid tick and point values
   do not prove that a continuous-contract series, roll policy, session template,
   or commission model is appropriate.
5. **External execution remains external.** The strategy has no authenticated
   webhook receiver, idempotency store, broker reconciliation, or partial-fill
   management.
6. **Static tests do not compile Pine.** Textual invariants cannot replace
   compilation and trade-by-trade broker-emulator tests.

## 5. Feature assessment criteria

Roadmap items are evaluated using four criteria:

- **User value:** improvement to operation, research, or safety;
- **Behavioral risk:** likelihood of changing entries, exits, or reported results;
- **Validation cost:** required TradingView scenario testing; and
- **Overfitting risk:** additional parameter flexibility introduced.

Features that improve visibility and verification rank ahead of features that add
trading parameters.

## 6. Recommended feature roadmap

### Phase 1 — Observability and integration safety

#### 6.1 Entry blocker diagnostics — completed

The dashboard now provides separate long and short status fields identifying why
an otherwise relevant setup cannot submit an entry. Reported states include:

- `NO TECHNICAL SETUP`;
- `SIGNAL EXPIRED`;
- `OUTSIDE ENTRY SESSION`;
- `OUTSIDE BACKTEST RANGE`;
- `ATR FILTER` or `VOLUME FILTER`;
- `COOLDOWN`;
- `DAILY TRADE LIMIT`;
- `DAILY LOSS LOCK` or `DRAWDOWN LOCK`;
- `DAILY CAPACITY` or `NOTIONAL CAP`;
- `MINIMUM SIZE`; and
- `READY`.

Separate long and short states would be more informative when both directions are
enabled.

**Value:** High.  
**Behavioral risk:** Low.  
**Validation cost:** Low to medium.  
**Status:** Completed. The implementation is display-only and does not participate
in the entry conditions. Keep its gate ordering synchronized with future changes
to entry eligibility.

#### 6.2 Structured, versioned alert payloads

Replace or supplement event-name-only messages with a documented JSON schema.
Useful fields include the schema and strategy version, event identifier, symbol,
exchange, timeframe, signal and expiration timestamps, action, direction,
quantity, planned bracket ticks, risk-day identifier, and administrative reason.

The external receiver must still authenticate requests, reject duplicates and
stale messages, reapply session and quantity limits, and reconcile broker
acknowledgements and fills.

**Value:** High for automation; medium for manual use.  
**Behavioral risk:** Low if event timing is unchanged.  
**Validation cost:** Medium.  
**Recommendation:** Implement after blocker diagnostics and publish the schema.

#### 6.3 Research telemetry

Extend the dashboard or Data Window with non-ordering diagnostics:

- account-risk, daily-capacity, notional, and maximum-contract quantity caps;
- current and peak drawdown;
- realized and open daily P&L;
- current trade risk in cash and percent;
- bars in position;
- setup count versus submitted and filled trade count;
- planned and active bracket values; and
- each score component's contribution.

Visibility should come before making score weights configurable.

**Value:** High.  
**Behavioral risk:** Low.  
**Validation cost:** Medium.  
**Recommendation:** Include where Pine table and resource limits permit.

### Phase 2 — Validation and backtest integrity

#### 6.4 Continuous integration

Add a CI workflow that runs:

```bash
python -m unittest discover -s tests -v
python -m py_compile tests/test_strategy_contract.py
git diff --check
```

Additional checks can verify that documented inputs match source labels and
defaults, every order-generating call includes an alert message, and no accidental
future-data request is introduced. Where practical, tests should target logical
source sections rather than rely on global occurrence counts. Static checks must
continue to state that they are not a Pine compiler.

**Value:** High for maintenance.  
**Behavioral risk:** None.  
**Validation cost:** Low.  
**Recommendation:** Implement early in Phase 2.

#### 6.5 Configurable end-of-backtest policy

The current date filter blocks entries but does not liquidate a position at the
configured end. Add an explicit policy:

- block new entries only;
- close on the final eligible confirmed bar; or
- close on the first confirmed bar after the end timestamp.

The selected behavior must define what happens when no chart bar closes exactly
at the configured end.

**Value:** Medium to high for comparable backtests.  
**Behavioral risk:** Medium.  
**Validation cost:** Medium.  
**Recommendation:** Use a backward-compatible default.

#### 6.6 Manual blackout and gap-risk controls

Add optional date/time blackout windows for contract rolls, scheduled events, or
known illiquid periods. Supporting controls could include a maximum opening-gap
filter and a separate overnight risk buffer.

Manual windows are preferable to claiming universal automatic futures-roll
detection because calendars and continuous-series construction vary by market
and provider.

**Value:** Medium.  
**Behavioral risk:** Medium.  
**Validation cost:** Medium.  
**Recommendation:** Require clear chart-timezone semantics.

### Phase 3 — Trade and risk management

#### 6.7 Optional break-even, trailing, and time exits

Add independently selectable management modes:

1. move the stop to break-even after a configurable R or ATR threshold;
2. trail by ATR after a configurable activation threshold; and
3. exit after a maximum number of bars in the position.

Each mode must define its interaction with the original bracket and the priority
of simultaneous protective, timed, session, daily-loss, and drawdown exits.
Existing fixed-bracket behavior should remain the default.

**Value:** Medium to high.  
**Behavioral risk:** High.  
**Validation cost:** High.  
**Overfitting risk:** Medium to high.  
**Recommendation:** Implement only after alert and diagnostic improvements.

#### 6.8 Drawdown-based risk throttle

Add an optional tiered reduction in account risk before the permanent maximum
drawdown lock is reached: full risk below threshold A, reduced risk between A and
B, and no new entries at threshold B. The permanent drawdown lock must remain the
final hard control and must not be weakened by the throttle.

**Value:** Medium.  
**Behavioral risk:** High.  
**Validation cost:** High.  
**Recommendation:** Make it an opt-in policy with conservative defaults.

#### 6.9 Daily-profit capacity policy

The current remaining daily-loss capacity can grow when daily P&L is positive.
Offer explicit policies:

- profits expand capacity, preserving current behavior;
- capacity is capped at the original daily allowance; or
- part of daily profits is locked and unavailable for new risk.

**Value:** Medium.  
**Behavioral risk:** Medium.  
**Validation cost:** Medium.  
**Recommendation:** Add only if alternative daily-risk mandates are needed.

### Phase 4 — Signal research

#### 6.10 Higher-timeframe or market-regime filter

Potential opt-in filters include higher-timeframe EMA alignment, trend strength,
or a realized-volatility regime. Higher-timeframe inputs must use confirmed data
with explicit non-lookahead behavior, and the display should identify the source
timeframe and current regime.

**Value:** Research-dependent.  
**Behavioral risk:** High.  
**Validation cost:** High.  
**Overfitting risk:** High.  
**Recommendation:** Defer until observability and validation work is complete.

#### 6.11 Score component controls

Use a staged approach:

1. display component contributions;
2. permit components to be enabled or disabled;
3. only then consider bounded integer weights; and
4. optionally require agreement across independent trend and momentum categories.

Avoid exposing many continuous parameters at once. Every new degree of freedom
increases the chance of fitting historical noise.

**Value:** Medium for research.  
**Behavioral risk:** High.  
**Validation cost:** High.  
**Overfitting risk:** Very high.  
**Recommendation:** Lowest priority.

## 7. Recommended implementation order

1. Entry blocker diagnostics — completed.
2. Structured and versioned alerts.
3. CI and stronger static contract checks.
4. Research telemetry and score-component visibility.
5. Configurable end-of-backtest liquidation.
6. Manual blackout and gap-risk controls.
7. Optional break-even, trailing, and time exits.
8. Drawdown-based risk throttling and daily-profit capacity policy.
9. Higher-timeframe or regime filters.
10. Configurable score components or weights.

This sequence improves the ability to explain, integrate, and verify the current
strategy before expanding its trading behavior.

## 8. Acceptance criteria for roadmap work

Every future feature should include:

- a backward-compatible default unless a safety defect requires otherwise;
- precise confirmed-bar and order-processing semantics;
- documented interactions with daily, drawdown, session, date, and sizing gates;
- stable alert behavior or a versioned alert-schema change;
- static regression coverage for reviewable invariants;
- Pine Editor compilation of the complete source;
- trade-by-trade TradingView broker-emulator scenarios; and
- corresponding updates to `README.md`, `USER_GUIDE.md`, and
  `STRATEGY_REVIEW.md` where applicable.

At minimum, emulator scenarios should cover long and short entries, protective
stops and targets, coincident administrative controls, session and midnight
boundaries, gaps, date-range boundaries, zero-quantity sizing, and alert ordering.

## 9. Conclusion

The current implementation has a strong safety and documentation base. The next
release should emphasize diagnostics, structured alerts, and automated validation
rather than immediately adding more indicators or tunable weights. Once those
foundations are in place, trade-management and regime features can be introduced
as explicit, opt-in policies with clearer evidence about their behavior and value.
