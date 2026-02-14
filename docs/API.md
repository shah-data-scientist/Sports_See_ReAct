# API Documentation

**Version**: 2.0
**Base URL**: `http://localhost:8002`
**Last Updated**: 2026-02-11

---

## Overview

Sports_See provides a FastAPI REST API for querying NBA statistics and managing conversations. The API supports:
- Hybrid RAG queries (SQL + Vector search)
- Conversation management (multi-turn context)
- Feedback collection (thumbs up/down)
- Automatic visualization generation

---

## Authentication

Currently **no authentication** required (development mode).

For production, consider:
- API key authentication
- Rate limiting per IP/key
- CORS configuration

---

## Base Endpoints

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "2.0"
}
```

### API Docs

```http
GET /docs
```

Interactive Swagger UI documentation.

```http
GET /redoc
```

ReDoc API documentation.

---

## Chat Endpoints

### Process Query

```http
POST /api/v1/chat
```

Main endpoint for processing user queries through the Hybrid RAG system.

**Request Body**:
```json
{
  "query": "Who are the top 5 scorers?",
  "k": 5,
  "include_sources": true,
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",  // optional
  "turn_number": 1  // optional
}
```

**Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | User's natural language question |
| `k` | integer | No | 5 | Number of search results to retrieve |
| `include_sources` | boolean | No | false | Include source documents in response |
| `conversation_id` | string (UUID) | No | null | UUID for multi-turn conversations |
| `turn_number` | integer | No | 1 | Current turn number in conversation |

**Response** (200 OK):
```json
{
  "answer": "The top 5 scorers this season are:\n1. Shai Gilgeous-Alexander (2,485 pts)\n2. Luka Dončić (2,370 pts)\n3. Giannis Antetokounmpo (2,329 pts)\n4. Kevin Durant (2,180 pts)\n5. Jayson Tatum (2,046 pts)",
  "sources": [
    {
      "content": "Statistical data from NBA database...",
      "metadata": {
        "source": "SQL",
        "table": "player_stats",
        "confidence": 1.0
      },
      "score": 100.0
    }
  ],
  "query_type": "statistical",
  "processing_time_ms": 1250,
  "generated_sql": "SELECT p.name, ps.pts FROM players p JOIN player_stats ps ON p.id = ps.player_id ORDER BY ps.pts DESC LIMIT 5",
  "visualization": {
    "pattern": "top_n",
    "viz_type": "horizontal_bar",
    "plot_json": "{\"data\":[...], \"layout\":{...}}",
    "plot_html": "<div>...</div>"
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Generated response text |
| `sources` | array | Source documents (if `include_sources=true`) |
| `query_type` | string | "statistical", "contextual", or "hybrid" |
| `processing_time_ms` | integer | Query processing time in milliseconds |
| `generated_sql` | string | SQL query (if SQL was used), null otherwise |
| `visualization` | object | Chart data (if applicable), null otherwise |

**Visualization Object**:

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | string | "top_n" or "player_comparison" |
| `viz_type` | string | "horizontal_bar", "comparison", etc. |
| `plot_json` | string | Plotly chart JSON (for programmatic use) |
| `plot_html` | string | HTML <div> for embedding in web pages |

**Error Responses**:

```json
// 400 Bad Request - Invalid input
{
  "detail": "Query cannot be empty"
}

// 429 Too Many Requests - Rate limit exceeded
{
  "detail": "Rate limit exceeded. Please wait before retrying."
}

// 500 Internal Server Error - Processing failure
{
  "detail": "Query processing failed after retries"
}
```

**Example Usage**:

```python
import requests

response = requests.post(
    "http://localhost:8002/api/v1/chat",
    json={
        "query": "Who are the top 5 scorers?",
        "k": 5,
        "include_sources": True
    }
)

data = response.json()
print(data["answer"])
print(data["generated_sql"])

# If visualization generated
if data["visualization"]:
    print(f"Chart type: {data['visualization']['viz_type']}")
```

**cURL Example**:

```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare Jokić and Embiid stats",
    "k": 5,
    "include_sources": true
  }'
```

---

## Conversation Endpoints

### Create Conversation

```http
POST /api/v1/conversation
```

Create a new conversation session.

**Request Body**:
```json
{
  "title": "NBA Statistics Discussion"  // optional
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "NBA Statistics Discussion",
  "created_at": "2026-02-11T10:30:00Z",
  "last_updated": "2026-02-11T10:30:00Z",
  "message_count": 0,
  "is_archived": false
}
```

### Get All Conversations

```http
GET /api/v1/conversation
```

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_archived` | boolean | false | Include archived conversations |
| `limit` | integer | 50 | Maximum conversations to return |

**Response** (200 OK):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "NBA Statistics Discussion",
    "created_at": "2026-02-11T10:30:00Z",
    "last_updated": "2026-02-11T10:35:00Z",
    "message_count": 5,
    "is_archived": false
  }
]
```

### Get Conversation Details

```http
GET /api/v1/conversation/{conversation_id}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "NBA Statistics Discussion",
  "created_at": "2026-02-11T10:30:00Z",
  "last_updated": "2026-02-11T10:35:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Who scored the most points this season?",
      "timestamp": "2026-02-11T10:30:15Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Shai Gilgeous-Alexander with 2,485 points.",
      "timestamp": "2026-02-11T10:30:18Z"
    }
  ],
  "is_archived": false
}
```

### Update Conversation

```http
PUT /api/v1/conversation/{conversation_id}
```

Update conversation metadata (title, archive status).

**Request Body**:
```json
{
  "title": "Updated Title",  // optional
  "is_archived": true  // optional
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Updated Title",
  "created_at": "2026-02-11T10:30:00Z",
  "last_updated": "2026-02-11T10:40:00Z",
  "message_count": 5,
  "is_archived": true
}
```

### Delete Conversation

```http
DELETE /api/v1/conversation/{conversation_id}
```

**Response** (204 No Content)

---

## Feedback Endpoints

### Submit Feedback

```http
POST /api/v1/feedback
```

Submit thumbs up/down feedback for a query response.

**Request Body**:
```json
{
  "query": "Who are the top 5 scorers?",
  "answer": "The top 5 scorers are...",
  "rating": 1,  // 1 = thumbs up, -1 = thumbs down
  "comment": "Very accurate and helpful!",  // optional
  "query_type": "statistical",  // optional
  "sources_used": ["SQL"]  // optional
}
```

**Response** (201 Created):
```json
{
  "id": 123,
  "query": "Who are the top 5 scorers?",
  "rating": 1,
  "comment": "Very accurate and helpful!",
  "timestamp": "2026-02-11T10:35:00Z"
}
```

### Get Feedback Stats

```http
GET /api/v1/feedback/stats
```

Get aggregated feedback statistics.

**Response** (200 OK):
```json
{
  "total_feedback": 150,
  "positive": 120,
  "negative": 30,
  "positive_rate": 0.80,
  "by_query_type": {
    "statistical": {
      "total": 100,
      "positive": 90,
      "negative": 10,
      "positive_rate": 0.90
    },
    "contextual": {
      "total": 50,
      "positive": 30,
      "negative": 20,
      "positive_rate": 0.60
    }
  }
}
```

---

## Data Models

### ChatRequest

```python
class ChatRequest(BaseModel):
    query: str
    k: int = 5
    include_sources: bool = False
    conversation_id: str | None = None
    turn_number: int = 1
```

### ChatResponse

```python
class ChatResponse(BaseModel):
    answer: str
    sources: list[SearchResult] = []
    query_type: str
    processing_time_ms: int
    generated_sql: str | None = None
    visualization: VisualizationData | None = None
```

### SearchResult

```python
class SearchResult(BaseModel):
    content: str
    metadata: dict[str, Any]
    score: float
```

### VisualizationData

```python
class VisualizationData(BaseModel):
    pattern: str  # "top_n" or "player_comparison"
    viz_type: str  # "horizontal_bar", "comparison"
    plot_json: str  # Plotly JSON
    plot_html: str  # HTML div
```

### Conversation

```python
class Conversation(BaseModel):
    id: str
    title: str
    created_at: datetime
    last_updated: datetime
    message_count: int = 0
    is_archived: bool = False
```

### ConversationMessage

```python
class ConversationMessage(BaseModel):
    id: int
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",  // optional
  "timestamp": "2026-02-11T10:35:00Z"  // optional
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_QUERY` | 400 | Query is empty or malformed |
| `INVALID_UUID` | 400 | Conversation ID is not a valid UUID |
| `CONVERSATION_NOT_FOUND` | 404 | Conversation does not exist |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests, retry later |
| `LLM_ERROR` | 500 | LLM API call failed after retries |
| `SQL_EXECUTION_ERROR` | 500 | SQL query execution failed |
| `VECTOR_SEARCH_ERROR` | 500 | Vector search failed |

---

## Rate Limiting

### Current Limits (Development)

- **Gemini API**: 15 requests per minute (free tier)
- **Mistral API**: 60 requests per minute (embeddings)

### Production Recommendations

```python
# Per-IP rate limiting
- 60 requests per minute per IP
- 1000 requests per hour per IP

# Per-API-key rate limiting (when auth is added)
- 300 requests per minute per key
- 10000 requests per hour per key
```

### Retry Logic (Built-in)

The API automatically retries on rate limit errors:
- Max 3 retries
- Exponential backoff: 2s → 4s → 8s
- Returns 429 if all retries exhausted

---

## Testing

### Test Client Example

```python
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_chat_endpoint():
    response = client.post(
        "/api/v1/chat",
        json={
            "query": "Who are the top 5 scorers?",
            "k": 5,
            "include_sources": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["query_type"] == "statistical"
```

### Integration Test Example

```python
import requests

def test_full_conversation():
    # 1. Create conversation
    conv_response = requests.post(
        "http://localhost:8002/api/v1/conversation",
        json={"title": "Test Conversation"}
    )
    conv_id = conv_response.json()["id"]

    # 2. First query
    response1 = requests.post(
        "http://localhost:8002/api/v1/chat",
        json={
            "query": "Who scored the most points?",
            "conversation_id": conv_id,
            "turn_number": 1
        }
    )

    # 3. Follow-up query (pronoun resolution)
    response2 = requests.post(
        "http://localhost:8002/api/v1/chat",
        json={
            "query": "What about his assists?",
            "conversation_id": conv_id,
            "turn_number": 2
        }
    )

    assert "Shai" in response1.json()["answer"]
    assert "assists" in response2.json()["answer"]
```

---

## Deployment

### Development Server

```bash
# Standard mode
poetry run uvicorn src.api.main:app --reload --port 8002

# With auto-reload and debug
poetry run uvicorn src.api.main:app --reload --port 8002 --log-level debug
```

### Production Server

```bash
# Gunicorn with Uvicorn workers
poetry run gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8002 \
  --access-logfile - \
  --error-logfile -
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

EXPOSE 8002

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

---

## Best Practices

### 1. Conversation Management

```python
# Always use conversation_id for multi-turn conversations
conversation_id = create_conversation()

# Increment turn_number for each query
for turn in range(1, 6):
    response = chat(
        query=user_input,
        conversation_id=conversation_id,
        turn_number=turn
    )
```

### 2. Error Handling

```python
import requests
from requests.exceptions import RequestException

def safe_query(query: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8002/api/v1/chat",
                json={"query": query},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 3. Visualization Handling

```python
response = chat(query="Who are the top 5 scorers?")

if response["visualization"]:
    # Option 1: Use Plotly JSON (for programmatic manipulation)
    import plotly.graph_objects as go
    fig = go.Figure(json.loads(response["visualization"]["plot_json"]))
    fig.show()

    # Option 2: Use HTML (for web embedding)
    html = response["visualization"]["plot_html"]
    # Embed in web page
```

---

## API Changelog

### Version 2.0 (2026-02-11)
- ✅ Added `generated_sql` field to ChatResponse
- ✅ Added `visualization` field to ChatResponse
- ✅ Added conversation endpoints (CRUD)
- ✅ Added feedback endpoints
- ✅ Automatic retry logic with exponential backoff
- ✅ Conversation-aware query processing

### Version 1.0 (2026-01-21)
- Initial API release
- Basic chat endpoint
- Vector search only

---

**Maintainer**: Shahu
**Version**: 2.0
**Last Updated**: 2026-02-11
