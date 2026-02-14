"""
FILE: verify_ground_truth.py
STATUS: Active
RESPONSIBILITY: Unified ground truth verification and establishment for ALL test cases
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Shahu

RESPONSIBILITIES:
1. SQL/Hybrid Ground Truth VERIFICATION - Verify against actual database
2. Vector Ground Truth ESTABLISHMENT - Provide LLM prompt for establishing ground truth

Usage:
    poetry run python src/evaluation/verify_ground_truth.py              # Verify SQL + Hybrid against DB
    poetry run python src/evaluation/verify_ground_truth.py sql          # SQL only (80 cases)
    poetry run python src/evaluation/verify_ground_truth.py hybrid       # Hybrid only (51 cases)
    poetry run python src/evaluation/verify_ground_truth.py vector       # Show vector ground truth prompt
"""
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.evaluation.consolidated_test_cases import ALL_TEST_CASES
from src.evaluation.unified_model import TestType

DB_PATH = Path(__file__).parent.parent.parent / "data" / "sql" / "nba_stats.db"


def query_db(sql: str) -> list[dict]:
    """Execute SQL and return results as list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except Exception as e:
        return [{"__error__": str(e)}]
    finally:
        conn.close()


def normalize_value(val: Any) -> Any:
    """Normalize values for comparison (handle float precision)."""
    if isinstance(val, float):
        return round(val, 1)
    return val


def compare_results(expected: Any, actual: list[dict]) -> tuple[bool, str, dict]:
    """Compare expected ground truth with actual results."""
    if expected is None:
        return True, "No ground truth data (analysis query)", {"type": "analysis_only"}

    if actual and "__error__" in actual[0]:
        return False, f"SQL error: {actual[0]['__error__']}", {"error": actual[0]["__error__"]}

    if isinstance(expected, dict):
        expected = [expected]

    if len(actual) != len(expected):
        return False, f"Count mismatch: expected {len(expected)}, got {len(actual)}", {
            "expected_count": len(expected),
            "actual_count": len(actual),
            "expected": expected,
            "actual": actual[:10],
        }

    if actual and expected:
        first_key = list(expected[0].keys())[0]
        try:
            actual_sorted = sorted(actual, key=lambda x: (x.get(first_key) is None, x.get(first_key)))
            expected_sorted = sorted(expected, key=lambda x: (x.get(first_key) is None, x.get(first_key)))
        except (TypeError, KeyError):
            actual_sorted = actual
            expected_sorted = expected

        mismatches = []
        for idx, (exp_row, act_row) in enumerate(zip(expected_sorted, actual_sorted)):
            for key in exp_row:
                if key not in act_row:
                    return False, f"Missing key '{key}' in actual results", {
                        "row": idx,
                        "expected_keys": list(exp_row.keys()),
                        "actual_keys": list(act_row.keys()),
                    }

                exp_val = normalize_value(exp_row[key])
                act_val = normalize_value(act_row[key])

                if exp_val != act_val:
                    mismatches.append({
                        "row": idx,
                        "key": key,
                        "expected": exp_val,
                        "actual": act_val,
                    })

        if mismatches:
            return False, "Value mismatches found", {"mismatches": mismatches, "expected": expected, "actual": actual}

    return True, "Match", {"expected": expected, "actual": actual}


def verify_answer_mentions_data(answer: str, data: Any) -> tuple[bool, str]:
    """Verify that ground_truth_answer mentions key values from ground_truth_data."""
    if data is None:
        return True, "No specific data to verify (analysis question)"

    if isinstance(data, dict):
        data = [data]

    missing_mentions = []
    for row in data:
        if "name" in row:
            name = row["name"]
            name_parts = name.split()
            if not any(part in answer for part in name_parts):
                missing_mentions.append(f"Player '{name}' not mentioned")

    if missing_mentions:
        return False, "; ".join(missing_mentions[:3])

    return True, "Answer appropriately mentions data"


def verify_dataset(test_cases: list, dataset_name: str) -> dict:
    """Verify a dataset of test cases against the database."""
    print(f"\n{'=' * 80}")
    print(f"{dataset_name.upper()} GROUND TRUTH VERIFICATION ({len(test_cases)} test cases)")
    print(f"{'=' * 80}")

    results = {"passed": [], "failed": [], "warnings": []}

    for i, test_case in enumerate(test_cases, 1):
        question = test_case.question
        expected_data = test_case.ground_truth_data
        expected_answer = test_case.ground_truth_answer
        sql = test_case.expected_sql
        category = test_case.category

        print(f"\n[{i}/{len(test_cases)}] {category}")
        print(f"Q: {question[:80]}...")

        actual_data = query_db(sql)
        is_match, message, details = compare_results(expected_data, actual_data)

        if not is_match:
            print(f"  \u274c SQL DATA MISMATCH: {message}")
            if "mismatches" in details:
                for mm in details["mismatches"][:3]:
                    print(f"     Row {mm['row']}, {mm['key']}: expected {mm['expected']}, got {mm['actual']}")
            results["failed"].append({"test_case": test_case, "message": message, "details": details})
            continue

        answer_ok, answer_msg = verify_answer_mentions_data(expected_answer, expected_data)

        if not answer_ok:
            print(f"  \u26a0\ufe0f  ANSWER WARNING: {answer_msg}")
            results["warnings"].append({"test_case": test_case, "message": answer_msg})

        print(f"  \u2705 PASS: {message}")
        results["passed"].append(test_case)

    # Summary
    print(f"\n{'=' * 80}")
    print(f"{dataset_name.upper()} SUMMARY")
    print(f"{'=' * 80}")
    print(f"\u2705 Passed:  {len(results['passed'])}/{len(test_cases)}")
    print(f"\u274c Failed:  {len(results['failed'])}/{len(test_cases)}")
    print(f"\u26a0\ufe0f  Warnings: {len(results['warnings'])}/{len(test_cases)}")

    if results["failed"]:
        print(f"\n\u274c FAILED TEST CASES:")
        for item in results["failed"]:
            tc = item["test_case"]
            print(f"\n  [{tc.category}] {tc.question[:70]}...")
            print(f"  Issue: {item['message']}")
            if "mismatches" in item["details"]:
                for mm in item["details"]["mismatches"][:5]:
                    print(f"    - {mm['key']}: expected {mm['expected']}, got {mm['actual']}")

    if results["warnings"]:
        print(f"\n\u26a0\ufe0f  WARNINGS:")
        for item in results["warnings"]:
            tc = item["test_case"]
            print(f"  - {tc.question[:60]}... | {item['message']}")

    success_rate = len(results['passed']) / len(test_cases) * 100
    print(f"\n\U0001f4ca Success Rate: {success_rate:.1f}%")

    if len(results['failed']) == 0:
        print(f"\n\u2705 ALL {dataset_name.upper()} GROUND TRUTH IS CORRECT!")
    else:
        print(f"\n\u26a0\ufe0f  {len(results['failed'])} test cases need correction")

    print("=" * 80)

    return results


# ============================================================================
# VECTOR GROUND TRUTH ESTABLISHMENT PROMPT
# ============================================================================

VECTOR_GROUND_TRUTH_PROMPT = """
# VECTOR GROUND TRUTH ESTABLISHMENT PROMPT

## Purpose
This prompt establishes ground truth for Vector test cases based on actual document content
stored in the FAISS vector index (358 chunks total).

## Source Documents

### A. Reddit Discussion PDFs (353 chunks - OCR-extracted)
- Reddit 1.pdf: "Who are teams in the playoffs that have impressed you?" (u/MannerSuperb, 31 upvotes, 59 chunks, max comment: 88 upvotes)
- Reddit 2.pdf: "How is it that the two best teams in the playoffs..." (u/mokaloca82, 457 upvotes, 106 chunks, max comment: 756 upvotes)
- Reddit 3.pdf: "Reggie Miller is the most efficient first option in NBA playoff history" (u/hqppp, 1,300 upvotes, 158 chunks, max comment: 11,515 upvotes)
- Reddit 4.pdf: "Which NBA team did not have home court advantage until the NBA Finals?" (u/DonT012, 272 upvotes, 30 chunks, max comment: 240 upvotes)

Metadata per chunk: source, post_title, post_author, post_upvotes, comment_author, comment_upvotes, is_nba_official, quality_score

### B. NBA Statistics Glossary (5 chunks)
Source: regular NBA.xlsx → "Dictionnaire des données" sheet
Contains 43 NBA statistical metric definitions in French (PTS, TS%, EFG%, DD2, TD3, OFFRTG, DEFRTG, NETRTG, PIE, etc.)

## Retrieval Scoring Formula
- Cosine similarity (50%): Semantic match via FAISS embeddings
- BM25 (35%): Exact keyword matching
- Metadata boost (15%): Comment upvotes (0-2%), post engagement (0-1%), NBA official (+2%)

## LLM PROMPT TEMPLATE

You are establishing ground truth for a RAG evaluation system.

I will provide:
1. Full OCR-extracted text of 4 Reddit discussion PDFs
2. NBA statistics glossary ("Dictionnaire des données") - 43 metric definitions in French

All content is chunked and stored in FAISS (358 chunks: 353 Reddit, 5 glossary).

For each test question, generate a ground_truth description specifying:

1. **Expected source document(s)**:
   - Reddit: filename (e.g., "Reddit 1.pdf"), post title, author
   - Glossary: "regular NBA.xlsx (glossary)"

2. **Expected content themes**:
   - Specific topics, names, statistics, arguments
   - Include exact names, numbers, quotes when possible

3. **Expected metadata**:
   - Post author, post upvotes, top comment upvotes (affects ranking)

4. **Expected similarity range**:
   - Direct topic match: 80-95%
   - Indirect/tangential: 68-80%
   - Out-of-scope/no match: 50-70%

5. **Expected retrieval behavior**:
   - Chunk count (e.g., "2-5 chunks")
   - Whether boosting affects ranking

## Special Query Categories

### Out-of-scope queries (weather, cooking, politics)
Vector search WILL return chunks (always returns k results). State:
- Out-of-scope
- Retrieved chunks will be irrelevant (estimate low similarity)
- LLM should DECLINE and state knowledge base covers NBA basketball only

### Adversarial/security queries (XSS, SQL injection, path traversal)
State:
- System treats input as literal text, not execute it
- Vector search returns random/irrelevant chunks
- LLM should ask clarification or decline

### Noisy/informal queries (typos, slang, abbreviations)
State:
- What query maps to after noise removal
- Which document should be retrieved despite noise
- Similarity will be LOWER (typically -5% to -10% vs clean equivalent)

### Conversational/follow-up queries (pronouns, context references)
State:
- What pronoun/reference resolves to (e.g., "their" = Lakers from Turn 1)
- System needs conversation context to resolve references
- Which turn establishes context, which turns are follow-ups

### Glossary/terminology queries (NBA metric definitions)
State:
- Glossary from regular NBA.xlsx should rank HIGHEST for metric definitions
- Descriptions are in French (e.g., "Points marqués en moyenne par match")
- If term NOT in glossary (e.g., "pick and roll", "zone defense"), state that glossary lacks definition
- Glossary only covers statistical abbreviations (PTS, TS%, EFG%, DD2), NOT basketball concept definitions

## Rules
- ONLY reference content that actually exists in provided documents
- Do NOT invent or assume content not present
- If question asks about something not covered, state that explicitly
- Include specific names, numbers, quotes to make ground truth verifiable
- For engagement-related questions, reference actual upvote counts
- For glossary queries, note descriptions are in French

## Output Format
Format each ground_truth as a single paragraph starting with "Should retrieve..." for use in UnifiedTestCase.

EXAMPLE FORMATS:

# Reddit discussion query
"Should retrieve Reddit 1.pdf: 'Who are teams in the playoffs that have impressed you?' by u/MannerSuperb (31 post upvotes, max comment upvotes 88). Expected teams: Magic (Paolo Banchero, Franz Wagner), Indiana Pacers, Minnesota Timberwolves (Anthony Edwards), Pistons. Comments discuss exceeding expectations, young talent, surprising playoff performances. Expected sources: 2-5 chunks from Reddit 1.pdf with 75-85% similarity."

# Glossary query
"Should retrieve regular NBA.xlsx (glossary). Expected definition: TS% — 'True Shooting % (inclut FG et FT dans l'efficacité)'. Glossary should rank HIGHEST (85-95% similarity) for metric definition queries. Note: Reddit 3 also discusses TS% but glossary MUST rank higher for definition queries. Expected source: glossary chunk #1."

# Out-of-scope query
"Out-of-scope query. Vector search WILL retrieve irrelevant chunks (likely Reddit PDFs with ~65-70% similarity due to semantic overlap with 'Los Angeles'). However, LLM should recognize retrieved content is basketball-related, NOT weather, and respond with 'I don't have information about weather forecasts. My knowledge base contains NBA basketball discussions only.' Tests LLM's ability to reject irrelevant context. Expected: LLM declines."

# Conversational follow-up
"Follow-up question referencing 'their' = Lakers from Turn 1. System should: (1) maintain conversation context (Lakers = subject), (2) retrieve Lakers-specific content about strengths. Expected sources: Same Reddit chunks mentioning Lakers. Similarity: 70-80%. Tests context maintenance across turns. NOTE: Evaluation should provide Turn 1 question as context."

Here are the source documents:
[PASTE FULL OCR CONTENT OF ALL 4 REDDIT PDFs HERE]
[PASTE CONTENT OF data/reference/nba_dictionary_vectorized.txt HERE]

Here are the test questions:
[LIST OF VECTOR TEST CASE QUESTIONS FROM consolidated_test_cases.py]
"""


def show_vector_prompt():
    """Display the vector ground truth establishment prompt."""
    vector_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.VECTOR]

    print(VECTOR_GROUND_TRUTH_PROMPT)
    print(f"\n{'=' * 80}")
    print(f"VECTOR TEST CASES ({len(vector_cases)} total)")
    print(f"{'=' * 80}\n")

    for i, tc in enumerate(vector_cases, 1):
        print(f"{i}. {tc.question}")
        if tc.category:
            print(f"   Category: {tc.category}")
        if tc.ground_truth:
            print(f"   ✅ Has ground_truth")
        else:
            print(f"   ❌ Missing ground_truth")
        print()


if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    # Vector mode shows the LLM prompt for establishing ground truth
    if mode == "vector":
        show_vector_prompt()
        sys.exit(0)

    # Filter test cases by type
    sql_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.SQL]
    hybrid_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.HYBRID]

    all_results = {}

    if mode in ("sql", "all"):
        all_results["sql"] = verify_dataset(sql_cases, "SQL")

    if mode in ("hybrid", "all"):
        all_results["hybrid"] = verify_dataset(hybrid_cases, "Hybrid")

    if mode == "all" and len(all_results) == 2:
        total_passed = sum(len(r["passed"]) for r in all_results.values())
        total_failed = sum(len(r["failed"]) for r in all_results.values())
        total_cases = len(sql_cases) + len(hybrid_cases)

        print(f"\n{'=' * 80}")
        print("OVERALL SUMMARY")
        print(f"{'=' * 80}")
        print(f"\u2705 Passed:  {total_passed}/{total_cases}")
        print(f"\u274c Failed:  {total_failed}/{total_cases}")
        print(f"\U0001f4ca Overall Success Rate: {total_passed / total_cases * 100:.1f}%")
        print("=" * 80)
