# Vector Ground Truth Generation Prompt

## Purpose

**IMPORTANT**: This document is for **documentation purposes only**. The `ground_truth_vector` field is **OPTIONAL** and not required for evaluation.

**Why?** RAGAS metrics now use **reference-free evaluation**:
- Context Precision/Relevancy: LLM judges chunk relevance automatically (no manual ground truth needed)
- Answer Quality Metrics: Judge LLM generates expected answers dynamically

**When to use this**: Generate `ground_truth_vector` descriptions for:
- Human documentation (what SHOULD be retrieved)
- Debugging retrieval issues
- Understanding test case expectations

All `ground_truth_vector` fields in [test_data.py](src/evaluation/test_data.py) are currently set to `None`.

## How the Agent Retrieves Documents

The ReAct agent has a `search_knowledge_base(query, k=5)` tool that:

1. **Generates embedding** from the query
2. **Searches vector store** using 3-signal hybrid scoring:
   - **Cosine similarity (70%)**: Semantic match from embeddings
   - **BM25 (15%)**: Keyword/term matching
   - **Quality boost (15%)**: LLM-assessed quality score (0-1)
3. **Returns top k chunks** with:
   - Text content
   - Similarity score (0-100)
   - Source (filename)
   - Metadata: title, author, upvotes, post_id

**Key insight**: Higher upvotes and better quality scores give a ranking boost, so highly-engaged content ranks higher for equal semantic relevance.

## Source Documents

The vector store contains **374 chunks from 4 Reddit discussion threads** (OCR-extracted):

| File | Post Title | Author | Post Upvotes | Total Chunks | Max Comment Upvotes |
|------|-----------|--------|--------------|--------------|---------------------|
| Reddit 1.pdf | "Who are teams in the playoffs that have impressed you?" | u/MannerSuperb | 31 | 64 | 186 |
| Reddit 2.pdf | "How is it that the two best teams in the playoffs based on stats, having a chance of playing against each other in the Finals, is considered to be a snoozefest?" | u/mokaloca82 | 457 | 111 | ~756 |
| Reddit 3.pdf | "Reggie Miller is the most efficient first option in NBA playoff history" | u/hqppp | 1,300 | 166 | 11,515 ⭐ |
| Reddit 4.pdf | "Which NBA team did not have home court advantage until the NBA Finals?" | u/DonT012 | 272 | 33 | 240 |

**Chunk format**: Each chunk contains the post header (title, author, upvotes) + post content or comment text. Metadata includes `comment_author` and `comment_upvotes` which affect quality boosting.

**Note**: NBA glossary is NOT in the vector store - only Reddit discussions.

## Task

For each test question, generate a `ground_truth_vector` that describes:

1. **Which Reddit thread(s)** should be retrieved
2. **What specific content** should appear (names, players, teams, stats, quotes, arguments)
3. **Include metadata**: Post title, author, post upvotes, comment upvotes
4. **Mention engagement**: High comment upvotes = stronger quality boost

**Why upvotes matter**: The agent's quality boost (15% of score) comes from `comment_upvotes`, so highly-upvoted comments rank higher. Ground truth should reference actual upvote counts (e.g., "11,515 upvotes" for Reddit 3's top comment).

## Output Format

Single paragraph starting with:
- **"Should retrieve [source]..."** for in-scope queries
- **"Out-of-scope query..."** for weather, cooking, politics, etc.

## Examples

```python
# Simple Reddit query
ground_truth_vector="Should retrieve Reddit 1.pdf: 'Who are teams in the playoffs that have impressed you?' by u/MannerSuperb (31 post upvotes, 64 chunks). Expected teams: Magic (Paolo Banchero, Franz Wagner), Indiana Pacers, Minnesota Timberwolves (Anthony Edwards), Pistons. Max comment upvotes: 186. Discusses exceeding expectations and surprising playoff performances."

# High-engagement query
ground_truth_vector="Should retrieve Reddit 3.pdf: 'Reggie Miller is the most efficient first option in NBA playoff history' by u/hqppp (1,300 post upvotes, 166 chunks). Top comment upvotes: 11,515 (HIGHEST engagement - strong quality boost). Expected discussion: Reggie Miller's 115% TS%, efficiency metrics, playoff performance comparisons."

# Out-of-scope query
ground_truth_vector="Out-of-scope query. Vector search WILL retrieve irrelevant chunks (likely Reddit PDFs with ~65-70% similarity due to keyword overlap). LLM should recognize retrieved content is basketball-related, NOT weather/cooking/politics, and decline to answer stating knowledge base covers NBA only."
```

## Rules

1. ONLY reference content actually present in the documents
2. Do NOT invent content
3. Include specific names, numbers, quotes from the source
4. For out-of-scope queries, state that LLM should decline

## Prompt Template

```
You are generating ground truth for a RAG evaluation system.

I will provide full OCR text from 4 Reddit NBA discussion threads (374 chunks total).

For each question, generate a `ground_truth_vector` paragraph describing:
- Which Reddit thread(s) should be retrieved
- What specific content should appear (players, teams, stats, arguments, quotes)
- Post metadata: title, author, post upvotes, max comment upvotes
- For out-of-scope queries: state "Out-of-scope query..." and that LLM should decline

FORMAT: Single paragraph starting with "Should retrieve..." or "Out-of-scope query..."

### REDDIT OCR CONTENT
[PASTE FULL OCR CONTENT FROM data/vector/_ocr_per_file/Reddit *.pkl]

### QUESTIONS
[LIST OF QUESTIONS]
```

## How to Use (OPTIONAL)

**Note**: This is **optional** - evaluation works without manual `ground_truth_vector` values.

If you want to document expected retrieval behavior:

1. Load OCR content from `data/vector/_ocr_per_file/Reddit *.pkl` (4 files, 374 chunks total)
2. Or read raw PDFs from `data/inputs/Reddit *.pdf` and extract text
3. Paste Reddit OCR content into prompt template above
4. Generate `ground_truth_vector` for each question
5. Update `ground_truth_vector` field in [test_data.py](src/evaluation/test_data.py) (currently all set to `None`)
6. Run evaluation: `poetry run python -m src.evaluation.run_evaluation --type vector`

**Tip**: You can create a **summarized version** of the Reddit OCR content for the prompt.

---

**EVALUATION APPROACH**:
- **`ground_truth_answer`**: Generated dynamically by judge LLM during evaluation ✅
- **`ground_truth_vector`**: OPTIONAL - used only for human documentation, not for metrics ✅
- **RAGAS metrics**: Use reference-free evaluation (LLM judges chunk relevance automatically) ✅
