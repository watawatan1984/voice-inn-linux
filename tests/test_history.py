import unittest
import tempfile
import os
from unittest.mock import patch

class TestHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_patcher = patch("src.core.history.STATE_DIR", self.temp_dir.name)
        self.history_path_patcher = patch(
            "src.core.history.HISTORY_PATH", 
            os.path.join(self.temp_dir.name, "history.json")
        )
        self.state_patcher.start()
        self.history_path_patcher.start()

    def tearDown(self):
        self.history_path_patcher.stop()
        self.state_patcher.stop()
        self.temp_dir.cleanup()

    def test_append_and_load_history(self):
        """履歴の追加と取得が正常に行えることを確認"""
        from src.core.history import append_history_item, load_history_file

        self.assertEqual(load_history_file(), [])
        
        append_history_item(text="テスト音声入力です", provider="gemini")
        items = load_history_file()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["text"], "テスト音声入力です")
        self.assertEqual(items[0]["provider"], "gemini")
        self.assertIsNone(items[0]["error"])

    def test_history_max_items_limit(self):
        """最大件数 (50件) を超えないことを確認"""
        from src.core.history import append_history_item, load_history_file, HISTORY_MAX_ITEMS

        for i in range(HISTORY_MAX_ITEMS + 10):
            append_history_item(text=f"アイテム {i}", provider="groq")

        items = load_history_file()
        self.assertEqual(len(items), HISTORY_MAX_ITEMS)
        # 先頭が最新のアイテム
        self.assertEqual(items[0]["text"], f"アイテム {HISTORY_MAX_ITEMS + 9}")

if __name__ == "__main__":
    unittest.main()
