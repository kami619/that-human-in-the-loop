import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import ipl_security as mod


class TestIplSecurity(unittest.TestCase):
    def test_accepts_official_source(self):
        url = "https://www.iplt20.com/news/article/example"
        self.assertEqual(mod.validate_trade_source_url(url), url)

    def test_rejects_javascript_scheme(self):
        with self.assertRaises(ValueError):
            mod.validate_trade_source_url("javascript:alert(1)")

    def test_rejects_wrong_host(self):
        with self.assertRaises(ValueError):
            mod.validate_trade_source_url("https://evil.example/trade")

    def test_valid_tint(self):
        tint = (
            "linear-gradient(145deg, rgba(245, 197, 24, 0.22) 0%, "
            "rgba(16, 19, 28, 0.95) 85%)"
        )
        self.assertTrue(mod.validate_tint(tint))

    def test_rejects_tint_injection(self):
        self.assertFalse(mod.validate_tint("linear-gradient(145deg, red); alert(1)"))


if __name__ == "__main__":
    unittest.main()