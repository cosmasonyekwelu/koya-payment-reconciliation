#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal


def parse_amount(value):
    """Convert an amount (number or string such as "12,345.67") to Decimal."""
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return Decimal(str(value))


def parse_ts(value):
    """Parse a UTC ISO-8601 timestamp into an aware datetime."""
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def read_events(lines):
    """Yield valid events, skipping unreadable lines and events without txn_id."""
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict) or not event.get("txn_id"):
            continue
        try:
            ts = parse_ts(event["ts"])
        except (KeyError, ValueError):
            continue
        yield ts, event


def reconcile(lines):
    """Return (count, total) of transactions whose latest attempt succeeded."""
    latest = {}
    for ts, event in read_events(lines):
        txn_id = event["txn_id"]
        # Events are not guaranteed to be in order; on equal timestamps the
        # later line wins.
        if txn_id not in latest or ts >= latest[txn_id][0]:
            latest[txn_id] = (ts, event)

    count = 0
    total = Decimal(0)
    for _, event in latest.values():
        if event.get("status") == "success":
            try:
                total += parse_amount(event["amount"])
            except (KeyError, ArithmeticError, ValueError):
                continue
            count += 1
    return count, total


def main():
    with open("payments.jsonl", encoding="utf-8") as f:
        count, total = reconcile(f)

    with open("expected.txt") as f:
        expected = int(f.read().strip())

    if count != expected:
        print(f"Check failed: counted {count} successful payments, expected {expected}.")
        print("Something in the data isn't being handled the way the README describes.")
    else:
        print(f"Check passed: {count} successful payments.")
        print(f"Your code: KOYA-{int(total.quantize(Decimal(1), rounding=ROUND_HALF_UP))}")


if __name__ == "__main__":
    main()
