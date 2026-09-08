import sys
import unittest
from unittest.mock import patch, MagicMock
from src.ai.factory import get_provider, get_available_providers

class TestAIFactory(unittest.TestCase):
    def test_available_providers(self):
        """登録プロバイダ一覧に gemini, groq, local が含まれることを確認"""
        providers = get_available_providers()
        self.assertIn("gemini", providers)
        self.assertIn("groq", providers)
        self.assertIn("local", providers)

    def test_unknown_provider_raises_error(self):
        """未知のプロバイダ名が指定された場合に ValueError が発生することを確認"""
        with self.assertRaises(ValueError) as ctx:
            get_provider("openai_unsupported")
        self.assertIn("Unknown provider", str(ctx.exception))

    def test_get_groq_provider(self):
        """groq プロバイダが生成できることを確認"""
        mock_groq_mod = MagicMock()
        with patch.dict(sys.modules, {"groq": mock_groq_mod}):
            with patch("src.core.config.config_manager.settings", {"groq_key": "dummy_key"}):
                provider = get_provider("groq")
                self.assertEqual(provider.__class__.__name__, "GroqProvider")

    def test_get_gemini_provider(self):
        """gemini プロバイダが生成できることを確認"""
        mock_genai_mod = MagicMock()
        with patch.dict(sys.modules, {"google": MagicMock(), "google.genai": mock_genai_mod}):
            with patch("src.core.config.config_manager.settings", {"gemini_key": "dummy_key"}):
                provider = get_provider("gemini")
                self.assertEqual(provider.__class__.__name__, "GeminiProvider")

if __name__ == "__main__":
    unittest.main()
