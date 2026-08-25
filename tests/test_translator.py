from __future__ import annotations

import unittest
from typing import Any

from cat_translate_cli.translator import detect_language, translate


class FakeLlama:
    def __init__(self, *, n_ctx: int = 4096, prompt_tokens: int = 20) -> None:
        self._n_ctx = n_ctx
        self._prompt_tokens = prompt_tokens
        self.calls: list[dict[str, Any]] = []

    def n_ctx(self) -> int:
        return self._n_ctx

    def tokenize(self, _text: bytes, *, add_bos: bool = True) -> list[int]:
        return list(range(self._prompt_tokens))

    def create_chat_completion(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"choices": [{"message": {"content": " translated "}}]}


class DetectLanguageTests(unittest.TestCase):
    def test_full_width_latin_is_english(self) -> None:
        self.assertEqual(detect_language("ＨＥＬＬＯ ＷＯＲＬＤ"), "English")

    def test_japanese_text_is_japanese(self) -> None:
        self.assertEqual(detect_language("猫はとてもかわいいです。"), "Japanese")

    def test_digits_and_punctuation_do_not_bias_detection(self) -> None:
        self.assertEqual(detect_language("Hello 12345 !!!"), "English")


class TranslationBudgetTests(unittest.TestCase):
    def test_rejects_input_that_cannot_fit_requested_output(self) -> None:
        llm = FakeLlama(n_ctx=100, prompt_tokens=80)
        with self.assertRaisesRegex(ValueError, "コンテキスト上限"):
            translate(llm, "hello", max_tokens=20)  # type: ignore[arg-type]
        self.assertEqual(llm.calls, [])

    def test_translation_runs_when_budget_fits(self) -> None:
        llm = FakeLlama(n_ctx=4096, prompt_tokens=20)
        result = translate(llm, "hello", max_tokens=32)  # type: ignore[arg-type]
        self.assertEqual(result, "translated")
        self.assertEqual(len(llm.calls), 1)


if __name__ == "__main__":
    unittest.main()
