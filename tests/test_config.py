import unittest
import copy
from src.core.config import DEFAULT_SETTINGS, ConfigManager
from src.core.utils import deep_merge_dict
from src.core.const import DEFAULT_APP_CATEGORIES, DEFAULT_GEMINI_MODEL

class TestConfig(unittest.TestCase):
    def test_default_settings_structure(self):
        """既定設定の主要キーが存在することを確認"""
        self.assertIn("audio", DEFAULT_SETTINGS)
        self.assertIn("ui", DEFAULT_SETTINGS)
        self.assertIn("prompts", DEFAULT_SETTINGS)
        self.assertIn("app_categories", DEFAULT_SETTINGS)
        self.assertIn("category_prompts", DEFAULT_SETTINGS)

    def test_app_categories_match_const(self):
        """アプリカテゴリが const.py の定義と一致することを確認"""
        self.assertEqual(DEFAULT_SETTINGS["app_categories"], DEFAULT_APP_CATEGORIES)
        self.assertIn("DEV", DEFAULT_SETTINGS["app_categories"])
        self.assertIn("BIZ", DEFAULT_SETTINGS["app_categories"])
        self.assertIn("DOC", DEFAULT_SETTINGS["app_categories"])
        self.assertIn("STD", DEFAULT_SETTINGS["app_categories"])

    def test_deep_merge_dict(self):
        """ディープマージがネストした辞書を適切に統合することを確認"""
        base = {
            "a": 1,
            "nested": {"x": 10, "y": 20},
            "list": [1, 2]
        }
        override = {
            "nested": {"y": 99, "z": 30},
            "b": 2
        }
        merged = deep_merge_dict(base, override)
        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["b"], 2)
        self.assertEqual(merged["nested"]["x"], 10)
        self.assertEqual(merged["nested"]["y"], 99)
        self.assertEqual(merged["nested"]["z"], 30)

    def test_get_language_fallback(self):
        """無効な言語が設定された場合に ja へフォールバックすることを確認"""
        cm = ConfigManager()
        cm.settings["ui"]["language"] = "invalid_lang_code"
        self.assertEqual(cm.get_language(), "ja")

        cm.settings["ui"]["language"] = "en"
        self.assertEqual(cm.get_language(), "en")

if __name__ == "__main__":
    unittest.main()
