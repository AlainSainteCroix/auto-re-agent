"""Tests for the OpenAI-compatible provider response parsing."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from re_agent.llm.openai_compat import OpenAIProvider
from re_agent.llm.protocol import Message


def _make_provider(response: object) -> OpenAIProvider:
    """Build a provider whose underlying client returns *response*."""
    with patch("re_agent.llm.openai_compat.openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.chat.completions.create.return_value = response
        mock_openai.return_value = client
        return OpenAIProvider(api_key="test")


def test_send_returns_message_content() -> None:
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))])
    provider = _make_provider(response)
    assert provider.send([Message(role="user", content="hi")]) == "hello"


def test_send_empty_choices_raises_clear_error() -> None:
    """An empty ``choices`` list must raise a clear error, not IndexError."""
    response = SimpleNamespace(choices=[])
    provider = _make_provider(response)
    with pytest.raises(RuntimeError, match="no choices"):
        provider.send([Message(role="user", content="hi")])


def test_send_none_content_returns_empty_string() -> None:
    """A content-less message (content=None) yields an empty string, not None."""
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None))])
    provider = _make_provider(response)
    assert provider.send([Message(role="user", content="hi")]) == ""
