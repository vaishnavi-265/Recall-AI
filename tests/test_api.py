import os
from pathlib import Path

TEST_DB = Path("test_recall_ai.db")
os.environ["RECALL_AI_DB"] = str(TEST_DB)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def setup_function():
    if TEST_DB.exists():
        TEST_DB.unlink()
    with client:
        pass


def teardown_function():
    if TEST_DB.exists():
        TEST_DB.unlink()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_search_timeline_and_tasks():
    payload = {
        "conversation_id": "conv-001",
        "provider": "gemini",
        "project": "healthcare-rag",
        "messages": [
            {"role": "user", "content": "We decided to use Pinecone for vector retrieval."},
            {"role": "assistant", "content": "The system must redact patient PII."},
            {"role": "user", "content": "Next we need to implement authentication."}
        ]
    }

    with client:
        ingest = client.post("/v1/conversations/ingest", json=payload)
        assert ingest.status_code == 200
        assert ingest.json()["memories_created"] == 3

        search = client.get("/v1/memories/search", params={"q": "Pinecone"})
        assert search.status_code == 200
        assert search.json()["count"] >= 1

        timeline = client.get("/v1/timeline/healthcare-rag")
        assert timeline.status_code == 200
        assert timeline.json()["count"] == 3

        tasks = client.get("/v1/tasks/open")
        assert tasks.status_code == 200
        assert tasks.json()["count"] >= 1
