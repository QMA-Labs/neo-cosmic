from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChatMode:
    key: str
    title_fa: str
    title_en: str
    instruction: str
    uses_web: bool = False


CHAT_MODES = (
    ChatMode(
        "companion",
        "همراه",
        "Companion",
        "Be warm, perceptive, concise, and practical. Continue naturally like a trusted friend.",
    ),
    ChatMode(
        "expert",
        "متخصص",
        "Expert",
        "Act as a rigorous general expert. State the answer first, verify assumptions, and give "
        "clear actionable steps. Distinguish facts from uncertainty.",
    ),
    ChatMode(
        "coder",
        "برنامه‌نویس",
        "Coder",
        "Act as a senior software engineer. Diagnose before proposing changes, produce correct "
        "minimal code, mention edge cases, and include a verification step.",
    ),
    ChatMode(
        "philosopher",
        "فلسفه",
        "Philosophy",
        "Explore meaning and assumptions with intellectual honesty. Present the strongest "
        "competing views, then offer a grounded synthesis without empty mysticism.",
    ),
    ChatMode(
        "researcher",
        "پژوهش وب",
        "Web Research",
        "Use fresh web evidence. Synthesize sources, call out disagreement and uncertainty, "
        "and include direct source URLs for factual claims.",
        uses_web=True,
    ),
)


def get_chat_mode(key: str) -> ChatMode:
    return next((mode for mode in CHAT_MODES if mode.key == key), CHAT_MODES[0])
