#coding:gbk
"""
QMT Built-in Strategy - Trade HTTP Server
==========================================
Runs inside QMT's built-in Python environment.
Exposes HTTP endpoints for external Python to execute trades and query market data.

Architecture:
  External Python --HTTP--> This strategy (server) --passorder/cancel--> Exchange
  schedule_run() polls socket every 100ms

Endpoints:
  POST /buy            Place buy order
  POST /sell           Place sell order
  POST /cancel         Cancel order
  GET  /positions      Query positions
  GET  /asset          Query account asset
  GET  /orders         Query orders (?cancelable_only=1)
  GET  /trades         Query trades/deals
  GET  /events         Poll callback events (?since=<timestamp>)
  GET  /health         Health check
  GET  /tick           Real-time tick (?codes=000001.SZ,600830.SH)
  GET  /instrument     Instrument detail (?code=000001.SZ)
  GET  /kline          K-line OHLCV (?stock=000001.SZ&count=10&period=1d)
  GET  /sector_list    Sector list (?node=)
  GET  /sector_stocks  Stocks in sector (?sector=name)

Usage:
  1. Copy this file to QMT's strategy directory
  2. Create a new strategy in QMT and load this file
  3. Run the strategy - it will start an HTTP server on 127.0.0.1:8964
  4. Use the Python client to connect from external Python
"""

import json
import time
import socket
import select
import traceback
import datetime as dt
from datetime import datetime
try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

# ==================== Config ====================
HTTP_HOST = '127.0.0.1'
HTTP_PORT = 8964
ACCOUNT_TYPE = 'stock'

# ==================== Shared State ====================
_event_queue = []
_MAX_EVENTS = 500
_account_id = ''
_server_socket = None
_poll_count = 0
_accept_count = 0
_ContextInfo = None  # Saved from init() and updated in _poll_socket() for use in request handlers


def _obj_to_dict(obj):
    """Convert QMT data object (m_xxx attributes) to dict."""
    result = {}
    for attr in dir(obj):
        if not attr.startswith('m_'):
            continue
        try:
            val = getattr(obj, attr)
            if isinstance(val, (int, float, str, bool, type(None))):
                result[attr] = val
        except Exception:
            pass
    return result


def _push_event(event_type, data):
    """Push a callback event into the queue."""
    event = {
        'type': event_type,
        'data': data,
        'time': time.time(),
        'datetime': datetime.now().strftime('%H:%M:%S.%f')[:-3]
    }
    _event_queue.append(event)
    if len(_event_queue) > _MAX_EVENTS:
        del _event_queue[:len(_event_queue) - _MAX_EVENTS]


def _safe_str(val):
    """Safely convert any value to string."""
    try:
        if isinstance(val, bytes):
            try:
                return val.decode('utf-8')
            except UnicodeDecodeError:
                return val.decode('gbk', errors='replace')
        return str(val)
    except Exception:
        return ''


def _get_last_order_id_safe():
    """Safely get the latest order ID."""
    try:
        result = get_last_order_id(_account_id, 'stock', 'order')
        if result:
            if isinstance(result, list) and len(result) > 0:
                return _safe_str(result[-1])
            return _safe_str(result)
    except Exception:
        pass
    return ''


# ==================== HTTP Server ====================

def _init_server():
    """Initialize the server socket (blocking with timeout)."""
    global _server_socket
    try:
        _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _server_socket.bind((HTTP_HOST, HTTP_PORT))
        _server_socket.listen(5)
        _server_socket.settimeout(0.05)  # 50ms timeout for accept()
        print('[HTTP] Server listening on %s:%d' % (HTTP_HOST, HTTP_PORT))
        return True
    except Exception as e:
        print('[HTTP] Init FAILED: %s' % _safe_str(e))
        traceback.print_exc()
        return False


def _poll_socket(ContextInfo):
    """Called by schedule_run() every 100ms. Accepts and handles connections."""
    global _poll_count, _accept_count, _ContextInfo

    # Update _ContextInfo with the current ContextInfo from schedule_run
    _ContextInfo = ContextInfo

    _poll_count += 1
    if _poll_count % 50 == 1:
        print('[POLL] count=%d accepts=%d' % (_poll_count, _accept_count))

    if not _server_socket:
        return

    try:
        # accept() with 50ms timeout - blocks briefly then returns if no connection
        client_socket, addr = _server_socket.accept()
        _accept_count += 1

        # Handle request
        try:
            _handle_request(client_socket)
        except Exception as e:
            print('[HTTP] Request error: %s' % _safe_str(e))
        finally:
            try:
                client_socket.close()
            except Exception:
                pass

    except socket.timeout:
        # No connection waiting - normal
        pass
    except Exception as e:
        print('[HTTP] Accept error: %s' % _safe_str(e))


def _send_response(client_socket, response_data, status_code=200):
    """Send HTTP JSON response on the client socket."""
    response_body = json.dumps(response_data, ensure_ascii=True, default=_safe_str).encode('utf-8')
    status_text = {200: 'OK', 400: 'Bad Request', 404: 'Not Found', 500: 'Internal Error'}.get(status_code, 'OK')

    response = 'HTTP/1.1 %d %s\r\n' % (status_code, status_text)
    response += 'Content-Type: application/json; charset=utf-8\r\n'
    response += 'Content-Length: %d\r\n' % len(response_body)
    response += 'Connection: close\r\n'
    response += '\r\n'

    send_data = response.encode('utf-8') + response_body
    send_deadline = time.time() + 3.0
    sent = 0
    while sent < len(send_data) and time.time() < send_deadline:
        try:
            n = client_socket.send(send_data[sent:])
            if n > 0:
                sent += n
            else:
                time.sleep(0.01)
        except Exception:
            time.sleep(0.01)


def _handle_request(client_socket):
    """Handle a single HTTP request on the client socket."""
    # Use EXPLICIT non-blocking mode + polling
    try:
        client_socket.setblocking(False)
    except Exception:
        pass

    # Poll for data with busy-wait
    request_data = b''
    deadline = time.time() + 5.0

    while time.time() < deadline:
        try:
            chunk = client_socket.recv(4096)
            if chunk:
                request_data += chunk
                if b'\r\n\r\n' in request_data:
                    break
            elif chunk == b'':
                # Connection closed
                break
        except Exception:
            # BlockingIOError / socket.error = no data yet in non-blocking mode
            pass
        time.sleep(0.01)  # 10ms sleep to avoid busy-spinning

    if not request_data:
        return

    # Parse headers
    header_end = request_data.find(b'\r\n\r\n')
    if header_end < 0:
        return

    headers = request_data[:header_end].decode('utf-8', errors='replace')

    # Parse Content-Length
    content_length = 0
    for line in headers.split('\r\n'):
        if line.lower().startswith('content-length:'):
            try:
                content_length = int(line.split(':')[1].strip())
            except ValueError:
                pass
            break

    # Read body if needed
    body_data = request_data[header_end + 4:]
    body_deadline = time.time() + 3.0
    while len(body_data) < content_length and time.time() < body_deadline:
        try:
            chunk = client_socket.recv(4096)
            if chunk:
                body_data += chunk
            elif chunk == b'':
                break
        except Exception:
            pass
        time.sleep(0.01)

    # Parse JSON body
    body_json = {}
    if body_data:
        try:
            body_json = json.loads(body_data.decode('utf-8'))
        except Exception:
            pass

    # Parse request line
    request_line = headers.split('\r\n')[0]
    parts = request_line.split(' ', 2)
    if len(parts) >= 2:
        method = parts[0]
        full_path = parts[1]
        path = full_path.split('?')[0]
    else:
        method = 'GET'
        path = '/health'
        full_path = '/health'

    # Route to handler (with safety net)
    try:
        response_data = _route_request(method, path, body_json, full_path)
    except Exception as e:
        print('[HTTP] Handler crashed: %s' % _safe_str(e))
        traceback.print_exc()
        response_data = {'success': False, 'error': 'internal error: %s' % _safe_str(e)}
        status_code = 500
        _send_response(client_socket, response_data, status_code)
        return

    # Handle tuple (data, status)
    status_code = 200
    if isinstance(response_data, tuple):
        response_data, status_code = response_data

    _send_response(client_socket, response_data, status_code)


# ==================== Request Router ====================

def _route_request(method, path, body, full_path=None):
    """Route request to handler."""
    if method == 'GET':
        if path == '/health':
            return _handle_health()
        elif path == '/positions':
            return _handle_positions()
        elif path == '/asset':
            return _handle_asset()
        elif path == '/orders':
            return _handle_orders(full_path or path)
        elif path == '/trades':
            return _handle_trades()
        elif path == '/events':
            return _handle_events(full_path or path)
        elif path.startswith('/kline'):
            return _handle_kline(full_path or path)
        elif path == '/tick':
            return _handle_tick(full_path or path)
        elif path == '/instrument':
            return _handle_instrument(full_path or path)
        elif path == '/sector_list':
            return _handle_sector_list(full_path or path)
        elif path == '/sector_stocks':
            return _handle_sector_stocks(full_path or path)
        else:
            return {'error': 'unknown path'}, 404
    elif method == 'POST':
        if path == '/buy':
            return _handle_buy(body)
        elif path == '/sell':
            return _handle_sell(body)
        elif path == '/cancel':
            return _handle_cancel(body)
        else:
            return {'error': 'unknown path'}, 404
    return {'error': 'method not allowed'}, 405


def _parse_query(path):
    """Parse query string from path into a dict (URL-decoded)."""
    params = {}
    if '?' in path:
        query = path.split('?', 1)[1]
        for p in query.split('&'):
            if '=' in p:
                k, v = p.split('=', 1)
                params[unquote(k)] = unquote(v)
    return params


# ==================== Request Handlers ====================

def _handle_buy(body):
    stock_code = _safe_str(body.get('stock_code', ''))
    volume = int(body.get('volume', 0))
    price = float(body.get('price', 0))
    pr_type = int(body.get('price_type', 11))
    strategy_name = _safe_str(body.get('strategy_name', 'default'))
    order_remark = _safe_str(body.get('order_remark', ''))

    if not stock_code or volume <= 0:
        return {'success': False, 'error': 'invalid params'}, 400

    try:
        passorder(23, 1101, _account_id, stock_code, pr_type, price, volume,
                  strategy_name, 2, order_remark, _ContextInfo)
        time.sleep(0.05)
        order_id = _get_last_order_id_safe()
        print('[BUY] %s vol=%d price=%.2f oid=%s' % (stock_code, volume, price, order_id))
        return {'success': True, 'order_id': order_id, 'stock_code': stock_code, 'volume': volume, 'price': price}
    except Exception as e:
        print('[BUY] Error: %s' % _safe_str(e))
        traceback.print_exc()
        return {'success': False, 'error': _safe_str(e)}, 500


def _handle_sell(body):
    stock_code = _safe_str(body.get('stock_code', ''))
    volume = int(body.get('volume', 0))
    price = float(body.get('price', 0))
    pr_type = int(body.get('price_type', 11))
    strategy_name = _safe_str(body.get('strategy_name', 'default'))
    order_remark = _safe_str(body.get('order_remark', ''))

    if not stock_code or volume <= 0:
        return {'success': False, 'error': 'invalid params'}, 400

    try:
        passorder(24, 1101, _account_id, stock_code, pr_type, price, volume,
                  strategy_name, 2, order_remark, _ContextInfo)
        time.sleep(0.05)
        order_id = _get_last_order_id_safe()
        print('[SELL] %s vol=%d price=%.2f oid=%s' % (stock_code, volume, price, order_id))
        return {'success': True, 'order_id': order_id, 'stock_code': stock_code, 'volume': volume, 'price': price}
    except Exception as e:
        print('[SELL] Error: %s' % _safe_str(e))
        traceback.print_exc()
        return {'success': False, 'error': _safe_str(e)}, 500


def _handle_cancel(body):
    order_id = _safe_str(body.get('order_id', ''))
    if not order_id:
        return {'success': False, 'error': 'missing order_id'}, 400

    try:
        result = cancel(order_id, _account_id, ACCOUNT_TYPE, _ContextInfo)
        print('[CANCEL] oid=%s result=%s' % (order_id, result))
        return {'success': bool(result), 'order_id': order_id}
    except Exception as e:
        print('[CANCEL] Error: %s' % _safe_str(e))
        traceback.print_exc()
        return {'success': False, 'error': _safe_str(e)}, 500


def _handle_positions():
    try:
        positions = get_trade_detail_data(_account_id, ACCOUNT_TYPE, 'position')
        result = []
        if positions:
            for pos in positions:
                d = _obj_to_dict(pos)
                inst = d.get('m_strInstrumentID', '')
                exc = d.get('m_strExchangeID', '')
                if inst and exc:
                    d['stock_code'] = '%s.%s' % (_safe_str(inst), _safe_str(exc))
                result.append(d)
        return {'success': True, 'positions': result}
    except Exception as e:
        print('[POS] Error: %s' % _safe_str(e))
        return {'success': False, 'error': _safe_str(e)}


def _handle_health():
    """Health check endpoint."""
    return {
        'status': 'ok',
        'account': _account_id,
        'time': datetime.now().strftime('%H:%M:%S'),
        'events': len(_event_queue),
        'poll_count': _poll_count,
    }


def _handle_asset():
    """Query account asset."""
    try:
        accounts = get_trade_detail_data(_account_id, ACCOUNT_TYPE, 'account')
        if accounts and len(accounts) > 0:
            return {'success': True, 'asset': _obj_to_dict(accounts[0])}
        return {'success': False, 'error': 'no account data', 'raw': _safe_str(accounts)}
    except Exception as e:
        print('[ASSET] Error: %s' % _safe_str(e))
        return {'success': False, 'error': _safe_str(e)}


def _handle_orders(path=''):
    try:
        params = _parse_query(path)
        cancelable_only = params.get('cancelable_only', '0') in ('1', 'true', 'yes')
        # Cancelable statuses: 49=未报, 50=待报, 55=已报
        _cancelable = {49, 50, 55}

        orders = get_trade_detail_data(_account_id, ACCOUNT_TYPE, 'order')
        result = []
        if orders:
            for order in orders:
                d = _obj_to_dict(order)
                inst = d.get('m_strInstrumentID', '')
                exc = d.get('m_strExchangeID', '')
                if inst and exc:
                    d['stock_code'] = '%s.%s' % (_safe_str(inst), _safe_str(exc))
                if cancelable_only and d.get('m_nOrderStatus', 0) not in _cancelable:
                    continue
                result.append(d)
        return {'success': True, 'orders': result}
    except Exception as e:
        print('[ORDERS] Error: %s' % _safe_str(e))
        return {'success': False, 'error': _safe_str(e)}


def _handle_trades():
    try:
        trades = get_trade_detail_data(_account_id, ACCOUNT_TYPE, 'deal')
        result = []
        if trades:
            for trade in trades:
                d = _obj_to_dict(trade)
                inst = d.get('m_strInstrumentID', '')
                exc = d.get('m_strExchangeID', '')
                if inst and exc:
                    d['stock_code'] = '%s.%s' % (_safe_str(inst), _safe_str(exc))
                result.append(d)
        return {'success': True, 'trades': result}
    except Exception as e:
        print('[TRADES] Error: %s' % _safe_str(e))
        return {'success': False, 'error': _safe_str(e)}


def _handle_events(path=''):
    params = _parse_query(path)
    since = 0
    since_str = params.get('since', '')
    if since_str:
        try:
            since = float(since_str)
        except ValueError:
            pass

    if since > 0:
        events = [e for e in _event_queue if e['time'] > since]
    else:
        events = list(_event_queue)
        _event_queue.clear()
    return {'success': True, 'events': events, 'count': len(events)}


def _handle_kline(path):
    """Get K-line data. Usage: /kline?stock=000001.SZ&count=10&period=1d"""
    params = _parse_query(path)

    stock = params.get('stock', '000001.SZ')
    count = int(params.get('count', '10'))
    period = params.get('period', '1d')

    try:
        # Use ContextInfo.get_market_data_ex to get K-line data
        # Empty list [] means get all fields (open/high/low/close/volume/etc)
        data = _ContextInfo.get_market_data_ex(
            [], [stock],
            period=period,
            count=count,
            subscribe=False  # Use local data, no subscription needed
        )

        if data and stock in data:
            df = data[stock]
            # Convert DataFrame to list of dicts
            records = []
            for idx, row in df.iterrows():
                record = {'date': str(idx)}
                for col in df.columns:
                    val = row[col]
                    # Convert to Python native types
                    if hasattr(val, 'item'):
                        val = val.item()
                    record[col] = val
                records.append(record)
            return {'success': True, 'stock': stock, 'count': len(records), 'data': records}
        else:
            return {'success': False, 'error': 'no data', 'raw': _safe_str(data)}
    except Exception as e:
        print('[KLINE] Error: %s' % _safe_str(e))
        traceback.print_exc()
        return {'success': False, 'error': _safe_str(e)}


def _handle_tick(path):
    """GET /tick?codes=000001.SZ,600830.SH
    Returns real-time tick data (lastPrice, bid/ask 5-level, volume, etc.)"""
    params = _parse_query(path)
    codes_str = params.get('codes', '')
    if not codes_str:
        return {'success': False, 'error': 'missing codes param'}, 400

    code_list = [c.strip() for c in codes_str.split(',') if c.strip()]
    if not code_list:
        return {'success': False, 'error': 'empty code list'}, 400

    try:
        tick_data = _ContextInfo.get_full_tick(code_list)
        if tick_data:
            result = {}
            for code, data in tick_data.items():
                if isinstance(data, dict):
                    clean = {}
                    for k, v in data.items():
                        if hasattr(v, 'item'):
                            clean[k] = v.item()
                        elif isinstance(v, list):
                            clean[k] = [x.item() if hasattr(x, 'item') else x for x in v]
                        else:
                            clean[k] = v
                    result[code] = clean
                else:
                    result[code] = data
            return {'success': True, 'count': len(result), 'data': result}
        else:
            return {'success': False, 'error': 'no tick data', 'data': {}}
    except Exception as e:
        print('[TICK] Error: %s' % _safe_str(e))
        traceback.print_exc()
        return {'success': False, 'error': _safe_str(e)}, 500


def _handle_instrument(path):
    """GET /instrument?code=000001.SZ
    Returns instrument detail (UpStopPrice, DownStopPrice, PreClose, FloatVolume, etc.)"""
    params = _parse_query(path)
    code = params.get('code', '')
    if not code:
        return {'success': False, 'error': 'missing code param'}, 400

    try:
        detail = _ContextInfo.get_instrument_detail(code)
        if detail:
            clean = {}
            for k, v in detail.items():
                if hasattr(v, 'item'):
                    clean[k] = v.item()
                else:
                    clean[k] = v
            return {'success': True, 'code': code, 'data': clean}
        else:
            return {'success': False, 'error': 'no instrument data'}
    except Exception as e:
        print('[INSTRUMENT] Error: %s' % _safe_str(e))
        traceback.print_exc()
        return {'success': False, 'error': _safe_str(e)}, 500


def _handle_sector_list(path):
    """GET /sector_list?node=
    Returns sector list. node='' for top-level."""
    params = _parse_query(path)
    node = params.get('node', '')

    try:
        result = get_sector_list(node)
        if result:
            return {'success': True, 'data': result}
        else:
            return {'success': True, 'data': [[], []]}
    except Exception as e:
        print('[SECTOR_LIST] Error: %s' % _safe_str(e))
        traceback.print_exc()
        return {'success': False, 'error': _safe_str(e)}, 500


def _handle_sector_stocks(path):
    """GET /sector_stocks?sector=xxx
    Returns stock list in a sector."""
    params = _parse_query(path)
    sector = params.get('sector', '')
    if not sector:
        return {'success': False, 'error': 'missing sector param'}, 400

    try:
        stock_list = get_stock_list_in_sector(sector)
        if stock_list:
            return {'success': True, 'sector': sector, 'count': len(stock_list), 'data': stock_list}
        else:
            return {'success': True, 'sector': sector, 'count': 0, 'data': []}
    except Exception as e:
        print('[SECTOR_STOCKS] Error: %s' % _safe_str(e))
        traceback.print_exc()
        return {'success': False, 'error': _safe_str(e)}, 500


# ==================== QMT Callbacks ====================

def order_callback(ContextInfo, orderInfo):
    try:
        data = _obj_to_dict(orderInfo)
        inst = data.get('m_strInstrumentID', '')
        exc = data.get('m_strExchangeID', '')
        if inst and exc:
            data['stock_code'] = '%s.%s' % (_safe_str(inst), _safe_str(exc))
        _push_event('order', data)
        print('[CB] order %s status=%s' % (data.get('stock_code', ''), data.get('m_nOrderStatus', '')))
    except Exception as e:
        print('[CB ERROR] order_callback: %s' % _safe_str(e))


def deal_callback(ContextInfo, dealInfo):
    try:
        data = _obj_to_dict(dealInfo)
        inst = data.get('m_strInstrumentID', '')
        exc = data.get('m_strExchangeID', '')
        if inst and exc:
            data['stock_code'] = '%s.%s' % (_safe_str(inst), _safe_str(exc))
        _push_event('deal', data)
        print('[CB] deal %s price=%.2f vol=%d' % (data.get('stock_code', ''), data.get('m_dPrice', 0), data.get('m_nVolume', 0)))
    except Exception as e:
        print('[CB ERROR] deal_callback: %s' % _safe_str(e))


def orderError_callback(ContextInfo, orderErrorInfo):
    try:
        data = _obj_to_dict(orderErrorInfo)
        _push_event('error', data)
        print('[CB] error id=%s' % data.get('m_nErrorID', ''))
    except Exception as e:
        print('[CB ERROR] orderError_callback: %s' % _safe_str(e))


def position_callback(ContextInfo, positionInfo):
    try:
        data = _obj_to_dict(positionInfo)
        inst = data.get('m_strInstrumentID', '')
        exc = data.get('m_strExchangeID', '')
        if inst and exc:
            data['stock_code'] = '%s.%s' % (_safe_str(inst), _safe_str(exc))
        _push_event('position', data)
        print('[CB] position %s vol=%d' % (data.get('stock_code', ''), data.get('m_nVolume', 0)))
    except Exception as e:
        print('[CB ERROR] position_callback: %s' % _safe_str(e))


def account_callback(ContextInfo, accountInfo):
    try:
        data = _obj_to_dict(accountInfo)
        _push_event('account', data)
        print('[CB] account status=%s' % data.get('m_strStatus', ''))
    except Exception as e:
        print('[CB ERROR] account_callback: %s' % _safe_str(e))


# ==================== QMT Strategy Framework ====================

def init(ContextInfo):
    global _account_id, _ContextInfo

    _ContextInfo = ContextInfo  # Save for use in request handlers

    # Get account ID from QMT framework
    # 'account' is a global variable injected by QMT strategy runtime
    try:
        _account_id = str(account)  # noqa
    except NameError:
        _account_id = ''
        print('[INIT] WARNING: account not available from QMT framework')
        print('[INIT] Please ensure this strategy is loaded with a valid trading account')

    if not _account_id:
        print('[INIT] ERROR: No account ID configured. Server will not function correctly.')
        print('[INIT] Please restart the strategy with a valid account.')
        return

    ContextInfo.set_account(_account_id)

    print('=' * 50)
    print('[INIT] Trade HTTP Server')
    print('[INIT] Account: %s' % _account_id)
    print('[INIT] HTTP: http://%s:%d' % (HTTP_HOST, HTTP_PORT))
    print('=' * 50)

    # Init server socket
    _init_server()

    # Use schedule_run() - the NEW timer API (more reliable than run_time)
    try:
        # Start immediately (past time), repeat every 100ms forever
        ContextInfo.schedule_run(
            _poll_socket,
            '20200101000000',
            -1,
            dt.timedelta(milliseconds=100),
            'http_poll'
        )
        print('[INIT] schedule_run() timer started (100ms)')
    except Exception as e:
        print('[INIT] schedule_run() FAILED: %s' % _safe_str(e))
        traceback.print_exc()
        # Fallback: also try run_time()
        try:
            ContextInfo.run_time('_poll_socket_v2', '100nMilliSecond', '2020-01-01 00:00:00')
            print('[INIT] run_time() fallback started')
        except Exception as e2:
            print('[INIT] run_time() also FAILED: %s' % _safe_str(e2))


def _poll_socket_v2(ContextInfo):
    """Fallback timer callback for run_time()."""
    _poll_socket(ContextInfo)


def handlebar(ContextInfo):
    pass


def after_init(ContextInfo):
    print('[INIT] Strategy ready')
