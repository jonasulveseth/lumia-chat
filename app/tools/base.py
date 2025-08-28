"""
Lightweight tool/function interface to enable model-agnostic function-calling.

The goal is to support simple tools that can be triggered by intent patterns
and provide structured context for the LLM, independent of the underlying
model (works with local Ollama as well as hosted models).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolResult:
    """Represents the text context produced by a tool.

    The text is meant to be injected into the LLM context directly.
    """

    name: str
    context_text: str


class Tool:
    """Base class for tools. Subclasses implement async run methods."""

    name: str = "tool"

    async def maybe_run(self, *args, **kwargs) -> Optional[ToolResult]:
        raise NotImplementedError


