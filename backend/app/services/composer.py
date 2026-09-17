from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.session import AnswerMode


@dataclass
class ComposedAnswer:
    content: str
    mode: str
    sources: list[dict] = field(default_factory=list)
    validation: dict | None = None


class AnswerComposer:
    """Composes the final answer per mode + attaches sources."""

    def __init__(self) -> None:
        self.mode_templates: dict[AnswerMode, str] = {
            AnswerMode.QUICK: "{body}",
            AnswerMode.INTERVIEW: "{body}",
            AnswerMode.SENIOR: "{body}",
            AnswerMode.CODING: "{body}",
            AnswerMode.SCENARIO: "{body}",
        }

    async def compose(
        self,
        content: str,
        mode: AnswerMode,
        sources: list[dict] | None = None,
        validation: dict | None = None,
    ) -> ComposedAnswer:
        body = content.strip()
        if validation and not validation.get("passed", True):
            body = (
                f"{body}\n\n_Note: I could not fully verify this answer against the "
                "available documents. Questions marked with an asterisk should be confirmed._"
            )
        return ComposedAnswer(content=body, mode=mode.value, sources=sources or [], validation=validation)