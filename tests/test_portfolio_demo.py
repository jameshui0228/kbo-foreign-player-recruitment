import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("portfolio_demo", ROOT / "scripts/portfolio_demo.py")
demo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(demo)


class PortfolioDemoTest(unittest.TestCase):
    def test_tracked_results(self):
        selected, audit = demo.load_results()
        self.assertEqual(len(selected), 6)
        self.assertEqual([r["player"] for r in selected if r["decision_rank"] == "1"],
                         ["Will Brennan", "Josh Fleming"])
        self.assertEqual(len(audit), 2)
        self.assertIn("0.650", demo.markdown(selected, audit))
        self.assertIn("validation", demo.svg(audit))

    def test_missing_columns_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text("other\nvalue\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing columns"):
                demo.read_rows(path, ["player"])

    def test_english_summary_keeps_context_and_korean_link(self):
        selected, audit = demo.load_results()
        summary = demo.markdown(selected, audit)
        self.assertTrue(summary.startswith("# Public Result Summary\n"))
        self.assertIn("[한국어](results.ko.md)", summary)
        self.assertIn("final June 2026 artifacts", summary)
        self.assertIn("not absolute success probabilities", summary)
        self.assertIn("| Hitter | 1 | Will Brennan |", summary)
        self.assertIn("| Pitcher | 1 | Josh Fleming |", summary)

    def test_empty_table_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty.csv"
            path.write_text("player\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no rows"):
                demo.read_rows(path, ["player"])

    def test_generated_files_match(self):
        selected, audit = demo.load_results()
        for name, content in (("results.md", demo.markdown(selected, audit)), ("validation.svg", demo.svg(audit))):
            self.assertEqual((ROOT / "docs/portfolio" / name).read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
