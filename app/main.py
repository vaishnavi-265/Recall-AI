from fastapi import FastAPI, Query

from .database import init_db, open_tasks, project_timeline, search_memories
from .models import ConversationIngestRequest, IngestResponse, SearchResponse, TimelineResponse
from .service import ingest_conversation

app = FastAPI(
    title="Recall-AI",
    version="0.1.0",
    description="Searchable personal memory for user-authorized AI conversations.",
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "recall-ai"}


@app.post("/v1/conversations/ingest", response_model=IngestResponse)
def ingest(request: ConversationIngestRequest) -> IngestResponse:
    memories = ingest_conversation(request)
    return IngestResponse(
        conversation_id=request.conversation_id,
        memories_created=len(memories),
        memories=memories,
    )


@app.get("/v1/memories/search", response_model=SearchResponse)
def search(q: str = Query(min_length=1), limit: int = Query(default=20, ge=1, le=100)) -> SearchResponse:
    results = search_memories(q, limit=limit)
    return SearchResponse(query=q, count=len(results), results=results)


@app.get("/v1/timeline/{project}", response_model=TimelineResponse)
def timeline(project: str) -> TimelineResponse:
    events = project_timeline(project)
    return TimelineResponse(project=project, count=len(events), events=events)


@app.get("/v1/tasks/open")
def tasks() -> dict:
    results = open_tasks()
    return {"count": len(results), "tasks": [item.model_dump() for item in results]}
