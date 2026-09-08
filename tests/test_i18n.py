import unittest
from src.core.i18n import t
from src.core.config import config_manager

class TestI18n(unittest.TestCase):
    def test_translation_ja(self):
        """日本語キーの翻訳が取得できることを確認"""
        config_manager.settings["ui"]["language"] = "ja"
        self.assertEqual(t("app_name"), "Voice In")
        self.assertIn("Voice In 設定", t("settings_title"))

    def test_translation_en(self):
        """英語キーの翻訳が取得できることを確認"""
        config_manager.settings["ui"]["language"] = "en"
        self.assertEqual(t("app_name"), "Voice In")
        self.assertIn("Voice In Settings", t("settings_title"))
        config_manager.settings["ui"]["language"] = "ja" # 復元

    def test_placeholder_formatting(self):
        """プレースホルダーのフォーマット置換が機能することを確認"""
        config_manager.settings["ui"]["language"] = "ja"
        text = t("tray_current", provider="Gemini")
        self.assertEqual(text, "現在: Gemini")

    def test_missing_key_fallback(self):
        """未定義のキーがそのまま返されることを確認"""
        self.assertEqual(t("non_existing_key_xyz"), "non_existing_key_xyz")

if __name__ == "__main__":
    unittest.main()
