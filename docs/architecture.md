# Architecture

## Overview

qmt-trade-server consists of two components that communicate over HTTP:

1. **Server** (`server/trade_server.py`) — Runs inside QMT's built-in Python environment
2. **Client** (`client/qmt_http_client.py`) — Runs in external Python

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        QMT Process                                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  trade_server.py (QMT Strategy)                                    │  │
│  │                                                                    │  │
│  │  init()                                                            │  │
│  │    ├── Get account ID from QMT framework                           │  │
│  │    ├── Create TCP server socket on 127.0.0.1:8964                  │  │
│  │    └── Start schedule_run() timer (100ms)                          │  │
│  │                                                                    │  │
│  │  _poll_socket() ← called every 100ms by schedule_run()             │  │
│  │    ├── accept() with 50ms timeout                                  │  │
│  │    ├── Parse HTTP request (method, path, headers, body)            │  │
│  │    ├── Route to handler                                            │  │
│  │    │   ├── /buy  → passorder(23, ...)                              │  │
│  │    │   ├── /sell → passorder(24, ...)                              │  │
│  │    │   ├── /cancel → cancel(...)                                   │  │
│  │    │   ├── /positions → get_trade_detail_data('position')          │  │
│  │    │   ├── /tick → ContextInfo.get_full_tick(...)                  │  │
│  │    │   └── ... (14 endpoints total)                                │  │
│  │    └── Send JSON response                                          │  │
│  │                                                                    │  │
│  │  Callbacks (order_callback, deal_callback, etc.)                   │  │
│  │    └── Push events to _event_queue                                 │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  QMT APIs used:                                                          │
│    passorder()        - Place orders                                     │
│    cancel()           - Cancel orders                                    │
│    get_trade_detail_data() - Query positions/orders/trades/account       │
│    get_last_order_id() - Get latest order ID                             │
│    get_sector_list()  - Sector data                                      │
│    get_stock_list_in_sector() - Sector stocks                            │
│    ContextInfo.get_full_tick()       - Real-time tick                    │
│    ContextInfo.get_instrument_detail() - Instrument info                  │
│    ContextInfo.get_market_data_ex()  - K-line data                       │
│                                                                          │
└───────────────────────────────────────────────────────────────────────────┘
                    ▲
                    │ HTTP (127.0.0.1:8964)
                    │
┌───────────────────┴───────────────────────────────────────────────────────┐
│                        External Python Process                            │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  qmt_http_client.py                                                │  │
│  │                                                                    │  │
│  │  QMTHttpClient                                                     │  │
│  │    ├── buy() / sell() / cancel()    → POST /buy /sell /cancel      │  │
│  │    ├── get_positions() / get_asset() → GET /positions /asset       │  │
│  │    ├── get_full_tick()               → GET /tick                   │  │
│  │    ├── get_kline()                   → GET /kline                  │  │
│  │    ├── poll_events()                 → GET /events                 │  │
│  │    └── _request()                    → Raw HTTP with retries       │  │
│  │                                                                    │  │
│  │  Zero external dependencies (stdlib only: urllib, json, logging)   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Your application code                                                   │
│    └── Uses QMTHttpClient like xtquant                                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Event Polling (Callback Replacement)

In xtquant, you register callbacks (`XtQuantTraderCallback`) to receive order/deal/error notifications. In HTTP mode, QMT callbacks push events into a server-side queue, and the client polls this queue.

```
QMT Callback              Server Queue              Client
─────────────             ────────────              ──────
order_callback() ──push──► _event_queue ──poll──► poll_events()
deal_callback()  ──push──►   (max 500)   ──GET──►   returns events
orderError_callback() ────►               ──────►
position_callback() ──────►               ──────►
account_callback() ───────►               ──────►
```

### Usage Pattern

```python
import time

last_ts = 0
while True:
    events = client.poll_events(since=last_ts)
    for event in events:
        if event['type'] == 'deal':
            print(f"Deal: {event['data']['stock_code']}")
        last_ts = max(last_ts, event['time'])
    time.sleep(0.1)  # 100ms polling interval
```

## Tick Polling (vs subscribe_whole_quote)

xtquant's `subscribe_whole_quote()` pushes tick data via callback on every price change. In HTTP mode, the client polls `/tick` endpoint instead.

### Recommended Polling Intervals

| Use Case | Interval | Notes |
|----------|----------|-------|
| Monitoring | 1-5s | Low CPU, sufficient for display |
| Signal detection | 500ms-1s | Balance between latency and load |
| High-frequency | 200-500ms | Maximum recommended rate |

### Batch Polling

```python
# Poll multiple stocks in one request
ticks = client.get_full_tick(['000001.SZ', '600519.SH', '002475.SZ'])
for code, tick in ticks.items():
    print(f"{code}: {tick['lastPrice']}")
```

## HTTP Protocol Details

- **Transport**: TCP, HTTP/1.1
- **Binding**: `127.0.0.1:8964` (localhost only, not exposed to network)
- **Content-Type**: `application/json; charset=utf-8`
- **Connection**: `Connection: close` (no keep-alive)
- **Server timeout**: 50ms accept timeout, 5s request read timeout
- **Max events in queue**: 500 (oldest events dropped when exceeded)

## Error Handling

All endpoints return JSON with a `success` field:

```json
// Success
{"success": true, "data": {...}}

// Error
{"success": false, "error": "error message"}
```

HTTP status codes:
- `200` — Request processed (check `success` field for business logic errors)
- `400` — Invalid parameters
- `404` — Unknown endpoint
- `405` — Method not allowed
- `500` — Internal error (QMT API exception)

## Security Considerations

- Server binds to `127.0.0.1` only — not accessible from network
- No authentication — relies on localhost-only binding
- No encryption — HTTP, not HTTPS (acceptable for localhost)
- No rate limiting — client-side throttling recommended
