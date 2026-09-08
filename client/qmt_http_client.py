#coding:utf-8
"""
QMT HTTP Client - Trade and market data via HTTP
=================================================
Connects to trade_server.py running inside QMT's built-in Python environment.
Provides an API similar to xtquant for easy migration.

Architecture:
  This module (external Python) --HTTP--> trade_server.py (QMT built-in) --passorder--> Exchange

Usage:
  from client import QMTHttpClient
  client = QMTHttpClient()
  tick = client.get_full_tick(['000001.SZ'])
  result = client.buy('000001.SZ', volume=100, price=10.5)
"""

import json
import time
import logging
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class QMTHttpClient:
    """HTTP client for QMT trade_server, replacing direct xtquant access."""

    def __init__(self, host: str = '127.0.0.1', port: int = 8964,
                 timeout: float = 5.0, max_retries: int = 2):
        self.base_url = f'http://{host}:{port}'
        self.timeout = timeout
        self.max_retries = max_retries
        self._connected = False

    # ==================== HTTP Basics ====================

    def _request(self, method: str, path: str,
                 params: Optional[dict] = None,
                 body: Optional[dict] = None) -> dict:
        """Send HTTP request and return JSON response.

        Args:
            method: 'GET' or 'POST'
            path: URL path, e.g. '/tick'
            params: GET query parameters
            body: POST JSON request body

        Returns:
            Parsed JSON dict

        Raises:
            QMTHttpError: Request failed or server returned error
        """
        url = self.base_url + path
        if params:
            # Filter None values
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url += '?' + urllib.parse.urlencode(filtered)

        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=True).encode('utf-8')

        headers = {
            'Content-Type': 'application/json; charset=utf-8',
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    result = json.loads(raw.decode('utf-8'))
                    self._connected = True
                    return result
            except urllib.error.HTTPError as e:
                # HTTP error (4xx/5xx), read body for details
                try:
                    err_body = e.read().decode('utf-8', errors='replace')
                    err_data = json.loads(err_body)
                    last_error = QMTHttpError(
                        f"HTTP {e.code}: {err_data.get('error', err_body)}",
                        status_code=e.code,
                        response=err_data
                    )
                except Exception:
                    last_error = QMTHttpError(f"HTTP {e.code}", status_code=e.code)
                # Don't retry 4xx errors
                if 400 <= e.code < 500:
                    raise last_error
            except urllib.error.URLError as e:
                last_error = QMTHttpError(f"Connection failed: {e.reason}")
                self._connected = False
            except Exception as e:
                last_error = QMTHttpError(f"Request error: {e}")
                self._connected = False

            if attempt < self.max_retries:
                time.sleep(0.1 * (attempt + 1))  # Incremental backoff

        raise last_error

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        return self._request('GET', path, params=params)

    def _post(self, path: str, body: Optional[dict] = None) -> dict:
        return self._request('POST', path, body=body)

    @property
    def connected(self) -> bool:
        return self._connected

    # ==================== Health Check ====================

    def health(self) -> dict:
        """Health check."""
        return self._get('/health')

    def check_connection(self) -> bool:
        """Check if trade_server is reachable."""
        try:
            result = self.health()
            return result.get('status') == 'ok'
        except Exception:
            return False

    # ==================== Market Data (replaces xtdata) ====================

    def get_full_tick(self, code_list: List[str]) -> Optional[Dict[str, dict]]:
        """Get real-time tick data. Replaces xtdata.get_full_tick().

        Args:
            code_list: Stock codes, e.g. ['000001.SZ', '600830.SH']

        Returns:
            {code: tick_dict} or None
            tick_dict contains: lastPrice, bidPrice(list), askPrice(list),
                               bidVol(list), askVol(list), volume, amount, etc.
        """
        if not code_list:
            return {}
        try:
            result = self._get('/tick', {'codes': ','.join(code_list)})
            if result.get('success'):
                return result.get('data', {})
            else:
                logger.warning(f"get_full_tick failed: {result.get('error')}")
                return None
        except QMTHttpError as e:
            logger.error(f"get_full_tick error: {e}")
            return None

    def get_instrument_detail(self, stock_code: str) -> Optional[dict]:
        """Get instrument details. Replaces xtdata.get_instrument_detail().

        Returns:
            dict containing: UpStopPrice, DownStopPrice, PreClose, FloatVolume,
                       InstrumentName, VolumeMultiple, etc.
        """
        try:
            result = self._get('/instrument', {'code': stock_code})
            if result.get('success'):
                return result.get('data', {})
            else:
                logger.warning(f"get_instrument_detail failed: {result.get('error')}")
                return None
        except QMTHttpError as e:
            logger.error(f"get_instrument_detail error: {e}")
            return None

    def get_kline(self, stock_code: str, count: int = 10,
                  period: str = '1d') -> Optional[List[dict]]:
        """Get K-line data. Replaces xtdata.get_market_data() / get_local_data().

        Args:
            stock_code: Stock code
            count: Number of records
            period: Period '1d', '1m', '5m', etc.

        Returns:
            [{date, open, high, low, close, volume, amount, ...}, ...]
        """
        try:
            result = self._get('/kline', {
                'stock': stock_code,
                'count': str(count),
                'period': period,
            })
            if result.get('success'):
                return result.get('data', [])
            else:
                logger.warning(f"get_kline failed: {result.get('error')}")
                return None
        except QMTHttpError as e:
            logger.error(f"get_kline error: {e}")
            return None

    def get_market_data(self, stock_list: List[str], period: str = '1d',
                        start_time: str = '', end_time: str = '',
                        count: int = -1, dividend_type: str = 'front') -> Optional[dict]:
        """Get market data (xtdata.get_market_data compatible interface).

        Note: trade_server's /kline only queries one stock at a time, so this
        loops through and merges. Return format differs from xtdata - callers
        need to adapt.

        Returns:
            {stock_code: [records...]} or None
        """
        actual_count = count if count > 0 else 100
        result = {}
        for code in stock_list:
            records = self.get_kline(code, count=actual_count, period=period)
            if records is not None:
                result[code] = records
        return result if result else None

    def get_sector_list(self, node: str = '') -> Optional[list]:
        """Get sector list. Replaces xtdata.get_sector_list()."""
        try:
            result = self._get('/sector_list', {'node': node})
            if result.get('success'):
                return result.get('data', [])
            return None
        except QMTHttpError as e:
            logger.error(f"get_sector_list error: {e}")
            return None

    def get_stock_list_in_sector(self, sector_name: str) -> Optional[List[str]]:
        """Get stocks in a sector. Replaces xtdata.get_stock_list_in_sector()."""
        try:
            result = self._get('/sector_stocks', {'sector': sector_name})
            if result.get('success'):
                return result.get('data', [])
            return None
        except QMTHttpError as e:
            logger.error(f"get_stock_list_in_sector error: {e}")
            return None

    # ==================== xtdata compatible but not directly supported ====================

    def download_history_data(self, stock_code: str, period: str = '1d',
                              start_time: str = '', end_time: str = '') -> bool:
        """Download history data (no-op in HTTP mode, trade_server reads local data)."""
        logger.debug(f"download_history_data no-op (HTTP mode): {stock_code}")
        return True

    def download_history_data2(self, stock_list: List[str], period: str = '1d',
                               start_time: str = '', end_time: str = '') -> bool:
        """Batch download history data (no-op in HTTP mode)."""
        logger.debug(f"download_history_data2 no-op (HTTP mode): {len(stock_list)} stocks")
        return True

    def subscribe_quote(self, code: str, period: str = 'tick',
                        callback=None) -> int:
        """Subscribe to quotes (real-time push not supported in HTTP mode, returns -1).

        In HTTP mode, use get_full_tick() polling instead.
        """
        logger.warning(f"subscribe_quote not supported in HTTP mode, use get_full_tick polling: {code}")
        return -1

    def subscribe_whole_quote(self, code_list: List[str], callback=None) -> int:
        """Whole quote subscription (not supported in HTTP mode, returns -1)."""
        logger.warning(f"subscribe_whole_quote not supported in HTTP mode, use get_full_tick polling")
        return -1

    def unsubscribe_quote(self, seq: int) -> bool:
        """Unsubscribe (no-op in HTTP mode)."""
        return True

    # ==================== Trading (replaces XtQuantTrader) ====================

    def buy(self, stock_code: str, volume: int, price: float = 0,
            price_type: int = 11, strategy_name: str = 'default',
            order_remark: str = '') -> Tuple[bool, str]:
        """Place buy order. Replaces XtQuantTrader.order_stock(..., STOCK_BUY, ...).

        Args:
            stock_code: Stock code
            volume: Volume (shares)
            price: Price (limit price when price_type=11)
            price_type: Price type, default 11=limit (FIX_PRICE)
            strategy_name: Strategy name
            order_remark: Order remark

        Returns:
            (success, order_id) order_id is string
        """
        try:
            result = self._post('/buy', {
                'stock_code': stock_code,
                'volume': volume,
                'price': price,
                'price_type': price_type,
                'strategy_name': strategy_name,
                'order_remark': order_remark,
            })
            if result.get('success'):
                order_id = str(result.get('order_id', ''))
                logger.info(f"Buy order placed: {stock_code} {volume} shares @ {price:.2f} order_id={order_id}")
                return True, order_id
            else:
                logger.error(f"Buy order failed: {stock_code} - {result.get('error')}")
                return False, ''
        except QMTHttpError as e:
            logger.error(f"Buy order error: {stock_code} - {e}")
            return False, ''

    def sell(self, stock_code: str, volume: int, price: float = 0,
             price_type: int = 11, strategy_name: str = 'default',
             order_remark: str = '') -> Tuple[bool, str]:
        """Place sell order. Replaces XtQuantTrader.order_stock(..., STOCK_SELL, ...).

        Returns:
            (success, order_id)
        """
        try:
            result = self._post('/sell', {
                'stock_code': stock_code,
                'volume': volume,
                'price': price,
                'price_type': price_type,
                'strategy_name': strategy_name,
                'order_remark': order_remark,
            })
            if result.get('success'):
                order_id = str(result.get('order_id', ''))
                logger.info(f"Sell order placed: {stock_code} {volume} shares @ {price:.2f} order_id={order_id}")
                return True, order_id
            else:
                logger.error(f"Sell order failed: {stock_code} - {result.get('error')}")
                return False, ''
        except QMTHttpError as e:
            logger.error(f"Sell order error: {stock_code} - {e}")
            return False, ''

    def cancel(self, order_id: str) -> bool:
        """Cancel order. Replaces XtQuantTrader.cancel_order_stock().

        Args:
            order_id: Order ID (string)

        Returns:
            Success flag
        """
        try:
            result = self._post('/cancel', {'order_id': str(order_id)})
            return result.get('success', False)
        except QMTHttpError as e:
            logger.error(f"Cancel order error: order_id={order_id} - {e}")
            return False

    # ==================== Query Operations ====================

    def get_positions(self) -> List[dict]:
        """Query positions.

        Returns:
            [{stock_code, m_strInstrumentID, m_strExchangeID,
              m_nVolume, m_nCanUseVolume, m_dCostPrice, ...}, ...]
        """
        try:
            result = self._get('/positions')
            if result.get('success'):
                return result.get('positions', [])
            logger.warning(f"get_positions failed: {result.get('error')}")
            return []
        except QMTHttpError as e:
            logger.error(f"get_positions error: {e}")
            return []

    def get_asset(self) -> Optional[dict]:
        """Query account asset.

        Returns:
            dict containing: m_dAvailable (available cash), m_dBalance (total assets),
                       m_dFrozenCash (frozen cash), m_dStockMarket (stock market value), etc.
        """
        try:
            result = self._get('/asset')
            if result.get('success'):
                return result.get('asset')
            logger.warning(f"get_asset failed: {result.get('error')}")
            return None
        except QMTHttpError as e:
            logger.error(f"get_asset error: {e}")
            return None

    def get_orders(self, cancelable_only: bool = False) -> List[dict]:
        """Query orders.

        Args:
            cancelable_only: Whether to return only cancelable orders

        Returns:
            [{stock_code, m_nOrderStatus, m_nVolume, m_dPrice, ...}, ...]
            m_nOrderStatus: 49=not reported, 50=pending, 55=reported, 54=cancelled, 56=partial, 57=filled
        """
        try:
            params = {}
            if cancelable_only:
                params['cancelable_only'] = '1'
            result = self._get('/orders', params if params else None)
            if result.get('success'):
                return result.get('orders', [])
            logger.warning(f"get_orders failed: {result.get('error')}")
            return []
        except QMTHttpError as e:
            logger.error(f"get_orders error: {e}")
            return []

    def get_trades(self) -> List[dict]:
        """Query trades/deals.

        Returns:
            [{stock_code, m_dPrice, m_nVolume, m_dTradedAmount, ...}, ...]
        """
        try:
            result = self._get('/trades')
            if result.get('success'):
                return result.get('trades', [])
            logger.warning(f"get_trades failed: {result.get('error')}")
            return []
        except QMTHttpError as e:
            logger.error(f"get_trades error: {e}")
            return []

    # ==================== Event Polling (replaces XtQuantTraderCallback) ====================

    def poll_events(self, since: float = 0) -> List[dict]:
        """Poll callback events. Replaces XtQuantTraderCallback push mode.

        Args:
            since: Timestamp, only return events after this time.
                   0 = return all events and clear queue.

        Returns:
            [{type, data, time, datetime}, ...]
            type: 'order' | 'deal' | 'error' | 'position' | 'account'
            data: Event details dict (contains m_* fields and stock_code)
            time: Unix timestamp
            datetime: Readable time string 'HH:MM:SS.mmm'
        """
        try:
            params = {}
            if since > 0:
                params['since'] = str(since)
            result = self._get('/events', params if params else None)
            if result.get('success'):
                return result.get('events', [])
            return []
        except QMTHttpError as e:
            logger.error(f"poll_events error: {e}")
            return []

    # ==================== Constants (xtconstant compatible) ====================
    # passorder operation codes (used internally by trade_server, buy/sell methods handle this)
    _OP_BUY = 23
    _OP_SELL = 24

    # xtconstant trading direction constants (for comparing direction field in events/trades)
    STOCK_BUY = 47    # Trade direction = buy
    STOCK_SELL = 48   # Trade direction = sell

    # xtconstant price type constants
    FIX_PRICE = 11    # Limit price
    LATEST_PRICE = 5  # Latest price


class QMTHttpError(Exception):
    """QMT HTTP request exception."""

    def __init__(self, message: str, status_code: int = 0,
                 response: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
