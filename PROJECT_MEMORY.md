# PROJECT MEMORY - Sports_See (NBA RAG Assistant)

**Project Type:** RAG Chatbot Application
**Primary Language:** Python 3.11+
**Frameworks:** Streamlit (UI), FastAPI (REST API)
**AI Model:** Gemini 2.0 Flash (upgraded from Mistral AI)
**Vector DB:** FAISS
**SQL DB:** SQLite (nba_stats.db - 569 players, 30 teams)
**Feedback DB:** SQLite (interactions.db - SQLAlchemy)
**Last Updated:** 2026-02-13
**Status:** Production Ready

---

## 📋 Project Requirements

**Last Audit:** 2026-01-26
**Requirements Status:** In Progress

### Initial Requirements

1. **RAG System Implementation**
   - Retrieval-Augmented Generation using FAISS for semantic search
   - Mistral AI for embeddings and response generation
   - Support for multiple document formats (PDF, TXT, DOCX, CSV, JSON, XLSX)

2. **Chat Interface**
   - Streamlit-based web interface
   - Conversation history management
   - Real-time response generation
   - NBA-specific domain expertise

3. **Document Processing**
   - Document indexing pipeline
   - Chunk-based document storage
   - Vector embeddings generation
   - FAISS index management

4. **API Integration**
   - Mistral API for LLM capabilities
   - FastAPI REST API for programmatic access
   - Environment-based configuration (.env)
   - Configurable model selection

5. **Feedback System**
   - Chat history logging to SQLite database
   - Thumbs up/down feedback buttons
   - Comment input for negative feedback
   - Feedback statistics dashboard

### Functional Requirements

- [x] Load and parse multiple document formats
- [x] Generate embeddings for document chunks
- [x] Build and maintain FAISS vector index
- [x] Semantic search with configurable top-k results
- [x] Context-aware response generation
- [x] Streamlit chat interface
- [x] Environment-based configuration
- [x] FastAPI REST API
- [x] Chat history logging
- [x] User feedback collection

### Non-Functional Requirements

- [x] Type hints throughout codebase (Python 3.10+ style)
- [x] Clean Architecture (API → Services → Repositories → Models)
- [x] Comprehensive test coverage using pytest
- [x] Code quality via ruff/black/mypy
- [x] Documentation consistency
- [x] Security: API key protection, input validation, SSRF protection

### Security/Compliance Requirements

- **Security Standard:** OWASP Top 10
- **Compliance:** None (internal tool)
- **Data Handling:** NBA statistics and Reddit posts (public data)
- **API Keys:** Secured via .env file (gitignored)
- **Input Validation:** Pydantic models with constraints
- **SSRF Protection:** URL validation for external requests

### Technical Stack

**Core:**
- Python 3.11+
- Poetry for dependency management
- Streamlit 1.44.1
- FastAPI ^0.115.0
- Uvicorn ^0.34.0
- Pydantic ^2.0.0
- Pydantic-settings ^2.0.0

**AI/ML:**
- Mistral AI 0.4.2
- FAISS-CPU 1.10.0
- LangChain 0.3.23

**Database:**
- SQLAlchemy ^2.0.46 (feedback storage)
- SQLite (interactions.db)

**Testing:**
- pytest ^8.0.0
- pytest-cov ^6.0.0
- pytest-mock ^3.0.0

**Code Quality:**
- ruff ^0.8.0
- black ^24.10.0
- mypy ^1.11.0

---

## 📂 Project Structure

```
Sports_See/
├── src/
│   ├── api/                         # FastAPI REST endpoints
│   │   ├── main.py                  # App initialization, routes
│   │   └── routes/                  # API route modules
│   │       ├── chat.py              # Chat endpoints
│   │       └── feedback.py          # Feedback endpoints
│   ├── core/                        # Configuration and utilities
│   │   ├── config.py                # Settings via Pydantic
│   │   ├── security.py              # Input validation, SSRF protection
│   │   ├── exceptions.py            # Custom exception types
│   │   └── observability.py         # Logfire integration
│   ├── models/                      # Pydantic models
│   │   ├── chat.py                  # ChatRequest, ChatResponse, SearchResult
│   │   └── feedback.py              # SQLAlchemy + Pydantic feedback models
│   ├── repositories/                # Data access layer
│   │   ├── vector_store.py          # FAISS vector storage
│   │   └── feedback.py              # SQLite feedback repository
│   ├── services/                    # Business logic
│   │   ├── chat.py                  # RAG pipeline orchestration
│   │   ├── embedding.py             # Mistral embeddings
│   │   ├── query_classifier.py      # Query type classification
│   │   ├── query_expansion.py       # NBA-specific query expansion
│   │   ├── conversation.py          # Conversation lifecycle management
│   │   └── visualization_service.py # Chart generation for SQL results
│   ├── tools/                       # External tools
│   │   └── sql_tool.py              # LangChain SQL agent for NBA stats
│   ├── pipeline/                    # Data ingestion pipeline
│   │   ├── chunker.py               # Document chunking
│   │   ├── data_loader.py           # Multi-format loader
│   │   ├── indexer.py               # FAISS indexer
│   │   └── models.py                # Document, Chunk, ChunkMetadata
│   ├── ui/                          # Streamlit application
│   │   ├── app.py                   # Main UI + session state
│   │   └── api_client.py            # API client for Streamlit
│   └── evaluation/                  # RAG quality evaluation
│       ├── models.py                # Evaluation data structures
│       └── runners/                 # Evaluation runners
│           ├── run_sql_evaluation.py    # SQL test suite runner
│           ├── run_vector_evaluation.py # Vector test suite runner
│           └── run_hybrid_evaluation.py # Hybrid test suite runner
├── tests/                           # Pytest test suite
│   ├── core/                        # Core functionality tests
│   ├── services/                    # Service layer tests
│   ├── integration/                 # Integration tests
│   ├── e2e/                         # End-to-end tests
│   └── ui/                          # UI tests
├── scripts/                         # Utility scripts
├── database/                        # SQLite databases (gitignored)
│   ├── nba_stats.db                 # NBA player/team statistics
│   └── interactions.db              # Feedback/conversation history
├── data/                            # Data directory
│   ├── inputs/                      # Raw documents (PDFs, Excel)
│   ├── vector/                      # FAISS index + pickled chunks
│   └── sql/                         # SQLite databases
├── docs/                            # Documentation
├── .streamlit/                      # Streamlit config
│   └── config.toml                  # UI port (8501), theme
├── pyproject.toml                   # Poetry dependencies + tool configs
├── .env                             # API keys (gitignored)
├── README.md                        # Main documentation (500 lines)
├── PROJECT_MEMORY.md                # This file (APPEND ONLY)
└── CHANGELOG.md                     # Version history

```

**Key Implementation Files:**
- `chat.py`: Hybrid RAG pipeline (SQL + Vector) with query classification
- `query_classifier.py`: Routes queries to SQL, Vector, or Hybrid
- `sql_tool.py`: LangChain SQL agent for NBA statistics
- `vector_store.py`: FAISS search with 3-signal ranking (cosine + BM25 + metadata)
- `feedback.py`: SQLAlchemy ORM + Pydantic models for feedback
- `embedding.py`: Mistral AI embedding service
- `feedback.py`: SQLite feedback repository with session management
- `app.py`: Streamlit UI with conversation management
- `main.py`: FastAPI application with CORS, health checks

---

## 🏗️ Architecture

### Overview

Clean Architecture with clear separation of concerns:

1. **API Layer** (FastAPI)
   - HTTP endpoints
   - Request validation (Pydantic)
   - Error handling
   - CORS configuration

2. **Service Layer**
   - Business logic
   - RAG pipeline orchestration
   - Query classification and routing
   - LLM interaction

3. **Repository Layer**
   - FAISS vector store
   - Feedback database (SQLite)
   - Conversation history

4. **Model Layer**
   - Pydantic models for validation
   - SQLAlchemy ORM for persistence
   - Type safety

### Data Flow

```
User Query
    ↓
FastAPI Endpoint (validation)
    ↓
ChatService (RAG orchestration)
    ↓
┌───────────────────┬──────────────────┬──────────────────┐
│  Query Classifier │                  │                  │
└───────────────────┘                  │                  │
         ↓                              │                  │
    ┌────────┬────────┬────────┐       │                  │
    │        │        │         │       │                  │
SQL_ONLY  CONTEXTUAL  HYBRID  GREETING │                  │
    │        │        │         │       │                  │
    ↓        ↓        ↓         ↓       │                  │
SQL Tool  Vector   Both+LLM   Simple   │                  │
         Search    Synthesis  Response │                  │
    │        │        │         │       │                  │
    └────────┴────────┴─────────┘       │                  │
              ↓                          │                  │
         LLM Response                    │                  │
              ↓                          │                  │
       Post-processing                   │                  │
       (citations, hedging)              │                  │
              ↓                          │                  │
         Return Response                 │                  │
              ↓                          │                  │
    Save to Feedback DB ←────────────────┘                  │
              ↓                                             │
    Visualization Service (SQL queries) ←──────────────────┘
```

### Design Patterns

1. **Repository Pattern**: Data access abstraction (vector_store.py, feedback.py)
2. **Service Layer**: Business logic separation (chat.py, embedding.py)
3. **Dependency Injection**: Service initialization with optional dependencies
4. **Factory Pattern**: Lazy initialization of heavy dependencies (Gemini client, SQL tool)
5. **Strategy Pattern**: Query routing based on classification (SQL/Vector/Hybrid)

---

## 🔍 Key Features

### 1. Hybrid RAG Pipeline (SQL + Vector Search)

**Query Classification** → Routes to appropriate data source:
- **STATISTICAL**: SQL database (LangChain SQL agent)
- **CONTEXTUAL**: Vector search (FAISS + Mistral embeddings)
- **HYBRID**: Both SQL + Vector (synthesized response)
- **GREETING**: Simple response (no RAG)

**Example Queries**:
- "Who has the most rebounds?" → SQL_ONLY
- "Why is LeBron effective?" → CONTEXTUAL
- "Top 5 scorers and why they're effective" → HYBRID
- "Who is LeBron?" → HYBRID (biographical with stats)

### 2. Conversation History

- SQLite-based conversation tracking
- Auto-saves query/response/sources for each turn
- Follow-up query resolution (pronoun replacement)
- Conversation context included in prompts (last 5 turns)

### 3. Query Expansion

**NBA-specific term expansion** for better keyword matching:
- "LeBron" → "LeBron James | King James | Lakers #23"
- "Warriors" → "Golden State Warriors | GSW | Dubs"
- Smart expansion based on query length (aggressive for short, minimal for long)

### 4. 3-Signal Hybrid Ranking

**Vector search uses weighted scoring**:
- **Cosine similarity** (50%): Semantic match via FAISS
- **BM25 term matching** (35%): Exact keyword relevance
- **Metadata boost** (15%): Reddit upvotes, NBA official sources

### 5. SQLite for Feedback

- SQLAlchemy ORM for clean data access
- Thumbs up/down + comment collection
- Feedback statistics dashboard in UI
- Conversation history for follow-up queries

### 6. Adaptive K Selection

**Complexity-based retrieval**:
- Simple queries ("who scored most"): k=3
- Moderate queries ("compare X and Y"): k=5
- Complex queries ("explain strategy"): k=7-9

---

## 📊 Testing

**Test Suite**: 171 tests, all passing
**Coverage**: 78.5% overall (target: 80%)

### Test Organization

```
tests/
├── core/              # Config, exceptions, security (19 tests)
├── services/          # Business logic (52 tests)
├── integration/       # API contract validation (8 tests)
├── e2e/               # End-to-end workflows (12 tests)
└── ui/                # Streamlit app (5 tests)
```

### Coverage Enforcement

**Pre-commit hook** (`check_coverage_thresholds.py`):
- Tier1 (critical): services, api, core, models, repositories, tools ≥77%
- Tier2 (standard): pipeline, evaluation, utils ≥24%
- Tier3 (best effort): ui (excluded, requires live browser)
- Config: `coverage_thresholds.toml`

### Excluded Tests

- `test_vector_store.py` - FAISS + torch AVX2 crash on Windows
- `test_improvements.py` - Experimental/archived
- `test_classifier_debug.py` - Debug utility
- `test_sql_conversation_demo.py` - Manual demo script

---

## 🛠️ Known Issues & Workarounds

### 1. FAISS + torch AVX2 Crash (Windows)

**Problem**: Importing `easyocr` (which uses `torch`) at module level alongside FAISS crashes process
**Solution**: Lazy-load easyocr only when OCR is needed (inside functions)
**Files**: `data_loader.py`

### 2. Windows SQLite File Locking

**Problem**: `PermissionError [WinError 32]` in tests due to SQLite locking
**Solution**: Add `repo.close()` to dispose SQLAlchemy engine before temp dir cleanup
**Files**: Test fixtures in `conftest.py`

### 3. FastAPI Circular Imports

**Problem**: Importing `get_chat_service` from `main.py` causes circular dependency
**Solution**: Extract shared dependencies to separate `dependencies.py` module
**Files**: `src/api/dependencies.py` (if created)

---

## 🚀 Performance Metrics

### Vector Search
- **Indexing**: ~30 seconds for 5 NBA docs (3 PDFs + 2 Reddit posts, 5 chunks total)
- **Query latency**: ~150ms (embedding + FAISS search + reranking)
- **Index size**: 1.7MB (5 chunks, 1024-dim Mistral embeddings)

### SQL Queries
- **Query performance**: 10-20ms (local SQLite)
- **Database size**: 2.1MB (569 players, 30 teams, player_stats)

### LLM Response
- **Latency**: 2-5 seconds (Gemini 2.0 Flash)
- **Rate limits**: 15 RPM (free tier)
- **Retry logic**: Exponential backoff (2s → 4s → 8s, max 30s)

### End-to-End
- **Total latency**: 2-7 seconds (query classification → search → LLM → post-processing)
- **Conversation history**: <100ms overhead (SQLite query + pronoun resolution)

---

## 📝 Change Log Summary

### 2026-02-13: SQL Test Case Remediations
- Database normalization (Phase 2) completed
- Team query fixes (8/8 tests passing)
- 30 teams, 569 players verified in database
- SQL performance issue remediations (Issues #1-#10)

### 2026-02-12: Vector Remediation (Phase 1 & 2)
- Query classifier enhancements (greeting, opinion, biographical detection)
- 3-signal hybrid ranking (cosine + BM25 + metadata)
- Adaptive K selection based on query complexity
- Source grounding in all prompts

### 2026-02-11: SQL Evaluation Results
- 48/48 test cases successful (100% execution)
- 97.9% classification accuracy (47/48 sql_only)
- Retry logic eliminated all 429 failures

### 2026-02-07: Phase 2 SQL Integration
- Excel data integration (nba_stats.db)
- LangChain SQL tool for statistical queries
- Query classifier (SQL/Vector/Hybrid routing)
- Conversation history support

### 2026-02-06: RAGAS Evaluation & Logfire
- RAGAS evaluation framework
- Logfire observability integration
- Data pipeline refactoring

---

## Update: 2026-02-06 — RAGAS Evaluation, Data Pipeline, Logfire Observability

### Added

**`src/evaluation/`** — RAGAS-based RAG quality evaluation
- `models.py`: TestCategory (simple/complex/noisy), EvaluationTestCase, EvaluationSample, MetricScores, CategoryResult, EvaluationReport
- `sql_evaluation.py`: SQL test suite runner (80 test cases)
- `runners/`: Evaluation execution with JSON/MD output
- Test categories: team_queries, player_stats, rankings, aggregations, comparisons, glossary, definitional, contextual

**`src/core/observability.py`** — Logfire integration
- Automatic instrumentation for FastAPI endpoints
- Distributed tracing for RAG pipeline
- LLM call tracking (latency, tokens, errors)

**`src/pipeline/`** — Refactored data ingestion
- `data_loader.py`: Multi-format loading (PDF, TXT, Excel, etc.) with easyOCR lazy-loading
- `chunker.py`: Semantic chunking with overlap
- `indexer.py`: FAISS index building
- `models.py`: Document, Chunk, ChunkMetadata

**`src/tools/sql_tool.py`** — LangChain SQL agent for NBA statistics
- Natural language → SQL generation
- SQLite query execution
- Table schema awareness (players, teams, player_stats)

**`src/services/query_classifier.py`** — Query type classification
- Patterns: STATISTICAL (SQL), CONTEXTUAL (Vector), HYBRID (both)
- Returns ClassificationResult with query_type, complexity_k, max_expansions

**`src/services/conversation.py`** — Conversation lifecycle management
- Start/get/list conversations
- Conversation history retrieval
- Follow-up query resolution

**`src/services/visualization_service.py`** — Chart generation for SQL results
- Plotly visualizations (bar, pie, scatter, line)
- Pattern detection (rankings, comparisons, trends, distributions)
- JSON + HTML output for Streamlit rendering

### Changed

**`src/services/chat.py`** — Enhanced RAG pipeline
- Query classification and routing (SQL/Vector/Hybrid)
- Conversation history integration
- Follow-up query rewriting
- Smart fallback (SQL → Vector if LLM can't parse)
- Post-processing (citations, hedging removal)

**`src/repositories/vector_store.py`** — Improved search
- 3-signal hybrid ranking (cosine + BM25 + metadata)
- Adaptive K selection
- Query expansion integration

**`src/ui/app.py`** — UI enhancements
- Conversation management
- Follow-up query support
- Visualization rendering
- Feedback statistics dashboard

### Tests

**Coverage**: 78.5% overall (171 tests)
- New: test_evaluation (16), test_pipeline (13), test_pipeline_models (19)
- New: test_query_classifier (15), test_conversation (8), test_visualization_service (6)
- Enhanced: test_chat_service (23 → 30 tests)

**Excluded**: test_vector_store.py (FAISS AVX2 crash), test_improvements.py (archived)

### Data

**`data/sql/nba_stats.db`** — NBA statistics database
- 569 players across 30 teams
- player_stats table with 25+ statistics per player
- teams table with 30 NBA franchises

**`data/inputs/`** — Raw source documents
- NBA rulebook PDF
- NBA official guidelines PDF
- NBA glossary PDF
- Reddit posts (2 Excel files)

---

## Update: 2026-02-07 — Phase 2: Excel Data Integration & SQL Tool

### Problem

Existing RAG system only handles **unstructured documents** (PDFs, Reddit posts) via vector search. Users couldn't ask precise statistical questions like "Who has the most rebounds?" or "Show me Lakers stats" because the system had no structured data source.

Added **structured NBA statistics querying** via SQL database to complement existing vector search (unstructured documents). Users can now ask precise statistical questions ("Who has the most rebounds?") alongside contextual questions ("Why is he effective?").

### Solution Architecture

**1. Database Normalization (players → teams relationship)**
- `players` table: id, name, team_id, age, games_played
- `teams` table: id, abbreviation, full_name, city
- `player_stats` table: player_id (FK), pts, reb, ast, fg_pct, etc.
- SQLAlchemy ORM models with relationships

**2. Excel Data Ingestion (`scripts/load_nba_stats.py`)**
- Reads `NBA_2024_Stats.xlsx`
- Extracts team names → normalizes to 3-letter abbreviations (LAL, BOS, GSW)
- Inserts into SQLite database
- Result: 569 players, 30 teams

**4. LangChain SQL Tool (`src/tools/sql_tool.py`)**
- Uses Gemini 2.0 Flash for natural language → SQL
- Schema awareness (knows players, teams, player_stats tables)
- SQL validation and execution
- Error handling with fallback

**5. Query Classifier (`src/services/query_classifier.py`)**
- Routes queries to SQL, Vector, or Hybrid
- Statistical patterns: "top N", "average", "compare", "how many"
- Contextual patterns: "why", "explain", "strategy", "opinion"
- Greeting detection

**6. Hybrid RAG Pipeline (`src/services/chat.py`)**
- Classification → SQL/Vector/Hybrid routing
- SQL results formatting (scalar, single record, top-N)
- Smart fallback (SQL error → Vector search)
- LLM synthesis (SQL + Vector for HYBRID queries)
- Post-processing (hedging removal, citation formatting)

### Results

**Capabilities Unlocked**:
- ✅ "Who has the most rebounds?" → SQL query (exact answer)
- ✅ "Why is LeBron effective?" → Vector search (contextual analysis)
- ✅ "Top 5 scorers and why they're effective" → Hybrid (stats + analysis)
- ✅ "Show me Lakers stats" → SQL query (team aggregation)
- ✅ Team name flexibility: "Lakers", "LAL", "Los Angeles Lakers" all work

**Test Results**:
- SQL evaluation: 48/48 successful (100% execution)
- Classification accuracy: 97.9% (47/48 sql_only)
- Team queries: 8/8 passing (all 30 teams present)

**Performance**:
- SQL query latency: 10-20ms (local SQLite)
- End-to-end latency: 2-7 seconds (with LLM synthesis)

### Files Changed

**New Files**:
- `src/tools/sql_tool.py` — LangChain SQL agent
- `src/services/query_classifier.py` — Query routing
- `src/services/conversation.py` — Conversation history
- `src/services/visualization_service.py` — Chart generation
- `scripts/load_nba_stats.py` — Data ingestion
- `data/sql/nba_stats.db` — SQLite database

**Modified Files**:
- `src/services/chat.py` — Hybrid RAG pipeline
- `src/ui/app.py` — Conversation management
- `src/repositories/vector_store.py` — 3-signal ranking
- `src/models/chat.py` — Added generated_sql, visualization fields

**Test Files**:
- `tests/services/test_query_classifier.py` (15 tests)
- `tests/services/test_conversation.py` (8 tests)
- `tests/services/test_visualization_service.py` (6 tests)
- `tests/integration/test_feedback_api_contract.py` (3 tests)

---

## Phase 5 Results (2026-02-08)

Achieved **major improvements** in faithfulness (+37%) and complex query handling by optimizing system prompt. Introduced **quick-test methodology** to rapidly iterate on prompt variations before full evaluation.

### Metrics (75 test cases)

| Metric | Phase 4 (Baseline) | Phase 5 (Optimized) | Change |
|--------|-------------------|---------------------|--------|
| **Answer Relevancy** | 52.09% | 51.88% | -0.21% ❌ |
| **Faithfulness** | 59.06% | **96.03%** | **+36.97%** ✅ |
| **Context Precision** | 43.03% | 41.92% | -1.11% ❌ |
| **Context Recall** | 43.75% | 42.14% | -1.61% ❌ |

**Biggest Win**: Faithfulness jumped from 59% → 96% (+37pp)

### By Category

| Category | Relevancy | Faithfulness | Precision | Recall |
|----------|-----------|-------------|-----------|--------|
| **Simple** | 54.6% (-3.2) | **98.6%** (+34.1) ✅ | 48.5% (+2.6) | 47.2% (-0.3) |
| **Complex** | 52.7% (-0.3) | **97.8%** (+52.9) ✅ | 37.1% (-5.2) | 40.0% (+1.9) |
| **Noisy** | 48.5% (+2.9) | **91.7%** (+23.8) ✅ | 40.0% (-1.3) | 39.1% (-5.1) |

**Insight**: Faithfulness improved across ALL categories, especially complex queries (+53pp!)

### Changes Made

**Prompt Optimization** (Phase 5 Quick Test Results):

| Variant | Faithfulness | Notes |
|---------|--------------|-------|
| Phase 4 Baseline | 60.0% | Remove inline citations, add personality |
| **Phase 5 Final** | **93.3%** | Mandatory source usage, numbered citations ✅ |
| 5A | 80.0% | Source grounding only |
| 5B | 90.0% | + Numbered citations |
| 5C | **93.3%** | + Conflict resolution ✅ (selected) |

**Final Prompt** (`SYSTEM_PROMPT_TEMPLATE` in `chat.py`):
1. **Mandatory source usage**: "ONLY use information from provided CONTEXT"
2. **Numbered citations**: [1], [2], [3] after each statement
3. **Conflict resolution**: "If sources conflict, present both perspectives"
4. **Completeness**: "If sources partially answer, provide what you can"
5. **Synthesis**: Weave facts into flowing paragraphs, not bullet lists

### Key Findings

1. **Faithfulness is critical** — Jumped from 59% → 96% by forcing source grounding
2. **Quick-test methodology works** — Tested 3 prompt variants in 5 minutes vs 2 hours for full eval
3. **Numbered citations help LLM** — Clearer than inline [Source: X] format
4. **Conflicts are rare but handled** — Explicit conflict resolution instructions

### Reproducibility Note

Phase 5 evaluation was run once (2026-02-08). A reproducibility study (Phase 7) later found RAGAS has ±16-28% variance. However, the +37pp faithfulness gain is far beyond noise threshold, indicating real improvement.

---

## Phase 7 Results (2026-02-09)

Disabled broken metadata filtering from Phase 6 and implemented **NBA-specific query expansion** to improve keyword matching. Conducted **reproducibility study** to distinguish real improvements from RAGAS evaluation variance.

### Metrics (75 test cases)

| Metric | Phase 5 (Baseline) | Phase 7 (Query Expansion) | Change |
|--------|-------------------|---------------------------|--------|
| **Answer Relevancy** | 51.88% | **77.73%** | **+25.85%** 🎯 |
| **Faithfulness** | 96.03% | 68.80% | **-27.23%** ❌ |
| **Context Precision** | 41.92% | **59.84%** | **+17.92%** ✅ |
| **Context Recall** | 42.14% | **65.12%** | **+22.98%** ✅ |

**Wins**: Answer Relevancy (+26%), Precision (+18%), Recall (+23%)
**Loss**: Faithfulness dropped 27pp (96% → 69%)

### By Category

| Category | Relevancy | Faithfulness | Precision | Recall |
|----------|-----------|-------------|-----------|--------|
| **Simple** | **85.3%** (+30.7) ✅ | 72.6% (-26.0) ❌ | **66.1%** (+17.6) ✅ | **71.6%** (+24.4) ✅ |
| **Complex** | **76.4%** (+23.7) ✅ | 70.2% (-27.6) ❌ | **57.1%** (+20.0) ✅ | **64.8%** (+24.8) ✅ |
| **Noisy** | **71.6%** (+23.1) ✅ | 63.6% (-28.1) ❌ | **56.4%** (+16.4) ✅ | **58.9%** (+19.8) ✅ |

**Insight**: Query expansion improved retrieval (precision/recall) but LLM struggled with faithfulness

### Changes Made

**1. Disabled Phase 6 Metadata Filtering**
- Phase 6 tagged only 3 chunks as `player_stats` (all headers, no actual data)
- Metadata filtering caused false negatives (missed relevant chunks)
- Disabled: `metadata_filters=None` in `vector_store.search()`

**2. NBA-Specific Query Expansion** (`query_expansion.py`)
- Player name expansion: "LeBron" → "LeBron James | King James | Lakers #23"
- Team expansion: "Warriors" → "Golden State Warriors | GSW | Dubs"
- Smart expansion based on query length:
  - Short (≤5 words): Aggressive expansion (max 4 expansions)
  - Medium (6-10 words): Moderate (max 2)
  - Long (>10 words): Minimal (max 1)
- Fallback: Keep original query if no patterns match

**3. Integration with Search Pipeline**
- `chat.py`: Calls `query_expander.expand_smart(query)` before embedding
- `vector_store.search()`: Uses expanded query for better keyword matching

### Reproducibility Study

**Question**: How much of Phase 7's +26% Answer Relevancy is real vs RAGAS variance?

**Method**: Re-ran Phase 5 evaluation (identical config, same test cases)

| Run | Answer Relevancy | Faithfulness | Precision | Recall |
|-----|------------------|--------------|-----------|--------|
| **Phase 5 Original** | 51.88% | 96.03% | 41.92% | 42.14% |
| **Phase 5 Re-run** | **78.05%** | 80.16% | **59.19%** | **65.50%** |
| **Phase 7** | 77.73% | 68.80% | 59.84% | 65.12% |

**Real Change** = Phase 5 Re-run → Phase 7 (controls for evaluation variance)

| Metric | Phase 5 Re-run | Phase 7 | Real Change |
|--------|---------------|---------|-------------|
| **Answer Relevancy** | 78.05% | 77.73% | **-0.32%** (no change) |
| **Faithfulness** | 80.16% | 68.80% | **-11.36%** ❌ |
| **Context Precision** | 59.19% | 59.84% | **+0.65%** (no change) |
| **Context Recall** | 65.50% | 65.12% | **-0.38%** (no change) |

### Key Findings: RAGAS Evaluation Variance

**Reproducibility Study**: Re-ran Phase 5 evaluation with identical configuration to measure variance

| Metric | Phase 5 Original | Phase 5 Re-run | Variance |
|--------|------------------|---------------|----------|
| **Answer Relevancy** | 51.88% | **78.05%** | **±26.17%** ❌ |
| **Faithfulness** | 96.03% | 80.16% | **±15.87%** ❌ |
| **Context Precision** | 41.92% | 59.19% | **±17.27%** ❌ |
| **Context Recall** | 42.14% | 65.50% | **±23.36%** ❌ |

**Insight**: RAGAS metrics have **high variance** (±16-28%) even with identical configuration!

**Possible Causes**:
1. Gemini 2.0 Flash Lite non-determinism (even with temperature=0)
2. RAGAS evaluation prompts have randomness
3. Small sample size (75 test cases)

**Implications**:
1. RAGAS evaluation variance (±16-28% across categories)
2. **Faithfulness drop** (-11.36%) is concerning but **partially due to variance**
3. **No real relevancy gain** (+26% was mostly evaluation variance)
4. **Precision/Recall stable** (±0.65%, within noise threshold)

**Action Items**:
1. ✅ Query expansion works (keeps precision/recall stable)
2. ❌ Faithfulness regression needs investigation (Phase 18 fix)
3. ⚠️ Use multiple evaluation runs to account for variance
4. 📊 Track trends over time, not single-run comparisons

### Visualizations

Generated in `evaluation_results/visualizations/`:
- `overall_metrics_comparison.png`: Bar chart of 4 metrics across 3 evaluations
- `category_metrics_comparison.png`: Grouped bar chart by category
- `evaluation_variance.png`: Variance magnitude by metric
- `real_vs_apparent_change.png`: Phase 5 → Phase 7 change with variance overlay

---

## Phase 12 Results (2026-02-11)

**Goal**: Fix 13/75 test case failures by using **query-type-specific prompts** (SQL_ONLY, CONTEXTUAL, HYBRID).

### Failures Root Cause Analysis

**Before Phase 12**:
- 62/75 passing (82.7%)
- 13/75 failing (17.3%)

**Failure Patterns**:
1. **SQL-only queries** (5 failures): LLM ignored SQL results, used general knowledge
2. **Contextual queries** (4 failures): LLM missed key facts in retrieved documents
3. **Hybrid queries** (4 failures): LLM didn't synthesize SQL + vector contexts

**Root Cause**: Single generic prompt (`SYSTEM_PROMPT_TEMPLATE`) wasn't optimized for different query types.

### Solution: Query-Type-Specific Prompts

**1. SQL_ONLY_PROMPT** (for STATISTICAL queries)
- "**ANSWER THE QUESTION USING THE STATISTICAL DATA ABOVE**"
- Forces LLM to extract from SQL results, not general knowledge
- Clear formatting: "Tell the story with data", not just list numbers
- Citation: "Sources: Database Name, ..."

**2. CONTEXTUAL_PROMPT** (for CONTEXTUAL queries)
- "**ONLY use information from the CONTEXTUAL KNOWLEDGE above**"
- Biographical queries: "Include both narrative AND statistics if available"
- Numbered citations: [1], [2], [3] for each statement

**3. HYBRID_PROMPT** (for HYBRID queries)
- Separate sections: "STATISTICAL DATA" + "CONTEXTUAL KNOWLEDGE"
- "**YOU MUST USE BOTH DATA SOURCES - WEAVE THEM TOGETHER**"
- Example: "Player X averaged 28.5 PPG[1], showcasing efficiency praised by fans[2]."

### Evaluation Methodology

**LLM**: Gemini 2.0 Flash Lite (consistent with Phase 5/7 evaluations)
**Test Suite**: 75 vector test cases (simple/complex/noisy)
**Note**: SQL hybrid search NOT tested (evaluation uses search() not chat() method)

### Results

**Before Phase 12**:
- 62/75 passing (82.7%)
- 13/75 failing (17.3%)

**After Phase 12**:
- **71/75 passing (94.7%)** ✅
- 4/75 failing (5.3%)

**Improvement**: +12pp pass rate (+9 test cases fixed)

### Remaining Failures (4/75)

1. **"What is a triple-double?"** (CONTEXTUAL)
   - Issue: Retrieved Reddit comments don't explicitly define "triple-double"
   - Fix needed: Add NBA glossary to vector store

2. **"Compare LeBron and Jordan"** (CONTEXTUAL)
   - Issue: LLM says "sources don't provide comparison" (but they do!)
   - Fix needed: Prompt enhancement for comparison synthesis

3. **"Top 5 scorers and why effective"** (HYBRID)
   - Issue: SQL provides top 5, but vector context missing "why effective"
   - Fix needed: Better vector retrieval for qualitative analysis

4. **"Who has the most assists and how do they create plays?"** (HYBRID)
   - Issue: SQL provides assists leader, but vector context missing "how create plays"
   - Fix needed: Hybrid query expansion to retrieve both stats + strategy docs

### Key Learnings

1. **Query-specific prompts matter** — 12pp improvement by tailoring prompts to data source type
2. **Mandatory synthesis is critical** — HYBRID_PROMPT "YOU MUST USE BOTH" forces LLM to combine sources
3. **Numbered citations help** — [1], [2], [3] clearer than inline [Source: X]
4. **Biographical queries need special handling** — "Include both narrative AND statistics" in prompt

---

## Phase 18 Results (2026-02-13) — Hybrid Evaluation

**Goal**: Measure hybrid query performance and faithfulness with numbered citations.

### Test Results (50 hybrid test cases)

**Execution**:
- 50/50 successful (100% execution)
- 0 failures, 0 errors
- Average processing time: 8.2s per query

**Classification**:
- 48/50 correctly routed to HYBRID (96.0%)
- 2/50 misclassified (4.0%)
  - "Who is LeBron?" → CONTEXTUAL (should be HYBRID biographical)
  - "Most improved team" → CONTEXTUAL (should be HYBRID)

**Response Quality**:
- 45/50 passed ground truth validation (90.0%)
- 5/50 partial matches (10.0%)
  - LLM synthesized SQL + vector but missed some details

### Report Structure

**11 Sections** (matching SQL and Vector reports):
1. Executive Summary (routing breakdown)
2. Failure Analysis (error taxonomy)
3. Routing Analysis (SQL vs Vector vs Both, fallback patterns)
4. SQL Component Analysis (query structure, complexity, column selection)
5. Vector Component Analysis (source quality, retrieval performance, K-value)
6. Response Quality (length, completeness, confidence, citations)
7. Hybrid Combination Quality (true hybrid query analysis)
8. Performance by Category (category breakdown with routing types)
9. Key Findings (actionable insights)
10. Detailed Test Results (per-query with SQL, response, sources)
11. Report Sections (footer with navigation)

### Numbered Citations Impact

**Before Phase 18** (inline citations):
- "Player X scored 30 points (Source: NBA Database). Fans praised him (Source: Reddit)."
- Faithfulness: 68.80% (Phase 7)

**After Phase 18** (numbered citations):
- "Player X scored 30 points[1]. Fans praised him[2]."
- Faithfulness: **Pending full evaluation** (expected ~80% based on Phase 5)

**Benefits**:
1. **Cleaner text** — No inline "(Source: X)" interrupts flow
2. **Better attribution** — [1], [2], [3] clearer than repetitive inline citations
3. **LLM comprehension** — Numbered format easier for LLM to track sources

### Key Learnings

1. **Hybrid queries are complex** — 8.2s average latency (SQL + Vector + LLM synthesis)
2. **Classification is hard** — 4% misclassification rate (biographical queries tricky)
3. **Synthesis is working** — 90% pass rate shows LLM can blend SQL + vector well
4. **Report depth matters** — 11-section format provides actionable insights

---

## Repository Reorganization (2026-02-11)

**Objective**: Achieve 100% compliance with GLOBAL_POLICY.md v1.17

**Changes**:
1. Archived 10 root-level documentation files to `_archived/2026-02/root_docs/`
2. Updated README.md to 500 lines (comprehensive overview)
3. Added 5-field headers to all Python files
4. Reorganized test structure (core/services/integration/e2e/ui)
5. Moved scripts to `scripts/` directory
6. Consolidated documentation in `docs/`

**Before Cleanup**:
```
Sports_See/
├── README.md (140 lines, basic)
├── PROJECT_MEMORY.md
├── CHANGELOG.md
├── 10 root-level .md files (scattered docs)
├── src/ (headers partially missing)
├── tests/ (flat structure, 150+ files)
├── scripts/ (mixed with notebooks)
└── test_results.txt
```

**After Cleanup**:
```
Sports_See/
├── README.md (500 lines, comprehensive)
├── PROJECT_MEMORY.md
├── CHANGELOG.md
├── src/ (all files with headers)
├── tests/ (reorganized: core/services/integration/e2e/ui/)
├── scripts/ (streamlit_viz_example.py moved here)
├── docs/ (all documentation here)
└── _archived/2026-02/
    ├── README.md (archive documentation)
    └── root_docs/ (10 archived documentation files)
```

### Results

**Compliance**: ✅ **100% compliant with GLOBAL_POLICY.md v1.17**

**Improvements**:
- Cleaner repository structure
- Single source of truth for documentation
- All files properly organized
- No orphaned or misplaced files
- Complete file headers
- Updated CHANGELOG

**Impact**:
- Easier navigation for contributors
- Reduced cognitive load
- Better maintainability
- Clearer project structure
- Professional production-ready organization

**Maintainer:** Shahu | **Date:** 2026-02-11

---

## Entry: Unified Ground Truth Verification Script (2026-02-13)

**Change**: Merged two separate verification scripts into one unified `src/evaluation/validator.py`.

**Before**:
- `src/evaluation/verification/verify_all_sql_ground_truth.py` — SQL-only verification
- `src/evaluation/verification/verify_all_hybrid_ground_truth.py` — Hybrid-only verification

**After**:
- `src/evaluation/validator.py` — Unified verification with CLI args: `all` (default), `sql`, `hybrid`

**Deleted**:
- `src/evaluation/verification/` folder (including `__init__.py`, both old scripts, `__pycache__`)
- `tests/evaluation/verification/` folder (including old test files)

**Updated References**: README.md (4 sections), CHANGELOG.md (1 reference)

**Maintainer:** Shahu | **Date:** 2026-02-13

---

## Entry: SQL Test Case Remediations (2026-02-13)

**Objective**: Address 10 SQL test case performance issues identified in `SQL_PERFORMANCE_ISSUES_AND_REMEDIATION.md`

**User Decisions**:
- Issue #1 (Conversational Context): Already handled (ConversationService exists)
- Issue #2 (Progressive Filtering): Covered by #1 implementation
- Issue #3 (Missing JOINs): Accept remediation with script
- Issue #4 (Incomplete Top-N): Prefer Option 1 (format constraint)
- Issue #5 (LLM Declined): Prefer Option 3 (constrain LLM behavior)
- Issue #6 (Excessive Hedging): Accept remediation
- **Issue #7 (Ambiguous MVP Queries): CORRECT BEHAVIOR - Move to vectors only**
- Issue #8 (Team Roster): Already covered (empty result messaging)
- Issue #9 (Team Aggregation): CRITICAL - Verified 30 teams exist, all working
- Issue #10 (Special Characters): Prefer Option 2 (fuzzy matching)

### Changes Made

**1. SQL Tool Enhancements** (`src/tools/sql_tool.py`)

**Issue #3: Missing JOINs**
- Added `_validate_sql_structure()` method
- Auto-corrects missing JOINs when query mentions "players" but only touches `player_stats`
- Pattern: If "player" in question and "player_stats" in SQL but no JOIN → add `INNER JOIN players`
- Example fix:
  ```sql
  -- Before (missing JOIN):
  SELECT name, pts FROM player_stats WHERE ...

  -- After (auto-corrected):
  SELECT p.name, ps.pts FROM players p
  INNER JOIN player_stats ps ON p.id = ps.player_id WHERE ...
  ```

**Issue #10: Special Character Handling**
- Added `normalize_player_name()` static method
- Unicode NFD normalization removes accents/diacritics for fuzzy matching
- Example: `normalize_player_name("Jokić")` → `"Jokic"`
- Enables matching "Nikola Jokic" when user types "Nikola Jokić" or "Jokic"

**2. Prompt Enhancements** (`src/services/chat.py`)

**Issue #4: Incomplete Top-N Responses**
- Updated `SQL_ONLY_PROMPT` with top-N format constraint:
  ```
  **Top-N Queries** (Issue #4 Fix):
  - FIRST: Present the COMPLETE list of ALL N items with their stats
  - THEN: Add analysis/context AFTER the complete list
  - CRITICAL: Complete the full list BEFORE adding commentary
  ```
- Forces LLM to present full list before analysis (prevents premature cutoff)

**Issue #5: LLM Declined Responses**
- Updated `SQL_ONLY_PROMPT` with decline prevention:
  ```
  **NEVER DECLINE TO ANSWER** (Issue #5 Fix):
  - If SQL results are EMPTY: State clearly what's missing, suggest alternatives
  - If you HAVE the data: Present it directly and confidently
  - Do NOT say "I can't provide..." when STATISTICAL DATA contains information
  - Be helpful, not apologetic
  ```
- Prevents LLM from declining when SQL data is available

**Issue #6: Excessive Hedging Language**
- Updated `SQL_ONLY_PROMPT` with tone guidelines:
  ```
  **Tone for EXACT statistics** (Issue #6 Fix):
  - Use DEFINITIVE language ("Player X scored 30 points")
  - NOT "appears to have scored around 30 points"
  - Reserve hedging ONLY for comparisons, projections, interpretations
  ```
- Added `_remove_excessive_hedging()` static method:
  - Removes weak qualifiers: "appears to have scored" → "scored"
  - Cleans approximations: "approximately 30 points" → "30 points"
  - Removes unnecessary qualifiers: "possibly", "probably", "likely"
  - Applied only to STATISTICAL and HYBRID queries (not CONTEXTUAL)

**3. Documentation** (Issue #7)

**Ambiguous Query Behavior is CORRECT**:
- Queries like "Who was the MVP?" or "Tell me about the best player" are intentionally routed to **CONTEXTUAL (vector search)**, NOT SQL
- Rationale:
  - "MVP" is ambiguous (regular season MVP? Finals MVP? historical?)
  - "Best player" is subjective (best in what category? scoring? defense? leadership?)
  - Vector search handles ambiguous/qualitative queries better than SQL
  - SQL is reserved for precise, measurable statistical queries
- **No code change needed** — Current routing behavior is correct and expected
- User decision: "Move this query to vectors only because the result is expected and this is not a problem"

### Verification Status

✅ **Issue #1**: ConversationService exists (verified in `src/services/conversation.py`)
✅ **Issue #2**: Progressive filtering covered by conversation history (user confirmed)
✅ **Issue #3**: JOIN validation implemented and tested
✅ **Issue #4**: Top-N format constraint added to SQL_ONLY_PROMPT
✅ **Issue #5**: LLM decline prevention added to SQL_ONLY_PROMPT
✅ **Issue #6**: Hedging removal implemented (prompt + post-processing)
✅ **Issue #7**: Documented as correct behavior (ambiguous queries → vectors)
✅ **Issue #8**: Empty result messaging already covered (user confirmed)
✅ **Issue #9**: VERIFIED - 30 teams exist in database, all queries working (8/8 tests passing)
✅ **Issue #10**: Name normalization implemented for special characters

### Expected Impact

**SQL Test Case Performance** (baseline: 83.75% accuracy, 15% fallback rate):
- **Missing JOINs**: 7.6% → 0% (auto-correction)
- **Incomplete Top-N**: 8.75% → 0% (format constraint)
- **LLM Declined**: 2.5% → 0% (decline prevention)
- **Excessive Hedging**: 50% → <10% (tone guidelines + regex)
- **Special Char Matching**: 50% → 100% (normalization)
- **Overall Accuracy**: 83.75% → **~95%** (estimated)

**Next Steps**:
1. Run full SQL evaluation suite to measure actual improvements
2. Test conversational queries with pronouns
3. Verify team queries still work (100% retention expected)

**Maintainer:** Shahu | **Date:** 2026-02-13
