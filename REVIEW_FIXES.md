# Review fixes for the futures scripts

This release addresses the 14 findings reviewed at commit `1151359`.
Source filenames remain stable: `futures_v7_5.pine` is now **V7.5.2**,
`futures_v7_4.pine` is compatibility **V7.4.1**, and
`liquidity_structure_v1.pine` is **LSM v1.1**.

## Resolution matrix

| Review finding | Change | Local regression coverage |
| --- | --- | --- |
| 1 Daily reset session hole | Explicit timezone-local midnight timestamp replaces the session-based day ID. | Sequence 23:58, 23:59, 00:00, 00:01 resets exactly once; both strategies. |
| 2 Actual session endpoints | Compare actual bar open and close against generated session endpoints. | Full, partial, late-ending, and missing-session endpoint cases; both strategies. |
| 3 Currency mismatch | Convert price risk and notional to account currency before budget comparison; estimated commission is already account currency. | Non-unit FX rate changes the computed amount and affordable quantity; both strategies. |
| 4 Partial liquidation cleanup | Cleanup/cooldown require a fully flat position. Entry counting uses distinct entry timestamps, including closed records for unobserved round trips, with fill-date attribution. | Partial close, full close, unobserved round trip, duplicate entry observation; both strategies. |
| 5 First-bar losses omitted | At a date reset carry the previous available equity/net-profit valuation. Closure gaps count; no synthetic midnight valuation is claimed. | A 100000 to 98000 first-bar drop remains a 2000 daily loss; both strategies. |
| 6 Margin affordability | Always cap quantity by conservative 100% buffered notional plus estimated round-trip costs; expose MARGIN CAP and its quantity. | Insufficient funds, exact affordability, missing conversion, and each hard quantity cap; both strategies. |
| 7 EMA separation only a score | Require minimum separation in both directional technical setups; retain its score contribution and add a blocker message. | High scores cannot bypass failed separation; both strategies. |
| 8 Opening-date sweep suppressed | Reset only the old arm; allow a new qualifying sweep on the first date bar. Store the new arm's date. | Date cancellation versus fresh-date eligibility and arming wiring. |
| 9 Ambiguous sweep with used pivot | Detect physical penetration independently from pivot consumption flags. | Both physical sides detected even when one is already consumed; long/short wiring rejects ambiguity. |
| 10 Zero-distance rounded target | Round the target distance outward to whole ticks with a minimum one favorable tick. | Long and short low-R, fractional-tick, and normal-R cases. |
| 11 Cross-configuration event identity | Schema 2 adds instance and canonical input configuration identity; namespace event IDs by both and version. | Instance/config distinction, duplicate logical-event stability, and coverage of all behavior inputs. |
| 12 Insufficient test coverage | Keep source contracts, add tests that evaluate actual pure Pine decision expressions, and run them in GitHub Actions. Hosted Pine checks remain explicit release requirements below. | Both strategies and indicator decisions; no claim of a full Pine runtime. |
| 13 Misleading live panel | Use the cancellation decision for both pending setup handling and the live panel, recomputing after reset/rearm. | Invalidating breach, equality touch, expiry, and panel wiring. |
| 14 Joined structure levels | Use a distinct line object per arm, finalizing the old object's endpoint before replacement. | Object-per-arm wiring, bounded history, and removal of the shared connecting plot. |

## Migration

- Recompile the complete scripts and recreate alerts after source/input changes.
- V7.5.2 requires alert **schema 2.0.0**. Migrate receivers before creating the
  new alerts; `instance_id` and `configuration_id` are required. Treat event IDs
  as opaque strings. See [the schema and migration guide](ALERT_SCHEMA.md).
- Set **Alert Instance ID** uniquely per account/deployment. Change it after
  changing Strategy Properties; Pine cannot fingerprint all Property overrides.
  Input configurations are included automatically, including risk/session gates.
- Currency conversions use TradingView's account conversion. Missing conversion
  data blocks sizing. The commission estimate is already in account currency.
- The 100% margin affordability cap remains conservative if UI margin is reduced.
  Keep buffer ticks at least as high as Properties slippage, and commission
  estimates at least as high as modeled round-trip costs. Unmodeled Property
  overrides, gaps, and broker conditions can still reject or alter fills.
- Historical results will change: separation is now a mandatory filter, opening
  sweeps can arm, and targets use outward tick rounding. Do not compare results
  without recording versions and settings.
- Daily baselines use the previous available valuation, including closure gaps.
  Entry records are attributed by actual entry timestamp. This is intentionally
  distinct from a separately sampled midnight account statement.

## Validation boundary

Run `python -B -m unittest discover -s tests -v` and `git diff --check`.
Local result for this release: **36 tests passed**, whitespace checks passed,
schema JSON parsed, Pine delimiter checks passed, and the updated Word guide's
archive/XML and current instructions were checked. Delimiter checks are not
Pine compilation; document structure checks are not visual page verification.
`tests/test_review_regressions.py` extracts the actual decision expressions from
the Pine files, evaluates their supported arithmetic/boolean subset against
edge cases, and checks wiring to the relevant state branches. It is not a Pine
compiler, a complete interpreter, a broker emulator, or a notification test.
The suite is dependency-free; GitHub Actions runs it on Python 3.12 and 3.13.

No successful TradingView compilation or emulator run has been established by
these local checks. The Word guide's package can be checked locally, but visual
page rendering is unavailable when the bundled environment has no LibreOffice.

Before using this release operationally, complete these hosted checks:

- [ ] Compile all three full Pine v6 sources without errors.
- [ ] Continuous 1m chart: daily counters and session locks reset across 23:59.
- [ ] RTH chart: first-bar losses count and prior-fill observations use fill date.
- [ ] Hourly chart: a bar ending after the entry-session end is excluded.
- [ ] Non-account-currency instrument: verify risk/notional conversion and quantity.
- [ ] Insufficient-margin configuration: no entry intent; MARGIN CAP is visible.
- [ ] Partial margin liquidation: residual plan/refresh remains and trade count does not increase.
- [ ] Full same-bar round trip: plan clears, one entry is counted, cooldown starts.
- [ ] RTH opening sweep arms after a prior-date reset and can later confirm.
- [ ] Both-side penetration is rejected with either pivot already consumed.
- [ ] Low-R short reference target remains at least one tick below signal close.
- [ ] Forming-bar invalidation/expiry/reset diagnostics agree with closing behavior.
- [ ] Replacement setup has a separate yellow line without a diagonal connector.
- [ ] Two account instances/configurations emit distinct IDs; duplicate intent/fill events retain the same ID.
- [ ] Reload/Replay results, live notifications, and schema 2 receiver migration are verified.
