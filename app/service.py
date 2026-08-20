import re

from .database import insert_memory
from .models import ConversationIngestRequest, Memory

DECISION_MARKERS = ("decided", "decision", "we will", "we'll", "use ", "switch to", "moved to")
REQUIREMENT_MARKERS = ("must", "need to", "required", "requirement", "should")
TASK_MARKERS = ("todo", "to do", "next", "need to", "will implement", "will add", "pending")
FACT_MARKERS = ("remember", "is ", "are ", "using", "works with", "currently")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _classify(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in TASK_MARKERS):
        return "task"
    if any(marker in lowered for marker in REQUIREMENT_MARKERS):
        return "requirement"
    if any(marker in lowered for marker in DECISION_MARKERS):
        return "decision"
    if any(marker in lowered for marker in FACT_MARKERS):
        return "fact"
    return "note"


def extract_memories(request: ConversationIngestRequest) -> list[Memory]:
    seen: set[tuple[str, str]] = set()
    extracted: list[Memory] = []

    for message in request.messages:
        clean = _clean(message.content)
        if len(clean) < 8:
            continue

        kind = _classify(clean)
        key = (kind, clean.lower())
        if key in seen:
            continue
        seen.add(key)

        extracted.append(
            Memory(
                kind=kind,
                content=clean[:1000],
                project=request.project,
                provider=request.provider,
                source_conversation_id=request.conversation_id,
            )
        )

    return extracted


def ingest_conversation(request: ConversationIngestRequest) -> list[Memory]:
    return [insert_memory(memory) for memory in extract_memories(request)]
