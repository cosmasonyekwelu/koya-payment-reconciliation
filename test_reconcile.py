import json
import unittest
from decimal import Decimal

from reconcile import reconcile


def ev(txn_id, status, amount, ts):
    return json.dumps({"txn_id": txn_id, "status": status, "amount": amount,
                       "currency": "NGN", "ts": ts})


class ReconcileTests(unittest.TestCase):
    def test_duplicate_ids_counted_once(self):
        lines = [ev("a", "success", 10, "2026-09-01T10:00:00Z"),
                 ev("a", "success", 10, "2026-09-01T11:00:00Z")]
        self.assertEqual(reconcile(lines), (1, Decimal(10)))

    def test_success_then_failure(self):
        lines = [ev("a", "success", 10, "2026-09-01T10:00:00Z"),
                 ev("a", "failed", 10, "2026-09-01T11:00:00Z")]
        self.assertEqual(reconcile(lines), (0, Decimal(0)))

    def test_failure_then_success(self):
        lines = [ev("a", "failed", 10, "2026-09-01T10:00:00Z"),
                 ev("a", "success", 10, "2026-09-01T11:00:00Z")]
        self.assertEqual(reconcile(lines), (1, Decimal(10)))

    def test_pending_latest_not_counted(self):
        lines = [ev("a", "success", 10, "2026-09-01T10:00:00Z"),
                 ev("a", "pending", 10, "2026-09-01T11:00:00Z")]
        self.assertEqual(reconcile(lines), (0, Decimal(0)))

    def test_out_of_order_lines_use_timestamp(self):
        lines = [ev("a", "failed", 10, "2026-09-01T11:00:00Z"),
                 ev("a", "success", 10, "2026-09-01T10:00:00Z")]
        self.assertEqual(reconcile(lines), (0, Decimal(0)))

    def test_malformed_and_missing_txn_id_ignored(self):
        lines = ["{not json", "", "[1, 2]",
                 json.dumps({"status": "success", "amount": 5, "ts": "2026-09-01T10:00:00Z"}),
                 ev("", "success", 5, "2026-09-01T10:00:00Z"),
                 ev("a", "success", 7, "2026-09-01T10:00:00Z")]
        self.assertEqual(reconcile(lines), (1, Decimal(7)))

    def test_string_amount_with_commas(self):
        lines = [ev("a", "success", "1,234.50", "2026-09-01T10:00:00Z")]
        self.assertEqual(reconcile(lines), (1, Decimal("1234.50")))

    def test_no_float_error(self):
        lines = [ev(str(i), "success", 0.1, "2026-09-01T10:00:00Z") for i in range(3)]
        self.assertEqual(reconcile(lines), (3, Decimal("0.3")))

    def test_timestamp_offsets_compared_as_instants(self):
        lines = [ev("a", "success", 1, "2026-09-01T10:00:00Z"),
                 ev("a", "failed", 1, "2026-09-01T10:30:00+02:00")]
        self.assertEqual(reconcile(lines), (1, Decimal(1)))


if __name__ == "__main__":
    unittest.main()
