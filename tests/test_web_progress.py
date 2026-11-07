"""Tests for Web Studio progress tracking and ETA calculation."""

import unittest
import time
from poke_translator.web import server as web_server
from poke_translator.core.table_scanner import TextEntry
from poke_translator.core.project import TranslationProject


class TestProgressTracking(unittest.TestCase):
    def setUp(self):
        # Reset state
        web_server.set_progress("test", "Test Task", 0, 100, "Initializing", finished=False)

    def test_set_and_get_progress(self):
        st = time.time() - 2.0  # 2 seconds ago
        web_server.set_progress(
            task="auto_translate",
            title="100%全自動翻訳中",
            current=50,
            total=100,
            detail="Pikachu -> ピカチュウ",
            start_time=st,
        )
        prog = web_server.get_progress()
        self.assertTrue(prog["active"])
        self.assertEqual(prog["task"], "auto_translate")
        self.assertEqual(prog["current"], 50)
        self.assertEqual(prog["total"], 100)
        self.assertEqual(prog["percentage"], 50.0)
        self.assertGreaterEqual(prog["elapsed_seconds"], 1.9)
        self.assertGreater(prog["speed"], 0)
        self.assertGreater(prog["eta_seconds"], 0)
        self.assertFalse(prog["finished"])

    def test_completion_progress(self):
        st = time.time() - 1.0
        web_server.set_progress(
            task="build_rom",
            title="ROM構築完了",
            current=4,
            total=4,
            detail="完了",
            start_time=st,
            finished=True,
        )
        prog = web_server.get_progress()
        self.assertFalse(prog["active"])
        self.assertTrue(prog["finished"])
        self.assertEqual(prog["percentage"], 100.0)
        self.assertEqual(prog["eta_seconds"], 0.0)

    def test_auto_translate_callback(self):
        entries = [
            TextEntry("sp_1", "species", 0x100, 10, "Bulbasaur", ""),
            TextEntry("sp_2", "species", 0x110, 10, "Ivysaur", ""),
            TextEntry("sp_3", "species", 0x120, 10, "Venusaur", ""),
            TextEntry("mv_1", "moves", 0x200, 10, "Tackle", ""),
            TextEntry("mv_2", "moves", 0x210, 10, "Tail Whip", ""),
        ]
        proj = TranslationProject("Test", entries=entries)
        events = []

        def on_prog(cur, tot, msg):
            events.append((cur, tot, msg))

        count = proj.auto_translate_all(progress_callback=on_prog)
        self.assertEqual(count, 5)
        self.assertGreaterEqual(len(events), 2)

        # Final event should mark completion
        last_cur, last_tot, last_msg = events[-1]
        self.assertEqual(last_cur, 5)
        self.assertEqual(last_tot, 5)
        self.assertIn("完了", last_msg)

        # Monotonically increasing progress
        currents = [e[0] for e in events]
        self.assertEqual(currents, sorted(currents))


if __name__ == "__main__":
    unittest.main()
