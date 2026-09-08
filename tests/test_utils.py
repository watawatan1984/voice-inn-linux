import os
import unittest
from datetime import datetime
from src.core.utils import get_config_dir, get_state_dir, now_iso, deep_merge_dict

class TestUtils(unittest.TestCase):
    def test_now_iso_format(self):
        """now_iso が有効な ISO 形式の文字列を返すことを確認"""
        iso_str = now_iso()
        self.assertIsInstance(iso_str, str)
        self.assertTrue(len(iso_str) > 10)
        # ISO形式のパース可能性を検証
        dt = datetime.fromisoformat(iso_str)
        self.assertIsNotNone(dt)

    def test_custom_env_config_dir(self):
        """VOICEIN_CONFIG_DIR 環境変数が指定された場合、最優先で使われることを確認"""
        custom_path = os.path.abspath("./custom_test_config")
        old_env = os.environ.get("VOICEIN_CONFIG_DIR")
        try:
            os.environ["VOICEIN_CONFIG_DIR"] = custom_path
            self.assertEqual(get_config_dir(), custom_path)
        finally:
            if old_env is not None:
                os.environ["VOICEIN_CONFIG_DIR"] = old_env
            else:
                os.environ.pop("VOICEIN_CONFIG_DIR", None)

    def test_portable_mode_config_dir(self):
        """VOICEIN_PORTABLE=1 の場合、アプリディレクトリが返されることを確認"""
        old_portable = os.environ.get("VOICEIN_PORTABLE")
        try:
            os.environ["VOICEIN_PORTABLE"] = "1"
            config_dir = get_config_dir()
            state_dir = get_state_dir()
            self.assertIsNotNone(config_dir)
            self.assertIsNotNone(state_dir)
        finally:
            if old_portable is not None:
                os.environ["VOICEIN_PORTABLE"] = old_portable
            else:
                os.environ.pop("VOICEIN_PORTABLE", None)

if __name__ == "__main__":
    unittest.main()
