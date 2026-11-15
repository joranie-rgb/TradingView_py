# Pine patch release candidate

Prepared November 15, 2026, from main `55e9eb6`, including merged PRs #15 and #16.
This PR prepares versioned sources and guides for review. It does not publish a
GitHub Release or a TradingView community script.

| File | Previous display version | Release candidate |
| --- | --- | --- |
| `futures_v7_5.pine` | 7.5.2 | **7.5.3** |
| `futures_v7_4.pine` | 7.4.1 | **7.4.2** |
| `liquidity_structure_v1.pine` | LSM 1.1 | **LSM 1.1.1** |

Source filenames remain stable. Input defaults, order rules and strategy
Properties are unchanged from the merged behavior fixes. This patch updates
titles, indicator panel/message versions, structured-alert strategy version and
event-ID prefix, guides, and generated fixture source identities.

## Included fixes

All three scripts determine session membership using the actual opening minute
and compare the actual candle close against the calendar session end. This
restores valid on-the-hour candles within a 09:30 session while excluding bars
that extend past its end. Overnight ends handle calendar rollover and DST.
Mixed-date candles remain excluded from new entries and indicator setups.

The release also packages the prior lifecycle hardening: calendar-day resets,
partial/full exit distinction, fill-relative brackets and sizing limits,
validated alert instance identities, indicator invalidation and expiry priority,
frozen drawing levels and target rounding. The
[review matrix](REVIEW_FIXES.md) and [validation overview](HARDENING_VALIDATION.md)
describe these fixes and their limits.

Hosted fixture safeguards now reject unsupported accounting charts and fail
generation on missing or duplicated indicator-title anchors. These fixtures are
verification tools and must not be used to create alerts or broker orders.

## Upgrade and saved alerts

1. Archive the previous source version, inputs, Properties and alert definitions.
2. Replace each complete Pine source using the same filename. Confirm the chart
   legend shows Fut V7.5.3, Fut V7.4.2 or LSM v1.1.1 as appropriate.
3. Compile the selected release source in Pine Editor and inspect its panel,
   settings and symbol metadata before relying on results.
4. Update strict receiver allowlists to strategy version **7.5.3**. The JSON
   schema remains **2.0.0** with the same fields and meanings. The strategy-version
   field and event-ID prefix change to 7.5.3. Treat event IDs as opaque.
5. Stop/replace prior alerts for the deployment and recreate alerts from the new
   source after verifying inputs. Saved TradingView alerts retain old snapshots;
   changing the chart source does not upgrade them. Avoid duplicate old/new
   deployments. Use an instance ID unique to the account and Properties.
6. Check notifications and external integration behavior independently. The
   compatibility strategy keeps its legacy text alerts; it does not emit the
   V7.5.3 JSON contract. The indicator messages now identify LSM v1.1.1.

See [strategy instructions](USER_GUIDE.md), the
[Word indicator guide](Liquidity_Structure_Monitor_User_Guide.docx), and the
[JSON contract](ALERT_SCHEMA.md).

## Validation and remaining limits

The [November 11 report](tests/hosted/RESULTS_2026-11-11.md) records historical
indicator lifecycle assertions on one-minute and hourly MNQ and controlled
accounting reconciliation. The [November 15 report](tests/hosted/RESULTS_2026-11-15.md)
records updated-fixture compilation, three rejected chart contexts and recovery.
Accounting was USD 28 gross less USD 25 commission equals USD 3 emulator net.
These reports identify the pre-bump source revisions; their hashes and images
remain unchanged. Regenerated fixtures describe the release candidate sources,
not a new hosted test run.

Existing regression checks verify payload/schema consistency, source helper
behavior, platform short-title limits and generated fixture synchronization.
All 62 local tests pass after the final serialization correction. Before that
correction, version-string normalization reproduced the three pre-bump
production sources exactly. The Word guide was rendered to seven
pages and visually inspected; current guide versions, schema fields, 43 local
root-document links and whitespace checks were verified.
The renamed candidate sources completed [final TradingView checks](tests/hosted/RELEASE_CHECKS_2026-11-15.md).
A native probe found lowercase r corruption in the JSON escape helper. The
correction passed native helper assertions and full-strategy compilation; it
requires this correction PR to merge before it is present on main.
This PR introduces no trading-performance optimization or profitability claim.

External receiver testing, live delivery, Bar Replay equivalence and exhaustive
liquidation/FX paths remain **UNVERIFIED**. Currency, point value and tick-size
conditions have independent local tests but were not individually falsified in
the hosted run. ETH, back adjustment and Properties remain manual prerequisites.
