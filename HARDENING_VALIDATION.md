# Lifecycle hardening and verification

This work follows the approved October 29 hardening specification. It is not a
claim of successful hosted Pine execution or improved trading performance.

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
midnight account balances. Post-calculation closing-tick fills and commissions
must still be reconciled in the hosted emulator. Local supplied-observation
fixtures do not prove their actual delivery timing.

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
The current suite has 53 passing tests. New coverage includes New York midnight,
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

## Outstanding acceptance evidence

- Successful compilation of all three exact current source files in TradingView.
- Replay and live confirmation of resets, expiry/invalidation, drawing replacement,
  partial liquidations, closing-tick fills/commissions, and alert delivery.
- Receiver-side acceptance tests in the actual external execution integration.
- A final security and documentation audit after runtime corrections.

The browser connection recovered on October 29. The exact working-tree indicator
was pasted into Pine Editor. Clicking Add to chart opened TradingView's account
sign-up prompt instead of a compiler result. The browser session is not signed
in; the authenticated desktop application cannot be controlled by the available
browser-only tools. This establishes neither compiler success nor compiler
failure. Resume hosted checks in an authenticated TradingView browser session.

These are unreleased changes to the existing versioned files. Before a release,
bump the script versions and synchronize the Word guide after hosted corrections.
The current Word guide predates the stricter session-day validation and calendar
boundary exclusion; this document is the addendum for this draft.

No signal-performance optimization or improved win-rate claim has been made.
Any later filter optimization requires a frozen baseline, chronological holdout,
cost assumptions, sample counts, expectancy, drawdown, and uncertainty estimates.
