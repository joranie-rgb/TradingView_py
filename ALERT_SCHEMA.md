# Futures V7.5.2 alert payload schema

V7.5.2 emits JSON objects from both `alert()` calls and
order-fill alert fields. The schema version is `2.0.0`; changing a field's name,
type, required status, or meaning requires a new schema version. Strategy version
and schema version are independent.

## Migration from schema 1

Schema 2 adds required `instance_id` and `configuration_id` fields and changes
event identity. Update strict receivers to accept schema `2.0.0` and strategy
`7.5.2` before recreating TradingView alerts. Do not mix old and new alert
snapshots for the same deployment. Deduplicate the entire opaque `event_id`;
do not parse it into a fixed number of colon-delimited fields.

Set **Alert Instance ID** uniquely per account/deployment, and change it when
changing Strategy Properties. Labels must contain 1 to 64 ASCII letters, digits,
underscores, or hyphens; spaces, control characters, and separators are rejected.
This validation does not authenticate a sender. Behavior inputs are automatically
encoded into the configuration token.

The canonical configuration token ensures different input configurations get different
IDs even when their instance labels match. The token is not a cryptographic hash
or an authentication mechanism. Identical deployments sharing both the instance
label and inputs intentionally share identities; do not reuse that namespace
across accounts. Strategy Properties are not fully introspectable from Pine
and therefore must be namespaced by the operator's instance label.

## JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.invalid/tradingview/futures-alert-2.0.0.schema.json",
  "title": "Futures strategy alert",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version", "strategy_version", "event_id", "instance_id", "configuration_id", "event", "symbol",
    "exchange", "timeframe", "signal_timestamp", "expiration_timestamp",
    "action", "direction", "quantity", "planned_bracket_ticks",
    "risk_day_id", "administrative_reason"
  ],
  "properties": {
    "schema_version": { "const": "2.0.0" },
    "strategy_version": { "const": "7.5.2" },
    "event_id": { "type": "string", "minLength": 1 },
    "instance_id": { "type": "string", "minLength": 1 },
    "configuration_id": { "type": "string", "minLength": 1 },
    "event": {
      "enum": [
        "LONG_ENTRY", "SHORT_ENTRY", "LONG_STOP_EXIT", "LONG_TARGET_EXIT",
        "SHORT_STOP_EXIT", "SHORT_TARGET_EXIT", "DAILY_LOSS_EXIT",
        "MAXIMUM_DRAWDOWN_EXIT", "SESSION_EXIT"
      ]
    },
    "symbol": { "type": "string", "minLength": 1 },
    "exchange": { "type": "string", "minLength": 1 },
    "timeframe": { "type": "string", "minLength": 1 },
    "signal_timestamp": { "type": "integer", "description": "Unix milliseconds" },
    "expiration_timestamp": {
      "type": ["integer", "null"],
      "description": "Exclusive Unix-millisecond freshness boundary; null for resting protective orders"
    },
    "action": { "enum": ["ENTER", "EXIT"] },
    "direction": { "enum": ["LONG", "SHORT", "FLAT"] },
    "quantity": { "type": "number", "minimum": 0 },
    "planned_bracket_ticks": {
      "type": "object",
      "additionalProperties": false,
      "required": ["stop", "target"],
      "properties": {
        "stop": { "type": ["integer", "null"], "minimum": 1 },
        "target": { "type": ["integer", "null"], "minimum": 1 }
      }
    },
    "risk_day_id": {
      "type": "integer",
      "description": "Unix-millisecond start of the risk day in the configured session timezone"
    },
    "administrative_reason": {
      "enum": [null, "DAILY_LOSS_LIMIT", "MAXIMUM_DRAWDOWN", "SESSION_CUTOFF"]
    }
  }
}
```

## Field and event semantics

- `event_id` is deterministic: strategy version, instance ID, canonical input
  configuration, TradingView ticker ID, timeframe, submission timestamp, and
  event name. The submission timestamp makes
  a re-entry from a still-valid technical setup a distinct logical event. Treat
  the same ID received from `alert()` and an order-fill alert as the same logical
  event, not two orders.
- Entry `signal_timestamp` identifies the original technical setup bar, even when
  execution gates delay submission within the configured validity window. Its
  `expiration_timestamp` is one chart interval after the submission bar closes,
  giving the receiver a bounded acceptance window. Receivers must reject an
  entry at or after that instant.
- Protective-exit messages use the bar close at which the active bracket was
  last submitted as the signal timestamp. Their expiration is `null` because a
  resting protective order remains valid until replaced, filled, or cancelled.
- Administrative messages use the triggering bar close for both timestamps and
  carry a non-null reason. A flat `SESSION_EXIT` notification has direction
  `FLAT` and quantity `0`.
- Tick values are distances from the actual entry fill, not absolute prices.
  They can be `null` when no entry plan exists.
- Timestamps and IDs describe strategy intent; they are not broker execution
  timestamps or broker order identifiers.
- String fields are JSON-escaped by the strategy before serialization, including
  symbol metadata supplied by TradingView.

## Receiver requirements

The payload is not an authentication mechanism. A production receiver must use
authenticated transport or a shared secret outside this body, validate the exact
schema and allowed strategy version, reject unknown fields, deduplicate on
`event_id`, and reject stale or expired entry messages. It must independently
reapply trading-session, symbol, direction, quantity, position, daily-trade,
daily-loss, and exposure limits before placing an order. Persist the relationship
between event IDs and broker order IDs, reconcile acknowledgements, rejections,
partial fills and fills, and make retries idempotent. Never assume a TradingView
alert proves that an emulator order filled at a broker.

For a TradingView strategy alert, use `{{strategy.order.alert_message}}` for order
fills and enable `alert()` calls if immediate confirmed-bar intent notifications
are also wanted. Enabling both intentionally produces the same entry or
administrative `event_id`; the receiver's idempotency layer must decide which
message is actionable for its workflow.
