from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from core.ai.anthropic_provider import (
    DEFAULT_MODEL,
    EFFORT,
    FALLBACK_BETA,
    MIN_MAX_TOKENS,
    AnthropicProvider,
)


def _response(content, stop_reason="end_turn", stop_details=None, model=DEFAULT_MODEL):
    return SimpleNamespace(
        content=content,
        stop_reason=stop_reason,
        stop_details=stop_details,
        model=model,
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )


def _text(text):
    return SimpleNamespace(type="text", text=text)


THINKING = SimpleNamespace(type="thinking", thinking="")


@override_settings(ANTHROPIC_API_KEY="test-key", AI_MODEL="")
class AnthropicProviderTests(SimpleTestCase):
    def setUp(self):
        patcher = patch("core.ai.anthropic_provider.Anthropic")
        self.client = patcher.start().return_value
        self.addCleanup(patcher.stop)

    def test_defaults_to_current_sonnet(self):
        self.assertEqual(AnthropicProvider().get_model_name(), DEFAULT_MODEL)

    @override_settings(AI_MODEL="claude-haiku-5-5")
    def test_respects_configured_model(self):
        self.assertEqual(AnthropicProvider().get_model_name(), "claude-haiku-5-5")

    def test_request_omits_temperature_and_sets_effort_fallback_and_token_floor(self):
        self.client.beta.messages.create.return_value = _response([_text("hello")])

        AnthropicProvider().generate("prompt", system_prompt="sys", temperature=0.7, max_tokens=2000)

        kwargs = self.client.beta.messages.create.call_args.kwargs
        self.assertNotIn("temperature", kwargs)
        self.assertEqual(kwargs["max_tokens"], MIN_MAX_TOKENS)
        self.assertEqual(kwargs["output_config"], {"effort": EFFORT})
        self.assertEqual(kwargs["system"], "sys")
        self.assertEqual(kwargs["fallbacks"], "default")
        self.assertEqual(kwargs["betas"], [FALLBACK_BETA])

    @override_settings(AI_MODEL="claude-haiku-5-5")
    def test_models_without_fallback_support_use_standard_endpoint(self):
        self.client.messages.create.return_value = _response([_text("hi")], model="claude-haiku-5-5")

        AnthropicProvider().generate("prompt")

        self.client.beta.messages.create.assert_not_called()
        self.assertNotIn("fallbacks", self.client.messages.create.call_args.kwargs)

    def test_skips_thinking_blocks_and_joins_text(self):
        self.client.beta.messages.create.return_value = _response([THINKING, _text("Dear "), _text("team")])

        result = AnthropicProvider().generate("prompt")

        self.assertEqual(result.content, "Dear team")
        self.assertEqual(result.total_tokens, 15)

    def test_refusal_raises(self):
        self.client.beta.messages.create.return_value = _response(
            [], stop_reason="refusal", stop_details=SimpleNamespace(category="cyber")
        )
        with self.assertRaisesMessage(ValueError, "cyber"):
            AnthropicProvider().generate("prompt")

    def test_truncation_raises(self):
        self.client.beta.messages.create.return_value = _response([_text("partial")], stop_reason="max_tokens")
        with self.assertRaisesMessage(ValueError, "max_tokens"):
            AnthropicProvider().generate("prompt")

    def test_empty_text_raises(self):
        self.client.beta.messages.create.return_value = _response([THINKING])
        with self.assertRaisesMessage(ValueError, "no text"):
            AnthropicProvider().generate("prompt")
