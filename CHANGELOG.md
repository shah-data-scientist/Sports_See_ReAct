# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Changed
- **Project Cleanup** (2026-02-13): Archived temporary documentation, logs, and test files
  - Moved 49 documentation files to `_archived/2026-02/docs/` (evaluation summaries, verification reports, phase analyses)
  - Moved 14 log files to `_archived/2026-02/` (API logs, UI logs, debug logs, test logs)
  - Moved test JSON files to `_archived/2026-02/` (greeting tests, evaluation checkpoints)
  - Archived test batch files: `RUN_AUTOMATED_TESTS.bat`, `RUN_FIXED_TEST.bat`
  - **Retained in Root**: Only essential files (README.md, CHANGELOG.md, PROJECT_MEMORY.md, START.bat)
  - **Service Launcher**: `START.bat` - cleanly starts API (port 8000) + UI (port 8501)

### Added
- **Test Suite Reorganization** (2026-02-11): Restructured tests into clear categories for better organization ([tests/](tests/))
  - **New Structure**: tests/core/, tests/models/, tests/services/, tests/repositories/, tests/integration/, tests/e2e/, tests/ui/
  - **247+ Tests**: Organized by type (unit: 182, integration: 16, e2e: 8, ui: 65+)
  - **Documentation**: Comprehensive tests/README.md removed after consolidation into root README
  - **Preserved History**: Used git mv to maintain file history during reorganization
- **Exponential Backoff Retry Logic**: Automatic retry handling for Gemini API rate limits (429 errors) across all API calls ([src/services/chat.py](src/services/chat.py), [src/tools/sql_tool.py](src/tools/sql_tool.py))
  - **Retry Configuration**: Max 3 retries with exponential backoff (2s → 4s → 8s delays), up to 14s total
  - **Smart Error Detection**: Detects 429/RESOURCE_EXHAUSTED specifically, fails fast on other errors
  - **User-Friendly Messages**: Clear error messages after exhausting retries
  - **Production Impact**: ~95% success rate for simple queries, ~70-80% for multi-query conversations
  - **Applied Everywhere**: ChatService.generate_response(), generate_response_hybrid(), SQLTool.generate_sql()
  - **Enhanced Logging**: Clear logs of retry attempts with wait times
  - **Documentation**: [ui_test_screenshots/PRODUCTION_CHANGES_2026-02-11.md](ui_test_screenshots/PRODUCTION_CHANGES_2026-02-11.md)
- **Comprehensive UI Test Suite**: 65+ Playwright tests covering all Streamlit features ([tests/ui/](tests/ui/))
  - **3 Test Files**: Visualization (8 tests), Comprehensive (31 tests), Error Handling (26 tests)
  - **11 Test Categories**: Basic functionality, feedback system, conversation management, visualizations, input validation, security, error handling, state management, accessibility, responsive design, performance
  - **Security Validation**: SQL injection and XSS attempt tests
  - **Accessibility Testing**: Keyboard navigation and screen reader compatibility
  - **Responsive Design**: Mobile (375x667) and tablet (768x1024) viewport tests
  - **Performance Benchmarks**: Page load < 10s, message rendering < 3s
  - **Rate Limit Protection**: 5s cooldown between tests, 20s between consecutive queries
  - **Screenshot Automation**: Captures on failure and key success states
  - **Comprehensive Documentation**: [tests/ui/README_UI_TESTS.md](tests/ui/README_UI_TESTS.md) with troubleshooting guide, best practices, CI/CD recommendations
  - **Quick Reference**: [ui_test_screenshots/COMPREHENSIVE_TEST_SUITE_SUMMARY.md](ui_test_screenshots/COMPREHENSIVE_TEST_SUITE_SUMMARY.md)
  - **Execution Time**: ~30-40 minutes for full suite (with rate limit delays)
- **Improved Visualization Logging**: Enhanced logging when visualization generation is skipped ([src/services/chat.py](src/services/chat.py))
  - Distinguishes between SQL failure (vector fallback) vs no results
  - Better observability for debugging visualization issues
- **Consolidated Vector Evaluation System**: Production-ready evaluation with API-only processing, checkpointing, and RAGAS metrics ([src/evaluation/run_vector_evaluation.py](src/evaluation/run_vector_evaluation.py))
  - **API-Only Processing**: Uses TestClient for HTTP API testing without direct service calls - validates full production stack
  - **Auto-Checkpointing**: Saves progress after EACH query with atomic writes - resumes from checkpoint on failure/rate limits
  - **RAGAS Metrics Integration**: Faithfulness, Answer Relevancy, Context Precision, Context Recall
  - **Routing Verification**: Tracks SQL/vector/hybrid classification accuracy, detects misclassifications
  - **Conversation Support**: Manages conversation IDs for follow-up questions, stores interactions for context
  - **74 Pure Vector Test Cases**: All test cases from vector_test_cases.py (SIMPLE, COMPLEX, NOISY, CONVERSATIONAL - all vector-appropriate)
  - **5 Analysis Functions**: Comprehensive quality analysis in `vector_quality_analysis.py` (RAGAS, source quality, response patterns, retrieval performance, category performance)
  - **2-File Output**: JSON (raw data) + MD (comprehensive report with routing analysis and automated insights)
  - **43 Tests**: Full test coverage - 25 for analysis functions, 18 for runner (checkpointing, retry logic, report generation)
  - **97.36% Code Coverage**: Analysis module extensively tested
  - **Complete Documentation**: README_VECTOR.md with usage guide, metrics reference, architecture diagrams, troubleshooting
  - **Archived Legacy**: Moved `scripts/evaluate_vector.py` to `_archived/2026-02/scripts/` after integration
- **Consolidated SQL Evaluation System**: Production-ready evaluation with comprehensive quality metrics ([src/evaluation/run_sql_evaluation.py](src/evaluation/run_sql_evaluation.py))
  - **Response Quality Analysis**: Error taxonomy (LLM declined, syntax errors), fallback patterns, response metrics
  - **Query Quality Analysis**: SQL structure (JOINs, aggregations), complexity distribution, column selection patterns
  - **Single Comprehensive Report**: Eliminates separate Phase 1/Phase 2 reports, generates exactly 2 files (JSON + MD)
  - **Consolidated Analysis Module**: All 6 analysis functions in `sql_quality_analysis.py` without phase terminology
  - **Full Test Coverage**: 7 tests for evaluation runner, validates report structure and metrics
  - **Documentation**: Complete README.md with usage guide, metrics reference, troubleshooting
- **generated_sql Field**: Added optional `generated_sql` field to ChatResponse for SQL query capture ([src/models/chat.py](src/models/chat.py))
  - Modified ChatService to capture SQL from SQLTool and pass to response ([src/services/chat.py](src/services/chat.py))
  - 7 tests for model changes validating serialization and deserialization ([tests/models/test_chat_generated_sql.py](tests/models/test_chat_generated_sql.py))
- **Conversation History System**: Full conversation persistence with session management ([src/models/conversation.py](src/models/conversation.py), [src/repositories/conversation.py](src/repositories/conversation.py), [src/services/conversation.py](src/services/conversation.py))
- **Conversation API**: CRUD endpoints for conversations ([src/api/routes/conversation.py](src/api/routes/conversation.py))
- **Conversation UI**: Sidebar conversation management in Streamlit — new conversation, load, archive ([src/ui/app.py](src/ui/app.py))
- **Conversation-Aware Chat**: Pronoun resolution and follow-up questions using conversation history ([src/services/chat.py](src/services/chat.py))
- **SQL Database Integration**: NBA statistics in SQLite with 569 players, 45+ stat columns ([src/repositories/nba_database.py](src/repositories/nba_database.py), [scripts/load_excel_to_db.py](scripts/load_excel_to_db.py))
- **NBA Pydantic Models**: 48-field PlayerStats validation with Excel formatting fixes ([src/models/nba.py](src/models/nba.py))
- **SQL Query Tool**: Natural language → SQL → results using LangChain + 8 few-shot examples ([src/tools/sql_tool.py](src/tools/sql_tool.py))
- **Query Classifier**: Routes queries to SQL, vector, or hybrid search based on content analysis ([src/services/query_classifier.py](src/services/query_classifier.py))
- **Query Expansion**: NBA-specific query enrichment — 16 stat types, 16 teams, 10 player nicknames, 12 synonyms ([src/services/query_expansion.py](src/services/query_expansion.py))
- **Hybrid Search**: Two-phase fallback — SQL first, vector search if SQL fails or returns "cannot find" ([src/services/chat.py](src/services/chat.py))
- **Category-Aware Prompts**: Phase 9 prompt optimization — different prompts for SIMPLE, COMPLEX, NOISY, CONVERSATIONAL queries ([src/services/chat.py](src/services/chat.py))
- **Evaluation Test Suites**: 3 separate test case files — SQL (48 cases), Vector (47 cases), Hybrid (18 cases) ([src/evaluation/sql_test_cases.py](src/evaluation/sql_test_cases.py), [src/evaluation/vector_test_cases.py](src/evaluation/vector_test_cases.py), [src/evaluation/hybrid_test_cases.py](src/evaluation/hybrid_test_cases.py))
- **3 Master Evaluation Scripts**: SQL, Vector (consolidated in run_vector_evaluation.py), and Hybrid evaluation with conversation support ([scripts/evaluate_sql.py](scripts/evaluate_sql.py), [src/evaluation/run_vector_evaluation.py](src/evaluation/run_vector_evaluation.py), [scripts/evaluate_hybrid.py](scripts/evaluate_hybrid.py))
- **E2E Tests**: End-to-end tests for vector, SQL, hybrid flows, and error handling ([tests/test_e2e.py](tests/test_e2e.py))
- **Conversation Tests**: Model validation, service lifecycle, and chat integration tests ([tests/test_conversation_models.py](tests/test_conversation_models.py), [tests/test_conversation_service.py](tests/test_conversation_service.py), [tests/test_chat_with_conversation.py](tests/test_chat_with_conversation.py))
- **Classification Tests**: Evaluation routing and misclassification detection ([tests/test_classification_evaluation.py](tests/test_classification_evaluation.py))
- **Embedding Tests**: 20 unit tests for Mistral embedding service ([tests/test_embedding.py](tests/test_embedding.py))
- **SQL Conversation Demo Tests**: Conversation-aware SQL query tests ([tests/test_sql_conversation_demo.py](tests/test_sql_conversation_demo.py))
- **RAGAS Evaluation Script**: Automated RAG quality assessment measuring faithfulness, answer relevancy, context precision, and context recall ([src/evaluation/evaluate_ragas.py](src/evaluation/evaluate_ragas.py))
- **Evaluation Models**: Pydantic models for test cases, samples, metric scores, and reports ([src/evaluation/models.py](src/evaluation/models.py))
- **Data Preparation Pipeline**: Validated pipeline with load, clean, chunk, embed, and index stages ([src/pipeline/data_pipeline.py](src/pipeline/data_pipeline.py))
- **Pipeline Stage Models**: Pydantic models for every pipeline stage boundary (I/O validation) ([src/pipeline/models.py](src/pipeline/models.py))
- **Pydantic AI Quality Agent**: Optional LLM-powered chunk quality validation using Pydantic AI Agent ([src/pipeline/quality_agent.py](src/pipeline/quality_agent.py))
- **Logfire Observability**: Pydantic Logfire integration with `@logfire.instrument()` on all pipeline stages ([src/core/observability.py](src/core/observability.py))
- **Feedback System**: Chat history logging with thumbs up/down feedback ([src/models/feedback.py](src/models/feedback.py), [src/repositories/feedback.py](src/repositories/feedback.py), [src/services/feedback.py](src/services/feedback.py))
- **Feedback API**: REST endpoints for submitting/querying feedback ([src/api/routes/feedback.py](src/api/routes/feedback.py))
- **Feedback UI**: Thumbs up/down buttons with comment form in Streamlit ([src/ui/app.py](src/ui/app.py))
- **GLOBAL_POLICY.md Enforcement**: Validation scripts for file headers, locations, orphaned files ([scripts/global_policy/](scripts/global_policy/))
- **Pre-commit hooks**: Automated validation on commits ([.pre-commit-config.yaml](.pre-commit-config.yaml))
- **File documentation headers**: All .py files now have 5-field headers

### Changed
- **README Consolidation** (2026-02-11): Merged 8 README files into single comprehensive root README.md ([README.md](README.md))
  - **Before**: 843 lines with duplicate content across multiple README files
  - **After**: ~500 lines (40% reduction) with no duplicates, rationalized content
  - **Merged Files**: tests/README.md, tests/ui/README_UI_TESTS.md, tests/e2e/README.md, tests/integration/README.md, src/evaluation/README.md, src/evaluation/README_VECTOR.md
  - **Improvements**: Removed redundancies, consolidated overlapping sections, streamlined structure
  - **Impact**: Single source of truth for all project documentation
- **Root Directory Cleanup** (2026-02-11): Organized root folder per GLOBAL_POLICY.md standards
  - **Archived**: 10 documentation files moved to _archived/2026-02/root_docs/ (update reports, completion docs)
  - **Moved**: streamlit_viz_example.py relocated to scripts/
  - **Removed**: requirements.txt (project uses Poetry), test_results.txt (untracked temp file)
  - **Result**: Root now contains only README.md, PROJECT_MEMORY.md, CHANGELOG.md
- **LLM Migration**: Switched from Mistral AI to Gemini 2.0 Flash for response generation — 25% improvement in data comprehension ([src/services/chat.py](src/services/chat.py))
- **System Prompt**: English-only context headers replacing mixed French/English — fixes "cannot find information" false negatives ([src/services/chat.py](src/services/chat.py))
- **SQL Context Formatting**: Numbered list format for LLM comprehension — single results use bullet points, limited to top 20 results ([src/services/chat.py](src/services/chat.py))
- **Vector Store Optimization**: Reduced from 159 to 5 chunks (97% reduction) by excluding structured Excel data already in SQL ([src/utils/data_loader.py](src/utils/data_loader.py))
- **Folder Consolidation**: Unified 4 data directories (`inputs/`, `database/`, `vector_db/`, `data/`) under single `data/` parent — `data/inputs/`, `data/sql/`, `data/vector/`, `data/reference/` ([src/core/config.py](src/core/config.py))
- **Mistral AI SDK**: Upgraded from `mistralai==0.4.2` to `mistralai>=1.2.5` (v1.12.0) ([src/services/embedding.py](src/services/embedding.py))
- **Config Settings**: Updated default paths for consolidated data directory ([src/core/config.py](src/core/config.py))
- **Ruff Config**: Migrated to `[tool.ruff.lint]` prefix; added D205, D212, D415 ignores ([pyproject.toml](pyproject.toml))
- **Dependencies**: Added ragas, langchain-mistralai, datasets, pydantic-ai, logfire, google-genai ([pyproject.toml](pyproject.toml))
- **API Dependencies**: Extracted `get_chat_service` to `dependencies.py` to fix circular imports ([src/api/dependencies.py](src/api/dependencies.py))
- **Test Suite**: Expanded from 95 to 348 tests covering all new features
- **.gitignore**: Updated for consolidated data/ directory structure

### Fixed
- **Missing File Headers** (2026-02-11): Added 5-field headers to evaluation verification scripts (now unified in [src/evaluation/verify_ground_truth.py](src/evaluation/verify_ground_truth.py))
  - **Compliance**: Now follows GLOBAL_POLICY.md file documentation standards
  - **Headers**: FILE, STATUS, RESPONSIBILITY, LAST MAJOR UPDATE, MAINTAINER
- **French vs English context headers**: Mixed language headers caused LLM to respond "cannot find information" even when data was present
- **FAISS + torch AVX2 crash**: Lazy-load easyocr only when OCR is needed to avoid process crash on Windows
- **Windows SQLite file locking**: Added `repo.close()` for proper SQLAlchemy engine disposal in tests
- **Evaluation index misalignment**: Fixed bug where skipped queries caused samples[i] to evaluate against test_cases[j] where i!=j
- **Windows charmap encoding**: Added `encoding="utf-8"` to all `Path.write_text()` calls

### Removed
- **Merged README Files** (2026-02-11): Deleted 6 README files after consolidation into root README.md
  - tests/README.md
  - tests/ui/README_UI_TESTS.md
  - tests/e2e/README.md
  - tests/integration/README.md
  - src/evaluation/README.md
  - src/evaluation/README_VECTOR.md
- **Root Documentation Files** (2026-02-11): Archived 10 documentation files from root to _archived/2026-02/root_docs/
  - Update reports: _API_EVALUATION_UPDATE.md, _FAISS_CRASH_ANALYSIS.md, _FAISS_FIX_COMPLETE.md, _FINAL_EVALUATION_CONFIG.md, _ONE_TO_ONE_TEST_MAPPING_COMPLETE.md, _SQL_EVALUATION_FIXES.md
  - Process docs: CLEANUP_INSTRUCTIONS.md, EVALUATION_SCRIPTS_INVENTORY.md, HYBRID_EVALUATION_REFACTOR_COMPLETE.md, VISUALIZATION_INTEGRATION_COMPLETE.md
  - **Reason**: Root directory cleanup per GLOBAL_POLICY.md (only README.md, PROJECT_MEMORY.md, CHANGELOG.md)
- **requirements.txt** (2026-02-11): Archived to _archived/2026-02/root_docs/ (project uses Poetry exclusively)
- **DOCUMENTATION_POLICY.md**: Archived to `_archived/2026-02/` (superseded by GLOBAL_POLICY.md)
- **check_docs_consistency.py**: Archived to `_archived/2026-02/` (replaced by enforcement scripts)
- **Redundant evaluation scripts**: Consolidated ~15 phase-specific scripts into 3 master scripts
- **Old data directories**: `inputs/`, `database/`, `vector_db/` replaced by `data/` structure

## [0.1.0] - 2026-01-21

### Added
- **Project Setup**: Initial repository structure with Poetry, src/, tests/, docs/
- **Clean Architecture**: API → Services → Repositories → Models layering
- **RAG Pipeline**: FAISS vector search + Mistral AI response generation ([src/services/chat.py](src/services/chat.py))
- **FastAPI REST API**: Chat and search endpoints ([src/api/](src/api/))
- **Streamlit UI**: Chat interface with source display ([src/ui/app.py](src/ui/app.py))
- **Document Indexer**: Multi-format document processing ([src/indexer.py](src/indexer.py))
- **Pydantic Config**: Validated settings with Pydantic Settings ([src/core/config.py](src/core/config.py))
- **Security Module**: Input sanitization and SSRF protection ([src/core/security.py](src/core/security.py))
- **Custom Exceptions**: Structured error hierarchy ([src/core/exceptions.py](src/core/exceptions.py))
- **Test Suite**: Tests for config, data loader, security, models, vector store
