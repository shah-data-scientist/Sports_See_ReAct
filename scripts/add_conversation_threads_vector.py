"""
Add conversation_thread field to Vector test cases.

4 conversational threads (12 queries):
1. Lakers (3 queries) - lines 489-516
2. Playoff teams (3 queries) - lines 519-547
3. Efficiency discussion (3 queries) - lines 550-577
4. Topic switching (3 queries) - lines 580-608
"""
from pathlib import Path
import re

# Read the test cases file
test_cases_path = Path("src/evaluation/test_cases/vector_test_cases.py")
content = test_cases_path.read_text(encoding="utf-8")

# Define replacements for each thread
replacements = [
    # Thread 1: Lakers - Query 1
    (
        r'(# Conversation Thread 1: Lakers\s+EvaluationTestCase\(\s+question="What do fans say about the Lakers\?",.*?category=TestCategory\.CONVERSATIONAL,)',
        r'\1\n        conversation_thread="lakers_discussion",'
    ),
    # Thread 1: Lakers - Query 2
    (
        r'(question="What are their biggest strengths\?",.*?category=TestCategory\.CONVERSATIONAL,)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="lakers_discussion",'
    ),
    # Thread 1: Lakers - Query 3
    (
        r'(question="And their weaknesses\?",.*?category=TestCategory\.CONVERSATIONAL,)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="lakers_discussion",'
    ),

    # Thread 2: Playoff teams - Query 1
    (
        r'(# Conversation Thread 2: Playoff teams\s+EvaluationTestCase\(\s+question="Tell me about playoff teams that surprised people\.",.*?category=TestCategory\.CONVERSATIONAL,)',
        r'\1\n        conversation_thread="playoff_surprises",'
    ),
    # Thread 2: Playoff teams - Query 2
    (
        r'(question="Why were they surprising\?",.*?category=TestCategory\.CONVERSATIONAL,)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="playoff_surprises",'
    ),
    # Thread 2: Playoff teams - Query 3
    (
        r'(question="Compare them to the top-seeded teams\.",.*?category=TestCategory\.CONVERSATIONAL,)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="playoff_surprises",'
    ),

    # Thread 3: Efficiency - Query 1
    (
        r'(# Conversation Thread 3: Efficiency discussion\s+EvaluationTestCase\(\s+question="What makes a player efficient in the playoffs\?",.*?category=TestCategory\.CONVERSATIONAL,)',
        r'\1\n        conversation_thread="efficiency_metrics",'
    ),
    # Thread 3: Efficiency - Query 2
    (
        r'(question="Who is the most efficient according to fans\?",.*?category=TestCategory\.CONVERSATIONAL,)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="efficiency_metrics",'
    ),
    # Thread 3: Efficiency - Query 3
    (
        r'(question="What do people debate about his efficiency\?",.*?category=TestCategory\.CONVERSATIONAL,)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="efficiency_metrics",'
    ),

    # Thread 4: Topic switching - Query 1
    (
        r'(# Conversation Thread 4: Topic switching\s+EvaluationTestCase\(\s+question="Tell me about home court advantage in playoffs\.",.*?category=TestCategory\.CONVERSATIONAL,)',
        r'\1\n        conversation_thread="topic_switching",'
    ),
    # Thread 4: Topic switching - Query 2
    (
        r'(question="Going back to efficiency, who else is considered efficient\?",.*?category=TestCategory\.CONVERSATIONAL,)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="topic_switching",'
    ),
    # Thread 4: Topic switching - Query 3
    (
        r'(question="Returning to home court, which teams historically lacked it\?",.*?category=TestCategory\.CONVERSATIONAL,)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="topic_switching",'
    ),
]

# Apply replacements
modified_content = content
for pattern, replacement in replacements:
    modified_content = re.sub(pattern, replacement, modified_content, flags=re.DOTALL)

# Write back
test_cases_path.write_text(modified_content, encoding="utf-8")
print(f"✅ Updated Vector test cases with conversation_thread IDs")
print(f"📄 File: {test_cases_path}")
print(f"\nAdded thread IDs:")
print("  1. lakers_discussion (3 queries)")
print("  2. playoff_surprises (3 queries)")
print("  3. efficiency_metrics (3 queries)")
print("  4. topic_switching (3 queries)")
print(f"\nTotal: 12 conversational queries marked")
