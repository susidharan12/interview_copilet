from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.session import AnswerMode

TECHNICAL_TEMPLATE = """\
You are an experienced software engineer helping a candidate answer an interview question.
Be concise and interview-ready. Structure your answer as:

## Direct Answer
(1-2 sentences)

## Explanation
(short, technically accurate)

## Example
(a concrete, practical example if useful)

## Caveat
(one important trade-off or caveat)

## Possible Follow-up
(one likely follow-up question, if any)"""

SCENARIO_TEMPLATE = """\
You are a senior engineer helping a candidate walk through a scenario question.
Frame the answer like an experienced engineer explaining their approach:

1. Identify the situation and my immediate goal
2. Assumptions I would confirm / clarifications I might ask
3. Immediate risks to check
4. How I would investigate (evidence first)
5. Likely root causes
6. Immediate mitigation
7. Permanent solution
8. Monitoring and prevention
9. Trade-offs

Do NOT invent company-specific systems. If the situation depends on unknown
internals, say what I would check rather than fabricating details."""

CODING_TEMPLATE = """\
You are a coding-interview coach. Produce:
- Approach (algorithm/pattern + why)
- Complexity (time and space)
- Code in the language requested (markdown code block)
- Edge cases list
- Test cases (input → expected)

Prefer clean, correct code over cleverness. The code will be executed and
validated in an isolated sandbox."""

BEHAVIORAL_TEMPLATE = """\
You are helping a candidate answer a behavioral interview question using STAR.
Keep answers truthful and anchored to the candidate's actual profile.
Structure: Situation → Task → Action → Result (with a metric if known from the resume).
If the resume lacks the specific detail, say so and give a safe generic framing
instead of inventing a specific project."""

MODES: dict[AnswerMode, str] = {
    AnswerMode.QUICK: "Keep it to 1-2 sentences.",
    AnswerMode.INTERVIEW: "Direct answer + short explanation + example.",
    AnswerMode.SENIOR: "Answer + architecture/trade-offs + production considerations.",
    AnswerMode.CODING: "Approach + code + complexity + edge cases.",
    AnswerMode.SCENARIO: "Situation + investigation + action + solution + prevention.",
}

CATEGORY_TEMPLATES: dict[str, str] = {
    "technical": TECHNICAL_TEMPLATE,
    "coding": CODING_TEMPLATE,
    "debugging": SCENARIO_TEMPLATE,
    "system_design": SCENARIO_TEMPLATE,
    "architecture": SCENARIO_TEMPLATE,
    "scenario": SCENARIO_TEMPLATE,
    "behavioral": BEHAVIORAL_TEMPLATE,
    "project": TECHNICAL_TEMPLATE,
    "resume": BEHAVIORAL_TEMPLATE,
    "sql": CODING_TEMPLATE,
    "follow_up": TECHNICAL_TEMPLATE,
    "clarification": TECHNICAL_TEMPLATE,
    "unknown": TECHNICAL_TEMPLATE,
}


@dataclass
class EngineInput:
    question: str
    category: str
    mode: AnswerMode = AnswerMode.INTERVIEW
    context: str = ""
    memory_fragment: str = ""
    profile_fragment: str = ""
    job_fragment: str = ""
    conversation_fragment: str = ""
    technology: str | None = None
    difficulty: str | None = None
    language: str = "python"
    extra: dict = field(default_factory=dict)


def build_system_prompt(inp: EngineInput) -> str:
    base = CATEGORY_TEMPLATES.get(inp.category, TECHNICAL_TEMPLATE)
    mode_instruction = MODES.get(inp.mode, MODES[AnswerMode.INTERVIEW])
    return (
        f"{base}\n\nMode instruction: {mode_instruction}\n"
        f"Answer mode: {inp.mode.value}\n"
        f"Target technology: {inp.technology or 'general'}\n"
        f"Difficulty: {inp.difficulty or 'unknown'}\n"
        "Rules:\n"
        "- Never invent facts about the candidate's resume or projects.\n"
        "- Distinguish what is known from the user's own documents vs general knowledge.\n"
        "- If the required information is unavailable, say so explicitly and give a safe, general answer.\n"
    )


def build_user_prompt(inp: EngineInput) -> str:
    parts = [f"Question: {inp.question}"]
    if inp.conversation_fragment:
        parts.append(f"\nPrevious conversation:\n{inp.conversation_fragment}")
    if inp.memory_fragment:
        parts.append(f"\nMemory:\n{inp.memory_fragment}")
    if inp.profile_fragment:
        parts.append(f"\nCandidate profile (VERIFIED, from documents):\n{inp.profile_fragment}")
    if inp.job_fragment:
        parts.append(f"\nJob description:\n{inp.job_fragment}")
    if inp.context:
        parts.append(f"\nRetrieved knowledge (\u2014 cite when used):\n{inp.context}")
    else:
        parts.append("\n(No relevant documents were found. Answer from general knowledge, and state this.)")
    if "coding" in inp.category or inp.mode == AnswerMode.CODING:
        parts.append(f"\nCode language: {inp.language}")
    return "\n".join(parts)