#!/usr/bin/env python
#coding:utf-8
"""
Test All Endpoints - QMT HTTP Server
======================================
Tests all 14 HTTP endpoints and prints results.
Useful for verifying that trade_server.py is working correctly.

Prerequisites:
  - QMT is running with trade_server.py loaded
  - trade_server is listening on 127.0.0.1:8964
"""

import sys
import os
import json
import urllib.request
import urllib.error

BASE_URL = 'http://127.0.0.1:8964'


def request(method, path, body=None):
    """Send HTTP request and return (success, data)."""
    url = BASE_URL + path
    data = json.dumps(body).encode('utf-8') if body else None
    headers = {'Content-Type': 'application/json; charset=utf-8'}

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return True, result
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return False, f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, str(e)


def test_endpoint(name, method, path, body=None):
    """Test a single endpoint and print result."""
    ok, data = request(method, path, body)
    status = "OK" if ok else "FAIL"
    if ok:
        # Compact print
        if isinstance(data, dict):
            success = data.get('success', None)
            if success is not None:
                status = "OK" if success else "FAIL"
        print(f"  [{status:4s}] {method:4s} {path}")
        # Print key info
        if isinstance(data, dict):
            for key in ['count', 'status', 'account', 'order_id']:
                if key in data:
                    print(f"         {key}={data[key]}")
    else:
        print(f"  [{status:4s}] {method:4s} {path} - {data}")
    return ok


def main():
    print("=" * 60)
    print("QMT Trade Server - Endpoint Test")
    print(f"Target: {BASE_URL}")
    print("=" * 60)

    results = {}

    # 1. Health check
    print("\n--- Health & Account ---")
    results['health'] = test_endpoint('Health', 'GET', '/health')
    results['asset'] = test_endpoint('Asset', 'GET', '/asset')
    results['positions'] = test_endpoint('Positions', 'GET', '/positions')

    # 2. Market data
    print("\n--- Market Data ---")
    results['tick'] = test_endpoint('Tick', 'GET', '/tick?codes=000001.SZ')
    results['instrument'] = test_endpoint('Instrument', 'GET', '/instrument?code=000001.SZ')
    results['kline'] = test_endpoint('Kline', 'GET', '/kline?stock=000001.SZ&count=3')

    # 3. Sector data
    print("\n--- Sector Data ---")
    results['sector_list'] = test_endpoint('Sector List', 'GET', '/sector_list?node=')
    results['sector_stocks'] = test_endpoint('Sector Stocks', 'GET', '/sector_stocks?sector=沪深A股')

    # 4. Order query
    print("\n--- Orders & Trades ---")
    results['orders'] = test_endpoint('Orders', 'GET', '/orders')
    results['orders_cancel'] = test_endpoint('Cancelable Orders', 'GET', '/orders?cancelable_only=1')
    results['trades'] = test_endpoint('Trades', 'GET', '/trades')
    results['events'] = test_endpoint('Events', 'GET', '/events')

    # 5. Trading (test with invalid params to verify error handling)
    print("\n--- Trading (error handling) ---")
    ok, data = request('POST', '/buy', {'stock_code': '', 'volume': 0})
    results['buy_invalid'] = not ok or (isinstance(data, dict) and not data.get('success'))
    print(f"  [{'OK' if results['buy_invalid'] else 'FAIL':4s}] POST /buy (invalid params) - should reject")

    ok, data = request('POST', '/sell', {'stock_code': '', 'volume': 0})
    results['sell_invalid'] = not ok or (isinstance(data, dict) and not data.get('success'))
    print(f"  [{'OK' if results['sell_invalid'] else 'FAIL':4s}] POST /sell (invalid params) - should reject")

    ok, data = request('POST', '/cancel', {'order_id': ''})
    results['cancel_invalid'] = not ok or (isinstance(data, dict) and not data.get('success'))
    print(f"  [{'OK' if results['cancel_invalid'] else 'FAIL':4s}] POST /cancel (empty id) - should reject")

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Results: {passed}/{total} passed")

    failed = [k for k, v in results.items() if not v]
    if failed:
        print(f"Failed: {', '.join(failed)}")
    else:
        print("All endpoints working!")


if __name__ == '__main__':
    main()
