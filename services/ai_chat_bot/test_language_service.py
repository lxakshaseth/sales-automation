import unittest

from app.services.language_service import detect_language, get_language_prompt, get_localized_message, should_switch_language


class LanguageServiceTests(unittest.TestCase):
    def test_detects_supported_greeting_languages(self):
        self.assertEqual(detect_language("Hello")["language_code"], "en")
        self.assertEqual(detect_language("नमस्ते")["language_code"], "hi")
        self.assertEqual(detect_language("Hola")["language_code"], "es")
        self.assertEqual(detect_language("Bonjour")["language_code"], "fr")

    def test_detects_explicit_language_switches(self):
        self.assertEqual(should_switch_language("Talk in English")["language_code"], "en")
        self.assertEqual(should_switch_language("Hindi me baat karo")["language_code"], "hi")
        self.assertEqual(should_switch_language("Switch to Marathi")["language_code"], "mr")
        self.assertEqual(should_switch_language("अब हिंदी में जवाब दो")["language_code"], "hi")

    def test_detects_manual_language_command(self):
        switch = should_switch_language("/language marathi")

        self.assertTrue(switch["should_switch"])
        self.assertEqual(switch["language_code"], "mr")

    def test_language_prompt_names_active_language(self):
        prompt = get_language_prompt("hi")

        self.assertIn("Always reply in the user's preferred language", prompt)
        self.assertIn("Hindi", prompt)

    def test_localized_reminder_falls_back_to_english(self):
        self.assertIn("फॉलो अप", get_localized_message("reminder", "hi"))
        self.assertIn("Just checking in", get_localized_message("reminder", "unknown"))


if __name__ == "__main__":
    unittest.main()
