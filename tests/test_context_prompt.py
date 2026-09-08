import unittest
from src.core.context_prompt import (
    detect_category,
    get_category_prompt,
    generate_context_prompt
)

class TestContextPrompt(unittest.TestCase):
    def test_detect_category_dev(self):
        """開発系ツールのタイトルから DEV カテゴリが検出されることを確認"""
        self.assertEqual(detect_category("main.py - Visual Studio Code"), "DEV")
        self.assertEqual(detect_category("Terminal - bash"), "DEV")
        self.assertEqual(detect_category("Cursor - settings.json"), "DEV")
        self.assertEqual(detect_category("git status - Windows Terminal"), "DEV")

    def test_detect_category_biz(self):
        """ビジネスツールのタイトルから BIZ カテゴリが検出されることを確認"""
        self.assertEqual(detect_category("Inbox - Outlook"), "BIZ")
        self.assertEqual(detect_category("Slack | #general"), "BIZ")
        self.assertEqual(detect_category("Zoom Meeting"), "BIZ")
        self.assertEqual(detect_category("Teams Chat"), "BIZ")

    def test_detect_category_doc(self):
        """文書作成ツールのタイトルから DOC カテゴリが検出されることを確認"""
        self.assertEqual(detect_category("Report.docx - Microsoft Word"), "DOC")
        self.assertEqual(detect_category("Meeting Notes - Notion"), "DOC")
        self.assertEqual(detect_category("無題 - メモ帳"), "DOC")

    def test_detect_category_fallback(self):
        """該当しないタイトルまたは空タイトルで STD にフォールバックすることを確認"""
        self.assertEqual(detect_category("Calculator"), "STD")
        self.assertEqual(detect_category(""), "STD")
        self.assertEqual(detect_category(None), "STD")

    def test_get_category_prompt_placeholder_injection(self):
        """ウィンドウタイトルがプロンプトテンプレートに正常に埋め込まれることを確認"""
        prompt = get_category_prompt("DEV", "PyCharm 2024")
        self.assertIn("PyCharm 2024", prompt)
        self.assertNotIn("{window_title}", prompt)

    def test_generate_context_prompt(self):
        """generate_context_prompt で各プロバイダのプロンプトにコンテキストが注入されることを確認"""
        base_prompts = {
            "groq_refine_system_prompt": "base refine",
            "gemini_transcribe_prompt": "base transcribe"
        }
        result = generate_context_prompt("Terminal", base_prompts)
        self.assertEqual(result["_detected_category"], "DEV")
        self.assertEqual(result["_detected_window"], "Terminal")
        self.assertIn("Terminal", result["groq_refine_system_prompt"])
        self.assertIn("Terminal", result["gemini_transcribe_prompt"])

if __name__ == "__main__":
    unittest.main()
