"""Claude (Anthropic) LLM provider implementation."""

from __future__ import annotations

import os
import uuid
from typing import Any

import anthropic

from re_agent.llm.protocol import Message


class ClaudeProvider:
    """LLM provider backed by an Anthropic-compatible Claude API.

    Implements :class:`LLMProvider` using the ``anthropic`` Python SDK.

    Two backends are supported:

    * **Bedrock** (recommended here): when ``use_bedrock`` is true — or the
      ``RE_AGENT_BEDROCK`` env var is set — the client uses
      ``anthropic.AnthropicBedrock``, which reads AWS credentials from the
      standard chain (``~/.aws/credentials``, ``AWS_*`` env vars, instance
      role). No Anthropic API key, no custom gateway.
    * **Direct / compatible API**: otherwise the client uses
      ``anthropic.Anthropic`` against the official API, or any
      Anthropic-compatible endpoint set via ``ANTHROPIC_BASE_URL``.

    Args:
        api_key: API key (direct mode only). If ``None``, the SDK falls back
            to the ``ANTHROPIC_API_KEY`` environment variable.
        model: Model identifier. If ``None``, falls back to the right env var
            for the active backend, then a sensible default.
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature (``0.0`` = deterministic).
        base_url: Anthropic-compatible endpoint (direct mode only). If
            ``None``, falls back to the ``ANTHROPIC_BASE_URL`` env var.
        use_bedrock: Force the Bedrock backend. If ``None``, enabled when the
            ``RE_AGENT_BEDROCK`` env var is set to a truthy value.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        base_url: str | None = None,
        use_bedrock: bool | None = None,
    ) -> None:
        if use_bedrock is None:
            use_bedrock = os.environ.get("RE_AGENT_BEDROCK", "").lower() in ("1", "true", "yes")

        if use_bedrock:
            bedrock_kwargs: dict[str, Any] = {}
            region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
            if region:
                bedrock_kwargs["aws_region"] = region
            self._client: anthropic.Anthropic | anthropic.AnthropicBedrock = anthropic.AnthropicBedrock(
                **bedrock_kwargs
            )
            self._model = model or os.environ.get("RE_AGENT_BEDROCK_MODEL", "us.anthropic.claude-opus-4-6-v1")
        else:
            resolved_base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL")
            client_kwargs: dict[str, Any] = {"api_key": api_key}
            if resolved_base_url:
                client_kwargs["base_url"] = resolved_base_url
            self._client = anthropic.Anthropic(**client_kwargs)
            self._model = model or os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")

        self._max_tokens = max_tokens
        self._temperature = temperature
        self._conversations: dict[str, list[Message]] = {}

    # -- LLMProvider interface ------------------------------------------------

    def send(self, messages: list[Message], **kwargs: Any) -> str:
        """Send messages to Claude and return the assistant response text."""
        system_text: str | None = None
        api_messages: list[dict[str, str]] = []

        for msg in messages:
            if msg.role == "system":
                system_text = msg.content
            else:
                api_messages.append({"role": msg.role, "content": msg.content})

        create_kwargs: dict[str, Any] = {
            "model": kwargs.get("model", self._model),
            "max_tokens": kwargs.get("max_tokens", self._max_tokens),
            "temperature": kwargs.get("temperature", self._temperature),
            "messages": api_messages,
        }
        if system_text is not None:
            create_kwargs["system"] = system_text

        response = self._client.messages.create(**create_kwargs)

        # Extract text from content blocks.
        parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)

    @property
    def supports_conversations(self) -> bool:
        """Claude supports multi-turn conversations (client-side history)."""
        return True

    def new_conversation(self, system: str) -> str:
        """Create a new conversation with a system prompt, returning its ID."""
        cid = uuid.uuid4().hex
        self._conversations[cid] = [Message(role="system", content=system)]
        return cid

    def resume(self, conversation_id: str, message: str) -> str:
        """Append a user message to the conversation and return the response."""
        history = self._conversations.get(conversation_id)
        if history is None:
            raise KeyError(f"Unknown conversation ID: {conversation_id}")

        history.append(Message(role="user", content=message))
        response_text = self.send(list(history))
        history.append(Message(role="assistant", content=response_text))
        return response_text
