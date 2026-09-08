#!/usr/bin/env python
#coding:utf-8
"""
Basic Usage Example - QMT HTTP Client
======================================
Demonstrates the core workflow:
  1. Connect to trade_server
  2. Query account info
  3. Get market data
  4. Place orders
  5. Poll for events

Prerequisites:
  - QMT is running with trade_server.py loaded as a strategy
  - trade_server is listening on 127.0.0.1:8964
"""

import sys
import os
import time
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import QMTHttpClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def main():
    # 1. Create client and check connection
    print("=" * 50)
    print("QMT HTTP Client - Basic Usage")
    print("=" * 50)

    client = QMTHttpClient(host='127.0.0.1', port=8964)

    if not client.check_connection():
        print("ERROR: Cannot connect to trade_server!")
        print("Make sure QMT is running and trade_server.py is loaded.")
        return

    print("Connected to trade_server")

    # 2. Health check
    health = client.health()
    print(f"\nServer health: {health}")

    # 3. Query account asset
    asset = client.get_asset()
    if asset:
        print(f"\nAccount Asset:")
        print(f"  Available cash: {asset.get('m_dAvailable', 'N/A')}")
        print(f"  Total assets:   {asset.get('m_dBalance', 'N/A')}")
        print(f"  Frozen cash:    {asset.get('m_dFrozenCash', 'N/A')}")
        print(f"  Stock value:    {asset.get('m_dStockMarket', 'N/A')}")
    else:
        print("Failed to get account asset")

    # 4. Query positions
    positions = client.get_positions()
    print(f"\nPositions ({len(positions)}):")
    for pos in positions:
        code = pos.get('stock_code', 'N/A')
        vol = pos.get('m_nVolume', 0)
        can_use = pos.get('m_nCanUseVolume', 0)
        cost = pos.get('m_dCostPrice', 0)
        print(f"  {code}: {vol} shares (available: {can_use}) @ {cost:.3f}")

    # 5. Get real-time tick data
    codes = ['000001.SZ', '600519.SH']
    ticks = client.get_full_tick(codes)
    if ticks:
        print(f"\nTick data:")
        for code, tick in ticks.items():
            last = tick.get('lastPrice', 0)
            bid1 = tick.get('bidPrice', [0])[0] if tick.get('bidPrice') else 0
            ask1 = tick.get('askPrice', [0])[0] if tick.get('askPrice') else 0
            print(f"  {code}: last={last:.2f} bid1={bid1:.2f} ask1={ask1:.2f}")
    else:
        print("Failed to get tick data")

    # 6. Get K-line data
    klines = client.get_kline('000001.SZ', count=5, period='1d')
    if klines:
        print(f"\nRecent K-line (000001.SZ):")
        for bar in klines:
            print(f"  {bar.get('date')}: O={bar.get('open',0):.2f} H={bar.get('high',0):.2f} "
                  f"L={bar.get('low',0):.2f} C={bar.get('close',0):.2f} V={bar.get('volume',0)}")

    # 7. Get instrument detail
    detail = client.get_instrument_detail('000001.SZ')
    if detail:
        print(f"\nInstrument detail (000001.SZ):")
        print(f"  Name:       {detail.get('InstrumentName', 'N/A')}")
        print(f"  PreClose:   {detail.get('PreClose', 'N/A')}")
        print(f"  UpStop:     {detail.get('UpStopPrice', 'N/A')}")
        print(f"  DownStop:   {detail.get('DownStopPrice', 'N/A')}")
        print(f"  FloatVol:   {detail.get('FloatVolume', 'N/A')}")

    # 8. Example: Place buy order (COMMENTED OUT for safety)
    # Uncomment to actually place an order
    """
    print("\n--- Placing buy order ---")
    success, order_id = client.buy(
        stock_code='000001.SZ',
        volume=100,          # 100 shares
        price=10.50,         # Limit price
        price_type=11,       # FIX_PRICE (limit order)
        strategy_name='test',
        order_remark='test order'
    )
    print(f"  Success: {success}, Order ID: {order_id}")

    if success and order_id:
        # Cancel the order
        print(f"\n--- Canceling order {order_id} ---")
        cancel_ok = client.cancel(order_id)
        print(f"  Cancel result: {cancel_ok}")
    """

    # 9. Poll events (callback replacement)
    events = client.poll_events(since=0)
    print(f"\nPending events: {len(events)}")
    for evt in events[:5]:  # Show first 5
        print(f"  [{evt.get('type')}] {evt.get('datetime')} - {evt.get('data', {}).get('stock_code', 'N/A')}")

    print("\nDone!")


if __name__ == '__main__':
    main()
