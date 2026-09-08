# API Reference

## Endpoints

### POST /buy — Place Buy Order

**Request Body:**
```json
{
    "stock_code": "000001.SZ",
    "volume": 100,
    "price": 10.50,
    "price_type": 11,
    "strategy_name": "default",
    "order_remark": "my order"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| stock_code | string | Yes | - | Stock code (e.g. `000001.SZ`) |
| volume | int | Yes | - | Volume in shares (must be > 0) |
| price | float | No | 0 | Limit price (used when price_type=11) |
| price_type | int | No | 11 | 11=limit, 5=latest price |
| strategy_name | string | No | `"default"` | Strategy name |
| order_remark | string | No | `""` | Order remark |

**Response:**
```json
{
    "success": true,
    "order_id": "12345",
    "stock_code": "000001.SZ",
    "volume": 100,
    "price": 10.50
}
```

---

### POST /sell — Place Sell Order

Same parameters as `/buy`.

---

### POST /cancel — Cancel Order

**Request Body:**
```json
{
    "order_id": "12345"
}
```

**Response:**
```json
{
    "success": true,
    "order_id": "12345"
}
```

---

### GET /positions — Query Positions

**Response:**
```json
{
    "success": true,
    "positions": [
        {
            "stock_code": "000001.SZ",
            "m_strInstrumentID": "000001",
            "m_strExchangeID": "SZ",
            "m_nVolume": 1000,
            "m_nCanUseVolume": 1000,
            "m_dCostPrice": 10.50,
            "m_dStockMarket": 11000.0
        }
    ]
}
```

Key fields (all prefixed with `m_` from QMT):
- `m_nVolume` — Total volume
- `m_nCanUseVolume` — Available to sell (T+1 settlement)
- `m_dCostPrice` — Average cost price
- `m_dStockMarket` — Current market value
- `m_dProfit` — Unrealized P&L

---

### GET /asset — Query Account Asset

**Response:**
```json
{
    "success": true,
    "asset": {
        "m_dAvailable": 50000.0,
        "m_dBalance": 100000.0,
        "m_dFrozenCash": 5000.0,
        "m_dStockMarket": 45000.0,
        "m_dFrozenMargin": 0.0
    }
}
```

Key fields:
- `m_dAvailable` — Available cash for trading
- `m_dBalance` — Total account balance
- `m_dFrozenCash` — Cash frozen by pending orders
- `m_dStockMarket` — Total stock market value

---

### GET /orders — Query Orders

**Parameters:**
- `cancelable_only=1` — Only return orders that can be cancelled

**Response:**
```json
{
    "success": true,
    "orders": [
        {
            "stock_code": "000001.SZ",
            "m_strOrderSysID": "12345",
            "m_nOrderStatus": 55,
            "m_nVolume": 100,
            "m_dPrice": 10.50,
            "m_dTradedVolume": 0,
            "m_dTradedPrice": 0
        }
    ]
}
```

Order status codes:
| Code | Status | Cancelable |
|------|--------|------------|
| 49 | Not reported (未报) | Yes |
| 50 | Pending report (待报) | Yes |
| 55 | Reported (已报) | Yes |
| 54 | Cancelled (已撤) | No |
| 56 | Partial fill (部成) | Yes |
| 57 | Full fill (已成) | No |

---

### GET /trades — Query Trades/Deals

**Response:**
```json
{
    "success": true,
    "trades": [
        {
            "stock_code": "000001.SZ",
            "m_dPrice": 10.50,
            "m_nVolume": 100,
            "m_dTradedAmount": 1050.0,
            "m_strOrderSysID": "12345"
        }
    ]
}
```

---

### GET /events — Poll Callback Events

**Parameters:**
- `since=<timestamp>` — Only return events after this Unix timestamp

**Response:**
```json
{
    "success": true,
    "events": [
        {
            "type": "order",
            "data": {
                "stock_code": "000001.SZ",
                "m_nOrderStatus": 55,
                "m_strOrderSysID": "12345"
            },
            "time": 1700000000.123,
            "datetime": "10:30:00.123"
        }
    ],
    "count": 1
}
```

Event types: `order`, `deal`, `error`, `position`, `account`

**Note:** When `since` is 0 or omitted, all events are returned and the queue is cleared.

---

### GET /health — Health Check

**Response:**
```json
{
    "status": "ok",
    "account": "12345678",
    "time": "10:30:00",
    "events": 5,
    "poll_count": 12345
}
```

---

### GET /tick — Real-time Tick Data

**Parameters:**
- `codes` — Comma-separated stock codes (required)

**Response:**
```json
{
    "success": true,
    "count": 1,
    "data": {
        "000001.SZ": {
            "lastPrice": 10.50,
            "bidPrice": [10.49, 10.48, 10.47, 10.46, 10.45],
            "askPrice": [10.50, 10.51, 10.52, 10.53, 10.54],
            "bidVol": [1000, 2000, 3000, 4000, 5000],
            "askVol": [500, 1500, 2500, 3500, 4500],
            "volume": 1000000,
            "amount": 10500000.0,
            "open": 10.30,
            "high": 10.60,
            "low": 10.25,
            "preClose": 10.28
        }
    }
}
```

---

### GET /instrument — Instrument Detail

**Parameters:**
- `code` — Stock code (required)

**Response:**
```json
{
    "success": true,
    "code": "000001.SZ",
    "data": {
        "InstrumentName": "平安银行",
        "UpStopPrice": 11.31,
        "DownStopPrice": 9.25,
        "PreClose": 10.28,
        "FloatVolume": 1940689200,
        "VolumeMultiple": 100
    }
}
```

---

### GET /kline — K-line Data

**Parameters:**
- `stock` — Stock code (default: `000001.SZ`)
- `count` — Number of records (default: 10)
- `period` — Period: `1d`, `1m`, `5m`, `15m`, `30m`, `60m` (default: `1d`)

**Response:**
```json
{
    "success": true,
    "stock": "000001.SZ",
    "count": 3,
    "data": [
        {
            "date": "2024-01-15",
            "open": 10.30,
            "high": 10.60,
            "low": 10.25,
            "close": 10.50,
            "volume": 1000000,
            "amount": 10500000.0
        }
    ]
}
```

---

### GET /sector_list — Sector List

**Parameters:**
- `node` — Sector node path (default: `""` for top-level)

**Response:**
```json
{
    "success": true,
    "data": [["沪深A股", "沪深B股", "..."], ["..."]]
}
```

---

### GET /sector_stocks — Stocks in Sector

**Parameters:**
- `sector` — Sector name (required, e.g. `沪深A股`)

**Response:**
```json
{
    "success": true,
    "sector": "沪深A股",
    "count": 5000,
    "data": ["000001.SZ", "000002.SZ", "..."]
}
```

---

## Client API

### Constructor

```python
QMTHttpClient(host='127.0.0.1', port=8964, timeout=5.0, max_retries=2)
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `health()` | dict | Health check |
| `check_connection()` | bool | Check if server is reachable |
| `buy(stock_code, volume, price, ...)` | (bool, str) | Place buy order |
| `sell(stock_code, volume, price, ...)` | (bool, str) | Place sell order |
| `cancel(order_id)` | bool | Cancel order |
| `get_positions()` | List[dict] | Query positions |
| `get_asset()` | Optional[dict] | Query account asset |
| `get_orders(cancelable_only)` | List[dict] | Query orders |
| `get_trades()` | List[dict] | Query trades |
| `poll_events(since)` | List[dict] | Poll callback events |
| `get_full_tick(code_list)` | Optional[Dict] | Get real-time tick |
| `get_instrument_detail(code)` | Optional[dict] | Get instrument info |
| `get_kline(code, count, period)` | Optional[List] | Get K-line data |
| `get_market_data(stock_list, ...)` | Optional[dict] | Batch K-line (loops internally) |
| `get_sector_list(node)` | Optional[list] | Get sector list |
| `get_stock_list_in_sector(name)` | Optional[List] | Get stocks in sector |

### Constants

```python
QMTHttpClient.STOCK_BUY = 47      # Buy direction
QMTHttpClient.STOCK_SELL = 48     # Sell direction
QMTHttpClient.FIX_PRICE = 11      # Limit price
QMTHttpClient.LATEST_PRICE = 5    # Latest price
```

### Exception

```python
from client import QMTHttpError

try:
    client.buy('000001.SZ', volume=100, price=10.5)
except QMTHttpError as e:
    print(f"Error: {e.message}, status: {e.status_code}")
```
