import unittest

import solana_log_parser as parser


class SolanaLogParserTests(unittest.TestCase):
    def test_parse_detects_errors_and_warnings(self):
        lines = [
            "INFO validator initialized",
            "WARN slow replay retry",
            "ERROR rpc health check failed",
            "INFO vote landed",
        ]
        summary = parser.parse_log_lines(lines)
        self.assertEqual(summary.total_lines, 4)
        self.assertEqual(summary.error_lines, 1)
        self.assertEqual(summary.warning_lines, 1)

    def test_signal_counts(self):
        lines = [
            "INFO vote landed",
            "INFO gossip table updated",
            "INFO rpc getSlot",
            "INFO slot advanced",
        ]
        summary = parser.parse_log_lines(lines)
        self.assertGreaterEqual(summary.signal_counts["votes"], 1)
        self.assertGreaterEqual(summary.signal_counts["gossip"], 1)
        self.assertGreaterEqual(summary.signal_counts["rpc"], 1)
        self.assertGreaterEqual(summary.signal_counts["slots"], 1)

    def test_as_dict_rates(self):
        lines = ["ERROR one", "WARN one", "INFO ok", "INFO ok"]
        summary = parser.parse_log_lines(lines)
        data = parser.as_dict(summary)
        self.assertEqual(data["total_lines"], 4)
        self.assertEqual(data["error_rate_pct"], 25.0)
        self.assertEqual(data["warning_rate_pct"], 25.0)


if __name__ == "__main__":
    unittest.main()
