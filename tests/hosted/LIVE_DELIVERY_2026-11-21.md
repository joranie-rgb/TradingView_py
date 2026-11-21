# November 19–20 alert evidence inspected November 21

Inspected Saturday November 21 approximately 09:15 America/New_York (chart
clock 09:15:11–09:15:27 UTC-5), market closed. Baseline is the
[November 18 10:08 observation](LIVE_DELIVERY_2026-11-18.md).

| Date | Strategy | Newly inspected log events, New York time |
| --- | --- | --- |
| Nov 19 | V7.5.3 / 1m | LONG_ENTRY pairs 09:33, 09:45; LONG_STOP_EXIT 09:38:04, 09:46:50; SHORT_ENTRY pair 09:56; SHORT_STOP_EXIT 10:04:00; SESSION_EXIT 15:50 |
| Nov 19 | V7.4.2 / 5m | LONG_ENTRY 09:50, LONG_STOP_EXIT 09:54:20; SHORT_ENTRY 10:25, 11:55; SHORT_TARGET_EXIT 10:36:01, 12:03:46; SESSION_EXIT 15:50 |
| Nov 20 | V7.5.3 / 1m | SHORT_ENTRY pairs 09:34, 09:43; SHORT_STOP_EXIT 09:36:52, 09:47:53; LONG_ENTRY pair 09:54; LONG_TARGET_EXIT 10:00:06; SESSION_EXIT 15:50 |
| Nov 20 | V7.4.2 / 5m | LONG_ENTRY 09:55, LONG_STOP_EXIT 10:14:19; SHORT_ENTRY 13:05, SHORT_STOP_EXIT 13:55:03; SESSION_EXIT 15:50 |

V7.5.3 entry pairs are matching payload rows for one entry, not independent
setups. V7.4.2 entries showed intent and expanded emulator-fill messages.
These are retrospective emulator notifications, not broker fills or accounting
reconciliation. The inspected portion covers November 19–20, not all history
since the baseline. No screenshot was saved or new log-filter inspection made.

The November 20 V7.5.3 LONG_TARGET_EXIT at 10:00:06 shows schema 2.0.0,
strategy 7.5.3, instance research-1, action EXIT, direction LONG, quantity 1,
planned stop/target 363/726 ticks and null expiration. This specific long-target
log example is now observed; earlier wholly-unverified wording is historical.
Channel receipt and exhaustive lifecycle coverage remain unverified.

Selected expanded V7.4.2 examples:

| Date/time | Event | Action / quantity / price / position |
| --- | --- | --- |
| Nov 19 09:50 | LONG_ENTRY | buy / 1 / 27811.00 / 1 |
| Nov 19 09:54:20 | LONG_STOP_EXIT | sell / 1 / 27713.75 / 0 |
| Nov 19 12:03:46 | SHORT_TARGET_EXIT | buy / 1 / 26773.25 / 0 |
| Nov 20 09:55 | LONG_ENTRY | buy / 1 / 26364.25 / 1 |
| Nov 20 13:05 | SHORT_ENTRY | sell / 1 / 25540.25 / -1 |
| Nov 20 13:55:03 | SHORT_STOP_EXIT | buy / 1 / 25683.50 / 0 |

## Inventory reconciliation and limits

The list initially retained old strategy trigger dates conflicting with newer
log rows. A normal reload reconciled those dates and revealed a newer LSM SHORT
timestamp. This is consistent with a stale browser view; root cause is unproven.
All four original replacement alerts remained Active after reload. Both
strategies' latest triggers were November 20 15:50. LSM SHORT advanced to
November 18 13:01: **inventory timestamp only**, with no event row, expanded
message, reference levels or notification receipt inspected. LSM LONG still
had no latest-trigger time; its end-to-end delivery remains **PENDING**, not failed.

Push, sound, browser-toast receipt, devices, per-event attribution, original
arrival times and latency for newly inspected events remain **UNVERIFIED**.
Earlier confirmations do not cover them. The November 18 09:59 long entry's
subsequent exit remains unresolved because that later November 18 history was
not inspected. Complete coverage since baseline, exhaustive paths, prior channel
limits and the unclassified November 16 V7.4.2 10:52:31 trigger remain unresolved.
Receiver deduplication/expiry enforcement and broker reconciliation remain
unverified; no external receiver is configured. No blanket delivery or
performance pass is claimed.

The chart showed one minute on the first pane and five on the second. No alerts
were recreated or paused, no settings/inputs/intervals changed, no log cleared
and no broker orders submitted. This weekend check was bounded retrospective
inspection, not continuous monitoring or a live signal-window test.
