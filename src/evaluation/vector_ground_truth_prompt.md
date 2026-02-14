# Vector Ground Truth Establishment — Methodology & Prompt

## Purpose

This document describes the methodology used to establish ground truth for the 75 vector (contextual) test cases in `src/evaluation/test_cases/vector_test_cases.py`. Unlike SQL and Hybrid test cases whose ground truth is verified against the database, vector test cases use **descriptive expectations** grounded in the actual document content stored in the FAISS vector index.

## Source Documents

The vector store (358 chunks total) contains content from **two types of sources**:

### A. Reddit Discussion PDFs (353 chunks — OCR-extracted)

| Document | Post Title | Author | Post Upvotes | Chunks | Max Comment Upvotes |
|----------|-----------|--------|-------------|--------|---------------------|
| Reddit 1.pdf | "Who are teams in the playoffs that have impressed you?" | u/MannerSuperb | 31 | 59 | 88 |
| Reddit 2.pdf | "How is it that the two best teams in the playoffs based on stats, having a chance of playing against each other in the Finals, is considered to be a snoozefest?" | u/mokaloca82 | 457 | 106 | 756 |
| Reddit 3.pdf | "Reggie Miller is the most efficient first option in NBA playoff history" | u/hqppp | 1,300 | 158 | 11,515 |
| Reddit 4.pdf | "Which NBA team did not have home court advantage until the NBA Finals?" | u/DonT012 | 272 | 30 | 240 |

Each Reddit chunk has metadata: `source`, `post_title`, `post_author`, `post_upvotes`, `comment_author`, `comment_upvotes`, `is_nba_official`, `quality_score`, `num_comments`.

### B. NBA Statistics Glossary (5 chunks — from "Dictionnaire des données" sheet)

Source: `regular NBA.xlsx` → sheet "Dictionnaire des données"

Contains 43 NBA statistical metric definitions with French descriptions. Examples:
- **PTS**: Points marqués en moyenne par match
- **TS%**: True Shooting % (inclut FG et FT dans l'efficacité)
- **EFG%**: Effective Field Goal % (pondère les 3 points)
- **DD2**: Double-doubles (≥10 dans deux catégories principales)
- **TD3**: Triple-doubles (≥10 dans trois catégories principales)
- **OFFRTG / DEFRTG / NETRTG**: Offensive/Defensive/Net Rating
- **PIE**: Player Impact Estimate — évaluation globale de l'impact

This glossary is vectorized as formatted text from `data/reference/nba_dictionary_vectorized.txt`. It provides definitions for terminology queries (e.g., "What is TS%?", "What is a triple-double?").

**Note**: The glossary only covers statistical metric abbreviations from the NBA database columns. It does NOT contain basketball concept definitions like "pick and roll" or "zone defense".

Source location: `data/inputs/` (PDF files + Excel processed through data pipeline)

## Methodology

Ground truth was established using an **LLM-assisted approach**:

1. **Extract**: OCR-extracted text from all 4 Reddit PDFs AND the NBA glossary content were provided to an LLM
2. **Analyze**: The LLM read the full content of each document, including post text, comments, upvote counts, user metadata, and glossary metric definitions
3. **Generate**: For each test question, the LLM generated a ground truth description based solely on what exists in the documents
4. **Validate**: Each ground truth was manually reviewed to ensure it accurately references content present in the source documents

## Prompt Template

The following prompt was used to generate ground truth expectations. Provide this prompt along with the full OCR content of all 4 Reddit PDFs AND the glossary content:

```
You are helping establish ground truth for a RAG (Retrieval-Augmented Generation) evaluation system.

I will provide you with:
1. The full OCR-extracted text of 4 Reddit discussion PDFs
2. The NBA statistics glossary ("Dictionnaire des données") containing 43 metric definitions in French

All of this content has been chunked and stored in a FAISS vector index (358 chunks total: 353 from Reddit, 5 from the glossary).

## CHUNK METADATA

Each Reddit chunk carries the following metadata used for retrieval scoring:
- `source`: filename (e.g., "Reddit 1.pdf")
- `post_title`: original Reddit post title
- `post_author`: Reddit username
- `post_upvotes`: post-level upvotes (used for engagement boosting)
- `comment_author`: author of the comment in this chunk
- `comment_upvotes`: comment-level upvotes (used for within-post boosting)
- `is_nba_official`: 0 or 1 (NBA official accounts get +2% boost)
- `quality_score`: pre-computed quality score (0-1)

The glossary chunks have source="regular NBA.xlsx" and no Reddit-specific metadata.

## RETRIEVAL SCORING

The system uses a 3-signal hybrid scoring formula:
- Cosine similarity (50%): Semantic match via FAISS embeddings
- BM25 (35%): Exact keyword matching
- Metadata boost (15%): Comment upvotes (0-2%), post engagement (0-1%), NBA official (+2%)

This means highly-upvoted content ranks higher for equal semantic relevance.

## YOUR TASK

For each test question I provide, generate a ground truth description that specifies:

1. **Expected source document(s)**: Which document(s) should the retrieval system find?
   - For Reddit: reference by filename (e.g., "Reddit 1.pdf"), include the post title and author
   - For glossary: reference as "regular NBA.xlsx (glossary)"

2. **Expected content themes**: What specific topics, names, statistics, or arguments from the source should appear in the retrieved context? Include exact names, numbers, and quotes when possible.

3. **Expected metadata**: Include post author, post upvotes, and top comment upvotes where relevant — these affect retrieval ranking via the boosting formula.

4. **Expected similarity range**: Estimate a percentage range (e.g., "75-85%") based on how directly the question maps to the source content. Consider:
   - Direct topic match: 80-95%
   - Indirect/tangential: 68-80%
   - Out-of-scope/no match: 50-70% (system will still return chunks, but irrelevant)

5. **Expected retrieval behavior**: How many chunks should be retrieved (e.g., "2-5 chunks"), and should boosting affect ranking?

## SPECIAL QUERY CATEGORIES

Handle these query types with specific ground truth patterns:

### Out-of-scope queries (weather, cooking, politics, etc.)
The vector search WILL still return chunks (it always returns k results). State:
- That it is out-of-scope
- That retrieved chunks will be irrelevant (estimate low similarity)
- That the LLM should DECLINE to answer and state the knowledge base covers NBA basketball only

### Adversarial / security queries (XSS, SQL injection, path traversal, etc.)
State:
- The system should treat input as literal text, not execute it
- Vector search will return random/irrelevant chunks
- The LLM should ask for clarification or decline

### Noisy / informal queries (typos, slang, abbreviations)
State:
- What the query maps to after noise removal
- Which document should be retrieved despite the noise
- That similarity will be LOWER due to noise (typically 5-10% lower than clean equivalent)

### Conversational / follow-up queries (pronouns, context references)
State:
- What the pronoun/reference resolves to (e.g., "their" = Lakers from Turn 1)
- That the system needs conversation context to resolve references
- Which turn establishes the context, and which turns are follow-ups

### Glossary / terminology queries (definitions of NBA metrics)
State:
- That the glossary from regular NBA.xlsx should rank HIGHEST for metric definitions
- That glossary descriptions are in French (e.g., "Points marqués en moyenne par match")
- If the term is NOT in the glossary (e.g., "pick and roll", "zone defense"), state that the glossary lacks this definition and Reddit context (if any) is acceptable
- The glossary only covers statistical abbreviations (PTS, TS%, EFG%, DD2, etc.), not basketball concept definitions

## IMPORTANT RULES

- ONLY reference content that actually exists in the provided documents
- Do NOT invent or assume content not present in the OCR text or glossary
- If a question asks about something not covered in any document, state that explicitly
- Include specific names, numbers, and quotes from the documents to make ground truth verifiable
- For engagement-related questions, reference the actual upvote counts from metadata
- For glossary queries, note that descriptions are in French

## OUTPUT FORMAT

FORMAT each ground truth as a single paragraph starting with "Should retrieve..." that can be used directly as the `ground_truth` field in an EvaluationTestCase.

Here are the source documents:

### REDDIT OCR CONTENT
[PASTE FULL OCR CONTENT OF ALL 4 REDDIT PDFs HERE]

### NBA GLOSSARY (Dictionnaire des données)
[PASTE CONTENT OF data/reference/nba_dictionary_vectorized.txt HERE]

Here are the test questions:
[LIST OF QUESTIONS]
```

## Ground Truth Format

Each test case ground truth follows this structure:

```python
# Reddit discussion query
EvaluationTestCase(
    question="What do Reddit users think about teams that impressed in the playoffs?",
    ground_truth=(
        "Should retrieve Reddit 1.pdf: 'Who are teams in the playoffs that have impressed you?' "
        "by u/MannerSuperb (31 post upvotes, max comment upvotes 88). Expected teams mentioned: Magic "
        "(Paolo Banchero, Franz Wagner), Indiana Pacers, Minnesota Timberwolves (Anthony Edwards), "
        "Pistons. Comments discuss exceeding expectations, young talent, and surprising playoff "
        "performances. Expected sources: 2-5 chunks from Reddit 1.pdf with 75-85% similarity."
    ),
    category=TestCategory.SIMPLE,
)

# Glossary query
EvaluationTestCase(
    question="Define true shooting percentage.",
    ground_truth=(
        "Should retrieve regular NBA.xlsx (glossary). Expected definition: TS% — "
        "'True Shooting % (inclut FG et FT dans l'efficacité)'. Glossary should rank HIGHEST "
        "(85-95% similarity) for metric definition queries. Note: Reddit 3 also discusses TS% "
        "but glossary MUST rank higher for definition queries. Expected source: glossary chunk #1."
    ),
    category=TestCategory.SIMPLE,
)

# Out-of-scope query
EvaluationTestCase(
    question="What is the weather forecast for Los Angeles tomorrow?",
    ground_truth=(
        "Out-of-scope query. Vector search WILL retrieve irrelevant chunks (likely Reddit PDFs "
        "with ~65-70% similarity due to semantic overlap with 'Los Angeles'). However, LLM should "
        "recognize retrieved content is basketball-related, NOT weather, and respond with 'I don't "
        "have information about weather forecasts. My knowledge base contains NBA basketball "
        "discussions only.' Tests LLM's ability to reject irrelevant context. Expected: LLM declines."
    ),
    category=TestCategory.NOISY,
)

# Conversational follow-up
EvaluationTestCase(
    question="What are their biggest strengths?",
    ground_truth=(
        "Follow-up question referencing 'their' = Lakers from Turn 1. System should: (1) maintain "
        "conversation context (Lakers = subject), (2) retrieve Lakers-specific content about strengths. "
        "Expected sources: Same Reddit chunks mentioning Lakers. Similarity: 70-80%. Tests context "
        "maintenance across turns. NOTE: Evaluation should provide Turn 1 question as context."
    ),
    category=TestCategory.CONVERSATIONAL,
)
```

Key elements in every ground truth:
- Source document identification (filename + post title + author for Reddit, "regular NBA.xlsx (glossary)" for definitions)
- Engagement metadata (post upvotes, comment upvotes) for boosting verification
- Specific content expectations (names, stats, themes, quotes)
- Similarity range estimate
- Expected chunk count
- For glossary: note French descriptions
- For out-of-scope: explicit "LLM should decline" instruction
- For conversational: pronoun resolution and turn context requirements

## Test Categories

| Category | Count | Description |
|----------|-------|-------------|
| SIMPLE | 20 | Direct retrieval from a single document |
| COMPLEX | 18 | Multi-document retrieval, cross-referencing, or analytical |
| NOISY | 25 | Off-topic, adversarial, XSS, or slang queries |
| CONVERSATIONAL | 12 | Follow-up queries with pronouns requiring context |

## How to Update Ground Truth

If the vector store content changes (new documents added, chunks re-processed):

1. Re-extract OCR text from all source documents in `data/inputs/`
2. Export the glossary content: `data/reference/nba_dictionary_vectorized.txt`
3. Use the prompt template above with the updated document content + glossary
4. Generate new ground truth descriptions for affected test cases
5. Review each generated ground truth against the actual document content
6. Update `src/evaluation/test_cases/vector_test_cases.py` with revised ground truth
7. Run vector evaluation to verify retrieval quality: `poetry run python -m src.evaluation.runners.run_vector_evaluation`

## Validation

Vector ground truth is validated during evaluation via RAGAS metrics:
- **Faithfulness**: Does the LLM response stay faithful to retrieved context?
- **Answer Relevancy**: Is the response relevant to the question?
- **Context Precision**: Are the retrieved chunks relevant to the question?
- **Context Recall**: Did retrieval find all relevant chunks?

See `src/evaluation/analysis/vector_quality_analysis.py` for metric calculation details.
