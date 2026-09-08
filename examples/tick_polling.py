#!/usr/bin/env python
#coding:utf-8
"""
Tick Polling Example
====================
Demonstrates how to poll real-time tick data in a loop,
which replaces xtdata.subscribe_whole_quote() in HTTP mode.

Key differences from xtquant:
  - xtquant: subscribe once, receive callbacks on every tick
  - HTTP mode: poll /tick endpoint every N seconds

Usage:
  python tick_polling.py                    # Default: poll every 1s
  python tick_polling.py --interval 0.5     # Poll every 0.5s
  python tick_polling.py --codes 000001.SZ,600519.SH
"""

import sys
import os
import time
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import QMTHttpClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


def format_tick(tick):
    """Format tick data for display."""
    last = tick.get('lastPrice', 0)
    volume = tick.get('volume', 0)
    amount = tick.get('amount', 0)

    bid_prices = tick.get('bidPrice', [])
    ask_prices = tick.get('askPrice', [])
    bid_vols = tick.get('bidVol', [])
    ask_vols = tick.get('askVol', [])

    bid1 = f"{bid_prices[0]:.2f}x{bid_vols[0]}" if bid_prices and bid_vols else "N/A"
    ask1 = f"{ask_prices[0]:.2f}x{ask_vols[0]}" if ask_prices and ask_vols else "N/A"

    return f"last={last:.2f}  bid1={bid1}  ask1={ask1}  vol={volume}  amt={amount:.0f}"


def main():
    parser = argparse.ArgumentParser(description='Tick polling example')
    parser.add_argument('--codes', default='000001.SZ,600519.SH',
                        help='Comma-separated stock codes (default: 000001.SZ,600519.SH)')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='Polling interval in seconds (default: 1.0)')
    args = parser.parse_args()

    code_list = [c.strip() for c in args.codes.split(',') if c.strip()]
    interval = args.interval

    print("=" * 70)
    print(f"Tick Polling - {', '.join(code_list)}")
    print(f"Interval: {interval}s | Ctrl+C to stop")
    print("=" * 70)

    client = QMTHttpClient()

    if not client.check_connection():
        print("ERROR: Cannot connect to trade_server!")
        return

    prev_prices = {}
    poll_count = 0

    try:
        while True:
            poll_count += 1
            ticks = client.get_full_tick(code_list)

            if ticks:
                ts = time.strftime('%H:%M:%S')
                print(f"\n[{ts}] Poll #{poll_count}")
                for code in code_list:
                    tick = ticks.get(code)
                    if tick:
                        last = tick.get('lastPrice', 0)
                        prev = prev_prices.get(code, last)
                        change = last - prev if prev else 0
                        arrow = "^^^" if change > 0 else ("vvv" if change < 0 else "---")
                        print(f"  {code}: {format_tick(tick)}  {arrow}")
                        prev_prices[code] = last
                    else:
                        print(f"  {code}: no data")
            else:
                print(f"\n[{time.strftime('%H:%M:%S')}] Poll #{poll_count} - failed")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\nStopped after {poll_count} polls")


if __name__ == '__main__':
    main()
