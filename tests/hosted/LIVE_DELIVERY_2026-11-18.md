# V7.5.3 long and short alert evidence — November 18, 2026

Inspected approximately 10:08 America/New_York; TradingView's clock showed
10:07:56–10:08:02 UTC-5. Compared with the [November 17 19:43 inspection](LIVE_DELIVERY_2026-11-17.md), the populated NOVEMBER 18 log showed:

| Logged time | Event | Matching rows | Action / direction / quantity | Planned stop / target ticks |
| --- | --- | --- | --- | --- |
| 09:31:00 | LONG_ENTRY | 2 | ENTER / LONG / 1 | 128 / 256 |
| 09:31:23 | LONG_STOP_EXIT | 1 | EXIT / LONG / 1 | 128 / 256 |
| 09:38:00 | SHORT_ENTRY | 2 | ENTER / SHORT / 1 | 224 / 448 |
| 09:41:12 | SHORT_TARGET_EXIT | 1 | EXIT / SHORT / 1 | 224 / 448 |
| 09:59:00 | LONG_ENTRY | 2 | ENTER / LONG / 1 | 376 / 752 |

Eight rows represent five event occurrences, including three entries. Matching
entry pairs are not independent setups. Displayed payloads retain schema 2.0.0,
strategy 7.5.3 and instance research-1. These are strategy emulator notifications,
not broker fills or external reconciliation. Planned ticks do not establish
execution of every bracket path.

The 09:38 entry retains a 09:36 signal timestamp (1795012560000), submission
09:38 encoded in event_id (1795012680000), and expiration 09:39
(1795012740000). Entry expiration is 60 seconds after submission, not always
after signal time. The 09:31 entry expires at 09:32 and the 09:59 entry at
10:00. Both exits have null expiration; receiver enforcement is unverified.

The [structured record](evidence/tradingview-live-events-2026-11-18.json)
transcribes selected observed fields and row counts, not complete raw payloads.
No screenshot was saved and no new log-filter inspection was performed.
Earlier images do not depict these events.

All four original replacement alerts were Active. V7.5.3's latest trigger
advanced to November 18 09:59. V7.4.2 remained November 17 15:50 with no newer
message observed; LSM SHORT remained November 16 11:13. LSM LONG had no
latest-trigger time and no LONG event appeared: delivery is **PENDING**, not failed.

A 09:59 V7.5.3 LONG_ENTRY browser card was directly visible retrospectively.
Original arrival time and latency are unknown. Other event toasts and mobile
push/sound for all these new events remain **UNVERIFIED**. Earlier user
confirmations do not cover them. No later exit for the 09:59 entry appeared;
its complete lifecycle remains unverified.

Specific V7.5.3 long-entry and long-stop log examples are now observed; earlier
long-side pending wording is historical for these examples. Long-target exits,
exhaustive paths, per-event receipt attribution, devices, exact arrival times
and latency remain unverified. November 17 V7.4.2 11:35 entry/12:17 stop
push/sound/toast limits and both strategies' 15:50 push/sound limits remain
unresolved. V7.4.2's November 17 session-exit toast is still unverified; the
V7.5.3 card has prior retrospective visibility. The November 16 V7.4.2
10:52:31 trigger remains unclassified. External receiver deduplication/expiry
enforcement and broker reconciliation remain unverified; no receiver is configured.

The chart showed one minute on the first pane and five on the second. No alert
settings, chart intervals or source inputs were changed, no log was cleared,
and no broker orders were submitted. This bounded inspection is not continuous
monitoring or complete-history verification.
