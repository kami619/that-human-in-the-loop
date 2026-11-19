import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import update_ipl_trades as mod


SAMPLE_NEWS_HTML = """
<a href="/news/article/csk-and-srh-agree-to-four-player-trade">trade</a>
<a href="/news/article/harshal-patel-traded-to-gujarat-titans-from-sunrisers-hyderabad">trade</a>
<a href="/news/article/tata-ipl-2026-final-rcb-v-gt-match-report">final</a>
"""


class TestDiscoverTradeSlugs(unittest.TestCase):
    def test_filters_trade_articles(self):
        slugs = mod.discover_trade_slugs(SAMPLE_NEWS_HTML)
        self.assertEqual(
            slugs,
            [
                "csk-and-srh-agree-to-four-player-trade",
                "harshal-patel-traded-to-gujarat-titans-from-sunrisers-hyderabad",
            ],
        )


class TestBuildTradeRecord(unittest.TestCase):
    def test_record_includes_source_metadata(self):
        slug = "hardik-pandya-and-arshdeep-singh-complete-major-trade-between-pbks-and-mi"
        meta = {
            "slug": slug,
            "url": f"{mod.IPL_BASE}/news/article/{slug}",
            "title": "Hardik Pandya and Arshdeep Singh complete major trade between PBKS and MI",
            "publishedAt": "2026-11-11T09:15:00+05:30",
            "description": "IPL MEDIA ADVISORY",
        }
        record = mod.build_trade_record(slug, meta, 4)
        self.assertEqual(record["id"], "IPL27-04")
        self.assertEqual(record["left"]["to"], "PBKS")
        self.assertTrue(record["sourceUrl"].endswith(slug))
        self.assertEqual(len(record["players"]), 2)
        self.assertEqual(record["players"][0]["feeCr"], 18.0)


if __name__ == "__main__":
    unittest.main()