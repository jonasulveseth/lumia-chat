from __future__ import annotations

from typing import Optional, List

from app.tools.base import Tool, ToolResult
from app.services.brain_service import BrainService
from app.utils.date_utils import (
    detect_swedish_date_filter,
    detect_swedish_date_filters,
)


class TimeQueryTool(Tool):
    """
    A tool that detects time/date intent in the user message and fetches
    relevant conversations from Brain filtered by the detected date(s).

    Produces a compact context block for the LLM.
    """

    name = "time_query"

    def __init__(self):
        self.brain = BrainService()

    def _has_time_intent(self, message: str) -> bool:
        msg = (message or "").lower()
        keywords = [
            "idag",
            "igår",
            "imorgon",
            "vilken dag",
            "datum",
            "den ",  # e.g. den 14e augusti
            "augusti",
            "september",
            "oktober",
            "november",
            "december",
            "januari",
            "februari",
            "mars",
            "april",
            "maj",
            "juni",
            "juli",
        ]
        return any(k in msg for k in keywords)

    async def maybe_run(self, user_id: str, message: str) -> Optional[ToolResult]:
        if not self._has_time_intent(message):
            return None

        dates: List[str] = detect_swedish_date_filters(message)
        date_filter = dates if len(dates) > 1 else (dates[0] if dates else detect_swedish_date_filter(message))

        # Fetch from Brain - don't rely on API date filter, we'll filter in code
        resp = await self.brain.query_quick_context(
            customer_id=user_id,
            question="conversation chat discussion today yesterday",  # Better search terms
            n_results=20,  # Get more results to filter from
            date_filter=None,  # Skip API date filter, we'll do it manually
        )

        if not resp or not (resp.sources or resp.results):
            return None

        lines: List[str] = []
        target_dates = date_filter if isinstance(date_filter, list) else ([date_filter] if date_filter else None)
        
        if resp.sources:
            for src in resp.sources:
                txt = src.get("content") or src.get("text") or ""
                if not txt:
                    continue
                meta = src.get("metadata") or {}
                src_date = meta.get("date")
                
                # Filter by target dates if specified
                if target_dates and src_date not in target_dates:
                    continue
                    
                # Add to results
                if src_date:
                    lines.append(f"- ({src_date}) {txt}")
                else:
                    lines.append(f"- {txt}")
                    
                # Limit results
                if len(lines) >= 8:
                    break
        elif resp.results:
            for txt in resp.results[:8]:
                lines.append(f"- {txt}")

        if not lines:
            return None

        block = "\n".join(lines)
        context_text = f"[TIME_QUERY]\nHämtade konversationer relaterade till begärt datum:\n{block}"
        return ToolResult(name=self.name, context_text=context_text)


