"""Analyze field usage in consolidated test cases."""
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.test_data import ALL_TEST_CASES

print('=' * 80)
print('TEST_TYPE vs QUERY_TYPE ANALYSIS')
print('=' * 80)

print('\nTestType enum values:')
print('  - SQL')
print('  - VECTOR')
print('  - HYBRID')

print('\nQueryType enum values:')
print('  - SQL_ONLY')
print('  - CONTEXTUAL_ONLY')
print('  - HYBRID')

print('\n--- ACTUAL DATA IN 206 TEST CASES ---')

# TestType distribution
test_type_values = Counter(tc.test_type.value for tc in ALL_TEST_CASES)
print(f'\nTestType distribution:')
for tt, count in sorted(test_type_values.items()):
    print(f'  {tt}: {count}')

# QueryType distribution
query_type_values = Counter(tc.query_type.value if tc.query_type else 'None' for tc in ALL_TEST_CASES)
print(f'\nQueryType distribution:')
for qt, count in sorted(query_type_values.items()):
    print(f'  {qt}: {count}')

# Correlation check
print('\n--- CORRELATION CHECK ---')

sql_cases = [tc for tc in ALL_TEST_CASES if tc.test_type.value == 'sql']
vector_cases = [tc for tc in ALL_TEST_CASES if tc.test_type.value == 'vector']
hybrid_cases = [tc for tc in ALL_TEST_CASES if tc.test_type.value == 'hybrid']

print(f'\nSQL test_type ({len(sql_cases)} cases):')
sql_qt = Counter(tc.query_type.value if tc.query_type else 'None' for tc in sql_cases)
for qt, count in sorted(sql_qt.items()):
    print(f'  query_type={qt}: {count}')

print(f'\nVECTOR test_type ({len(vector_cases)} cases):')
vec_qt = Counter(tc.query_type.value if tc.query_type else 'None' for tc in vector_cases)
for qt, count in sorted(vec_qt.items()):
    print(f'  query_type={qt}: {count}')

print(f'\nHYBRID test_type ({len(hybrid_cases)} cases):')
hyb_qt = Counter(tc.query_type.value if tc.query_type else 'None' for tc in hybrid_cases)
for qt, count in sorted(hyb_qt.items()):
    print(f'  query_type={qt}: {count}')

# Example cases
print('\n--- EXAMPLE CASES SHOWING REDUNDANCY ---')
sql_example = next((tc for tc in sql_cases if tc.query_type), None)
if sql_example:
    print(f'\nSQL Example:')
    print(f'  question: {sql_example.question[:60]}...')
    print(f'  test_type: {sql_example.test_type.value}')
    print(f'  query_type: {sql_example.query_type.value if sql_example.query_type else None}')
    print(f'  → REDUNDANT: test_type already tells us it\'s SQL')

vector_example = next((tc for tc in vector_cases if tc.query_type), None)
if vector_example:
    print(f'\nVECTOR Example:')
    print(f'  question: {vector_example.question[:60]}...')
    print(f'  test_type: {vector_example.test_type.value}')
    print(f'  query_type: {vector_example.query_type.value if vector_example.query_type else None}')
    print(f'  → REDUNDANT: test_type already tells us it\'s VECTOR')

hybrid_example = next((tc for tc in hybrid_cases if tc.query_type), None)
if hybrid_example:
    print(f'\nHYBRID Example:')
    print(f'  question: {hybrid_example.question[:60]}...')
    print(f'  test_type: {hybrid_example.test_type.value}')
    print(f'  query_type: {hybrid_example.query_type.value if hybrid_example.query_type else None}')
    print(f'  → REDUNDANT: test_type already tells us it\'s HYBRID')

print('\n' + '=' * 80)
print('OTHER FIELDS ANALYSIS')
print('=' * 80)

# Check min_similarity_score
min_sim_scores = [tc.min_similarity_score for tc in ALL_TEST_CASES if hasattr(tc, 'min_similarity_score') and tc.min_similarity_score != 0.5]
print(f'\nmin_similarity_score:')
print(f'  Non-default values (≠ 0.5): {len(min_sim_scores)}')
if min_sim_scores:
    print(f'  Values: {set(min_sim_scores)}')
    example = next((tc for tc in ALL_TEST_CASES if hasattr(tc, 'min_similarity_score') and tc.min_similarity_score != 0.5), None)
    if example:
        print(f'\n  Example with min_similarity_score={example.min_similarity_score}:')
        print(f'    question: {example.question[:60]}...')
        print(f'    ground_truth: {example.ground_truth[:100] if example.ground_truth else "None"}...')

# Check tags
has_tags = [tc for tc in ALL_TEST_CASES if hasattr(tc, 'tags') and tc.tags]
print(f'\ntags:')
print(f'  Test cases with tags: {len(has_tags)}')
if has_tags:
    print(f'  Example: {has_tags[0].question[:60]}')
    print(f'  Tags: {has_tags[0].tags}')

# Check difficulty
has_difficulty = [tc for tc in ALL_TEST_CASES if hasattr(tc, 'difficulty') and tc.difficulty != 'medium']
print(f'\ndifficulty:')
print(f'  Non-default values (≠ "medium"): {len(has_difficulty)}')
if has_difficulty:
    difficulty_dist = Counter(tc.difficulty for tc in has_difficulty)
    print(f'  Distribution: {dict(difficulty_dist)}')

# Check description
has_description = [tc for tc in ALL_TEST_CASES if hasattr(tc, 'description') and tc.description]
print(f'\ndescription:')
print(f'  Test cases with description: {len(has_description)}')
if has_description:
    print(f'  Example: {has_description[0].question[:60]}')
    print(f'  Description: {has_description[0].description[:100]}')

# Check notes
has_notes = [tc for tc in ALL_TEST_CASES if hasattr(tc, 'notes') and tc.notes]
print(f'\nnotes:')
print(f'  Test cases with notes: {len(has_notes)}')
if has_notes:
    print(f'  Example: {has_notes[0].question[:60]}')
    print(f'  Notes: {has_notes[0].notes[:100]}')

# Check ground_truth_answer
missing_answer = [tc for tc in ALL_TEST_CASES if not tc.ground_truth_answer]
print(f'\nground_truth_answer:')
print(f'  Test cases WITH answer: {len(ALL_TEST_CASES) - len(missing_answer)}')
print(f'  Test cases MISSING answer: {len(missing_answer)}')
if missing_answer:
    print(f'  Missing by type:')
    missing_by_type = Counter(tc.test_type.value for tc in missing_answer)
    for tt, count in sorted(missing_by_type.items()):
        print(f'    {tt}: {count}')

print('\n' + '=' * 80)
