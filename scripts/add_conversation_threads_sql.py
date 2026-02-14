"""
Add conversation_thread field to SQL test cases.

This script adds conversation_thread IDs to the 5 conversational threads in SQL test cases:
1. Progressive Filtering (3 queries) - lines 732-792
2. User Correction (3 queries) - lines 795-840
3. Implicit Category Continuation (3 queries) - lines 842-879
4. Multi-Entity Tracking (3 queries) - lines 881-924
5. Team-Level Pronoun Resolution (3 queries) - lines 926-966
"""
from pathlib import Path
import re

# Read the test cases file
test_cases_path = Path("src/evaluation/test_cases/sql_test_cases.py")
content = test_cases_path.read_text(encoding="utf-8")

# Define replacements for each thread
# Thread 1: Progressive Filtering (3 queries at lines 733-792)
replacements = [
    # Progressive Filtering - Query 1
    (
        r'(# --- Thread: Progressive Filtering.*?\n.*?question="Show me players with good three-point shooting",.*?category="conversational_progressive_filtering",)',
        r'\1\n        conversation_thread="progressive_filtering_1",'
    ),
    # Progressive Filtering - Query 2
    (
        r'(question="Only from the Lakers",.*?category="conversational_progressive_filtering",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="progressive_filtering_1",'
    ),
    # Progressive Filtering - Query 3
    (
        r'(question="Sort them by attempts",.*?category="conversational_progressive_filtering",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="progressive_filtering_1",'
    ),

    # User Correction - Query 1
    (
        r'(# --- Thread: User Correction.*?\n.*?question="Show me stats for the Warriors",.*?category="conversational_correction",)',
        r'\1\n        conversation_thread="correction_celtics",'
    ),
    # User Correction - Query 2
    (
        r'(question="Actually, I meant the Celtics",.*?category="conversational_correction",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="correction_celtics",'
    ),
    # User Correction - Query 3
    (
        r'(question="Who is their top scorer\?",.*?category="conversational_correction",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="correction_celtics",'
    ),

    # Implicit Continuation - Query 1
    (
        r'(# --- Thread: Implicit Category Continuation.*?\n.*?question="Who leads the league in steals\?",.*?category="conversational_implicit_continuation",)',
        r'\1\n        conversation_thread="stats_continuation",'
    ),
    # Implicit Continuation - Query 2
    (
        r'(question="And blocks\?",.*?category="conversational_implicit_continuation",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="stats_continuation",'
    ),
    # Implicit Continuation - Query 3
    (
        r'(question="What about turnovers\?",.*?category="conversational_implicit_continuation",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="stats_continuation",'
    ),

    # Multi-Entity Tracking - Query 1
    (
        r'(# --- Thread: Multi-Entity Tracking.*?\n.*?question="Tell me about Jayson Tatum\'s scoring",.*?category="conversational_multi_entity",)',
        r'\1\n        conversation_thread="multi_entity_tatum_lebron",'
    ),
    # Multi-Entity Tracking - Query 2
    (
        r'(question="How does his scoring compare to LeBron James\?",.*?category="conversational_multi_entity",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="multi_entity_tatum_lebron",'
    ),
    # Multi-Entity Tracking - Query 3
    (
        r'(question="Who has more rebounds between the two\?",.*?category="conversational_multi_entity",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="multi_entity_tatum_lebron",'
    ),

    # Team Pronoun Resolution - Query 1
    (
        r'(# --- Thread: Team-Level Pronoun Resolution.*?\n.*?question="Which team has the highest total points\?",.*?category="conversational_team_pronoun",)',
        r'\1\n        conversation_thread="team_pronoun_pistons",'
    ),
    # Team Pronoun Resolution - Query 2
    (
        r'(question="Who are their top scorers\?",.*?category="conversational_team_pronoun",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="team_pronoun_pistons",'
    ),
    # Team Pronoun Resolution - Query 3
    (
        r'(question="What is the average age of their players\?",.*?category="conversational_team_pronoun",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="team_pronoun_pistons",'
    ),
]

# Apply replacements
modified_content = content
for pattern, replacement in replacements:
    modified_content = re.sub(pattern, replacement, modified_content, flags=re.DOTALL)

# Write back
test_cases_path.write_text(modified_content, encoding="utf-8")
print(f"✅ Updated SQL test cases with conversation_thread IDs")
print(f"📄 File: {test_cases_path}")
print(f"\nAdded thread IDs:")
print("  1. progressive_filtering_1 (3 queries)")
print("  2. correction_celtics (3 queries)")
print("  3. stats_continuation (3 queries)")
print("  4. multi_entity_tatum_lebron (3 queries)")
print("  5. team_pronoun_pistons (3 queries)")
print(f"\nTotal: 15 conversational queries marked")
