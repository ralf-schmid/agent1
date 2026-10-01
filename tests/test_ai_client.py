"""Tests für die Fehler-Benachrichtigung im AIClient."""

from unittest.mock import MagicMock, patch

from losungs_bot.ai_client import AIClient


def _failing_client(on_error=None) -> AIClient:
    with patch("losungs_bot.ai_client.Anthropic"):
        client = AIClient("test-key", on_error=on_error)
    client._client.messages.create.side_effect = Exception("credit balance too low")
    return client


def test_error_triggers_notification():
    on_error = MagicMock()
    client = _failing_client(on_error)

    assert client.generate("prompt", "system") is None

    on_error.assert_called_once()
    assert "credit balance" in on_error.call_args.args[0]


def test_notification_is_throttled():
    on_error = MagicMock()
    client = _failing_client(on_error)

    client.generate("prompt", "system")
    client.generate("prompt", "system")

    on_error.assert_called_once()


def test_notification_again_after_cooldown():
    on_error = MagicMock()
    client = _failing_client(on_error)

    client.generate("prompt", "system")
    client._last_error_notify -= AIClient.ERROR_NOTIFY_COOLDOWN + 1
    client.generate("prompt", "system")

    assert on_error.call_count == 2


def test_failing_callback_does_not_raise():
    client = _failing_client(MagicMock(side_effect=Exception("mastodon down")))

    assert client.generate("prompt", "system") is None


def test_without_callback():
    assert _failing_client().generate("prompt", "system") is None
