"""PoC de connectivité Bedrock via le ClaudeProvider patché.

Valide le tuyau LLM (creds AWS + Bedrock + ID de profil d'inférence), pas Ghidra.
Aucune clé Anthropic, aucun contournement : on passe par le canal AWS/Bedrock.
"""

from __future__ import annotations

import os
import sys

from re_agent.llm.claude import ClaudeProvider
from re_agent.llm.protocol import Message

# ID principal = §7 de la config Alain. Fallbacks au cas où le suffixe diffère.
MODELS = [
    os.environ.get("RE_AGENT_BEDROCK_MODEL", "us.anthropic.claude-opus-4-6-v1:0"),
    "us.anthropic.claude-opus-4-6-v1",
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
]
PROMPT = "Réponds exactement par le mot OK et rien d'autre."


def try_model(model: str) -> str:
    print(f"[*] Essai Bedrock modèle={model}")
    provider = ClaudeProvider(model=model, max_tokens=16, use_bedrock=True)
    return provider.send([Message(role="user", content=PROMPT)])


def main() -> int:
    seen: set[str] = set()
    for model in MODELS:
        if model in seen:
            continue
        seen.add(model)
        try:
            reply = try_model(model)
            print(f"[OK] {model} a répondu : {reply!r}")
            print("\n[SUCCESS] Bedrock fonctionne. Garde ce model id pour RE_AGENT_BEDROCK_MODEL.")
            return 0
        except Exception as exc:  # noqa: BLE001 - on capture tout pour diagnostiquer
            print(f"[ERR] {model} : {type(exc).__name__}: {str(exc)[:200]}\n")
    print("[FAIL] Aucun modèle Bedrock n'a répondu — voir l'erreur ci-dessus.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
