# Flexible Evaluation Script - User Guide

## Overview

The flexible evaluation script (`scripts/run_flexible_evaluation.py`) is a comprehensive evaluation tool that provides:

1. ✅ **Flexible test case selection** - Select specific test cases by indices, types, or categories
2. ✅ **Classification confidence tracking** - Shows when LLM is used vs heuristic classification
3. ✅ **SQL-specific metrics** - Query complexity analysis, execution time, structure metrics
4. ✅ **Enhanced executive summary** - Comprehensive overview with issue monitoring
5. ✅ **Per-query detailed reports** - Complete answers, SQL queries, RAGAS metrics, issues
6. ✅ **Conversation support** - Test multi-turn conversations with pronoun resolution

## Usage Examples

### Run Optimized 9-Case Dataset

```bash
poetry run python scripts/run_flexible_evaluation.py --preset optimized
```

This runs the same 9 test cases as before (3 SQL + 3 Vector + 3 Hybrid).

### Run Optimized Dataset + Conversation Test

```bash
poetry run python scripts/run_flexible_evaluation.py --preset optimized --with-conversation
```

Adds a 2-turn conversation test to verify pronoun resolution.

### Run Specific Test Cases by Index

```bash
# Run test cases 0, 1, 2, 44, and 75
poetry run python scripts/run_flexible_evaluation.py --indices 0 1 2 44 75
```

### Run Test Cases by Type

```bash
# Run first 10 SQL test cases
poetry run python scripts/run_flexible_evaluation.py --type sql --limit 10

# Run all vector test cases
poetry run python scripts/run_flexible_evaluation.py --type vector

# Run 5 hybrid test cases
poetry run python scripts/run_flexible_evaluation.py --type hybrid --limit 5
```

### Run Test Cases by Category

```bash
# Run all simple top-N queries
poetry run python scripts/run_flexible_evaluation.py --category simple_sql_top_n

# Run all player statistics queries
poetry run python scripts/run_flexible_evaluation.py --category player_stats
```

## Features in Detail

### 1. Classification Confidence Tracking

The script tracks how queries were classified:

- **Heuristic Classification (≥0.9 confidence)**: Fast pattern-based classification
- **LLM Classification (<0.9 confidence)**: Slower but more accurate LLM-based classification

**Report Example:**
```
### Classification Method Distribution

| Method | Count | Percentage |
|--------|-------|------------|
| Heuristic (High Confidence ≥0.9) | 8 | 88.9% |
| LLM Classification | 1 | 11.1% |
```

This helps you understand when the agent needs to use the LLM for classification vs when the heuristic is sufficient.

### 2. SQL-Specific Metrics

For every SQL query, the script analyzes:

- **Complexity Level**: Trivial, Simple, Moderate, Complex
- **Complexity Score**: Numerical score based on query structure
- **Join Count**: Number of JOIN operations
- **Filter Count**: Number of WHERE/AND conditions
- **Aggregation**: Uses GROUP BY, AVG, SUM, etc.
- **Sorting**: Uses ORDER BY
- **Subqueries**: Contains nested SELECT
- **Window Functions**: Uses OVER, PARTITION BY, etc.

**Report Example:**
```
**SQL Query:**
```sql
SELECT p.name, ps.pts FROM players p
JOIN player_stats ps ON p.id = ps.player_id
ORDER BY ps.pts DESC LIMIT 1;
```

**SQL Complexity:** Simple (score: 2)
- Joins: 1
- Filters: 0
- Aggregation: No
- Subqueries: No
```

### 3. Enhanced Executive Summary

The executive summary includes:

- **Total queries and success rate**
- **Average processing time**
- **Classification method distribution**
- **RAGAS metrics (averaged across all queries)**
- **Issue monitoring with severity levels**
- **SQL complexity distribution**

**Report Example:**
```
## Executive Summary

- **Total Queries:** 10
- **Successful Executions:** 10 (100.0%)
- **Failed Executions:** 0
- **Average Processing Time:** 8542ms

### Classification Method Distribution
[... stats ...]

### RAGAS Metrics (Averaged)

| Metric | Score | Status |
|--------|-------|--------|
| Faithfulness | 0.900 | ✅ |
| Answer Correctness | 0.880 | ⚠️ |
| Answer Relevancy | 0.850 | ⚠️ |
| Context Precision | 0.750 | ⚠️ |
| Context Relevancy | 0.800 | ⚠️ |
```

### 4. Issue Monitoring

The script automatically detects and reports issues:

**Issue Types:**
- ❌ **Critical**: Low RAGAS scores (<0.5), SQL errors, pronoun resolution failures
- ⚠️ **Warning**: Moderate RAGAS scores (0.5-0.7), short responses
- ℹ️ **Info**: Low classification confidence, LLM usage for classification

**Report Example:**
```
## Issue Monitoring

**Total Issues Detected:** 12

| Severity | Count |
|----------|-------|
| ❌ Critical | 2 |
| ⚠️ Warning | 8 |
| ℹ️ Info | 2 |

### Critical Issues

- **low_metric**: Context Precision score is 0.000 (below 0.7 threshold)
- **pronoun_resolution_failed**: Failed to resolve pronoun 'they' to 'Shai Gilgeous-Alexander'
```

### 5. Per-Query Detailed Reports

Each query gets a detailed section with:

- Complete answer (first 500 chars)
- SQL query executed (if applicable)
- SQL complexity analysis
- Vector sources retrieved (top 5)
- All RAGAS metrics
- Processing time
- Issues detected

### 6. Conversation Support

Add `--with-conversation` to test multi-turn conversations:

**Conversation Test:**
- **Turn 1**: "Who scored the most points?"
- **Turn 2**: "What team do they play for?"

The script verifies:
- Pronoun resolution ("they" → "Shai Gilgeous-Alexander")
- Conversation context usage
- Response quality

## Output Files

The script generates two files:

1. **JSON file**: `flexible_eval_YYYYMMDD_HHMMSS.json`
   - Raw results data
   - Summary statistics
   - Classification stats
   - All issues detected

2. **Markdown report**: `flexible_eval_YYYYMMDD_HHMMSS.md`
   - Human-readable report
   - Executive summary
   - Issue monitoring
   - Per-query details

## Test Case Selection Reference

### Available Presets

- `optimized`: 9 carefully selected test cases (3 SQL + 3 Vector + 3 Hybrid)

### Test Types

- `sql`: SQL-only queries (80 total in test data)
- `vector`: Vector-only queries (75 total in test data)
- `hybrid`: Hybrid queries (51 total in test data)

### Example Categories

- `simple_sql_top_n`: Top N ranking queries
- `player_stats`: Player statistics queries
- `team_stats`: Team statistics queries
- `advanced_sql`: Complex SQL with joins, aggregations, subqueries
- `qualitative_vector`: Opinion/analysis queries
- `biographical_hybrid`: Player/team biography queries

## Comparison with Previous Scripts

| Feature | Old Script | New Flexible Script |
|---------|------------|---------------------|
| Test case selection | Fixed dataset | ✅ Flexible (indices, types, categories, presets) |
| Classification confidence | ❌ Not tracked | ✅ Tracked (heuristic vs LLM) |
| SQL metrics | ❌ Only execution | ✅ Complexity analysis, structure metrics |
| Executive summary | ✅ Basic | ✅ Enhanced with issue monitoring |
| Issue detection | ❌ Manual | ✅ Automatic with severity levels |
| SQL complexity | ❌ Not analyzed | ✅ Full complexity breakdown |
| Conversation test | ✅ Hardcoded | ✅ Optional with `--with-conversation` |

## Maintenance and Extension

### Adding New Test Cases

Test cases are defined in `src/evaluation/test_data.py`. The flexible script automatically picks them up.

### Adding New Issue Detection

Edit the `detect_issues()` function in the script to add new issue types.

### Adding New SQL Metrics

Edit the `analyze_sql_complexity()` function to add new SQL analysis metrics.

## Best Practices

1. **Start small**: Test with `--preset optimized` first
2. **Add conversation**: Use `--with-conversation` to verify pronoun resolution
3. **Check issues**: Review the issue monitoring section for problems
4. **SQL complexity**: Use complexity metrics to identify hard queries
5. **Classification stats**: Monitor how often LLM is used for classification

## Troubleshooting

### No test cases selected

**Error**: "Error: No test cases selected"

**Solution**: You must specify one of:
- `--indices <numbers>`
- `--type <sql|vector|hybrid>`
- `--category <category_name>`
- `--preset <preset_name>`

### Conversation test fails

**Issue**: Pronoun not resolved

**Check**:
1. Is conversation history being saved to database?
2. Are field names correct (`query`/`response` not `user_query`/`assistant_response`)?
3. Is conversation context being passed to agent?

### RAGAS metrics fail

**Check**:
- Google API key is valid
- Rate limits not exceeded
- Ground truth data is properly formatted

---

**Last Updated**: 2026-02-15
