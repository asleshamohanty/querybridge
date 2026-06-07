import re

class InjectionError(Exception):
    pass

_INJECTION_PATTERNS = [
    r"ignore (all |previous |above |prior )?instructions?",
    r"you are now",
    r"disregard (your |all )?rules?",
    r"system prompt",
    r"act as",
    r"pretend (you are|to be)",
    r"jailbreak",
    r"forget everything",
    r"new persona",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]
_STRIP_CHARS = re.compile(r"[;'\"\\]")
MAX_QUESTION_LENGTH = 500


def sanitise(question: str) -> str:
    question = question.strip()[:MAX_QUESTION_LENGTH]

    for pattern in _COMPILED:
        if pattern.search(question):
            raise InjectionError(
                "Your question contains text that looks like a prompt-injection attempt. "
                "Please rephrase as a plain data question."
            )

    question = _STRIP_CHARS.sub("", question)
    return question
