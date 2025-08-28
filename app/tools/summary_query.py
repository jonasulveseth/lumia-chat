from __future__ import annotations

from typing import Optional, List

from app.tools.base import Tool, ToolResult
from app.services.brain_service import BrainService


class SummaryQueryTool(Tool):
    """
    Detects intent to get a general summary of user's history/topics and
    fetches broader context from Brain (no strict date filter).

    Produces a compact bullet list and a short theme line for the LLM.
    """

    name = "summary_query"

    def __init__(self):
        self.brain = BrainService()

    def _has_summary_intent(self, message: str) -> bool:
        msg = (message or "").lower()
        keywords = [
            "sammanfatta",
            "sammanfattning",
            "summera",
            "vad har vi pratat om",
            "vad har jag pratat om",
            "vad har jag sagt",
            "viktiga områden",
            "fokus",
            "vad vet du om mig",
            "tidigare",
            "historik",
        ]
        return any(k in msg for k in keywords)

    async def maybe_run(self, user_id: str, message: str) -> Optional[ToolResult]:
        if not self._has_summary_intent(message):
            return None

        # Broader pull for variety
        resp = await self.brain.query_quick_context(
            customer_id=user_id,
            question="user previous conversation topics and interests; summarise",
            n_results=10,  # Increased for comprehensive summaries with fast /search endpoint
        )

        if not resp or not (resp.sources or resp.results):
            return None

        bullets: List[str] = []
        dates: List[str] = []
        if resp.sources:
            for src in resp.sources[:10]:
                txt = src.get("content") or src.get("text") or ""
                if not txt:
                    continue
                meta = (src.get("metadata") or {})
                date = meta.get("date") or meta.get("timestamp")
                if date:
                    bullets.append(f"- ({date}) {txt}")
                    dates.append(str(date))
                else:
                    bullets.append(f"- {txt}")
        elif resp.results:
            for txt in resp.results[:10]:
                bullets.append(f"- {txt}")

        if not bullets:
            return None

        # Provide a very small hint for themes without heavy summarisation
        theme_hint = "Teman: projekt/teknik, personliga mål/hälsa, arbetsflöden/säljpipe"  # lightweight prior; LLM refines
        context_text = "[SUMMARY_QUERY]\n" + "\n".join(bullets) + f"\n\n{theme_hint}"
        return ToolResult(name=self.name, context_text=context_text)


