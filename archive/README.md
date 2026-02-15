# Archive

This directory contains files that are no longer actively used but kept for reference.

## Files

### vector_ground_truth_prompt.md
**Archived**: 2026-02-15
**Reason**: Evaluation now uses reference-free RAGAS metrics - manual `ground_truth_vector` values are no longer needed

**Background**:
- Original approach: Manually write `ground_truth_vector` descriptions for each test case
- Problem: Time-consuming, doesn't scale, subjective
- New approach: Reference-free RAGAS metrics automatically judge chunk relevance using LLM
- All `ground_truth_vector` fields in test_data.py are now set to `None`

**If you need it**: The prompt is still valid for generating human documentation of expected retrieval behavior, but it's optional and not used for evaluation metrics.

---

**Evaluation Architecture (Current)**:
- ✅ `ground_truth_answer`: Generated dynamically by judge LLM during evaluation
- ✅ `ground_truth_vector`: Set to `None` - not needed (reference-free metrics)
- ✅ Context Precision/Relevancy: LLM judges chunk relevance automatically
- ✅ Context Recall: Skipped (requires manual ground truth)
