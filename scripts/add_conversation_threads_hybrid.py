"""
Add conversation_thread field to Hybrid test cases.

2 conversational threads (6 queries):
1. MVP Discussion (3 queries) - lines 515-547
2. Team Deep Dive (3 queries) - lines 550-588
"""
from pathlib import Path
import re

# Read the test cases file
test_cases_path = Path("src/evaluation/test_cases/hybrid_test_cases.py")
content = test_cases_path.read_text(encoding="utf-8")

# Define replacements for each thread
replacements = [
    # Thread 1: MVP Discussion - Query 1
    (
        r'(# --- Thread: MVP Discussion.*?\n.*?question="What are Shai Gilgeous-Alexander\'s full stats this season\?",.*?category="hybrid_conversational_mvp",)',
        r'\1\n        conversation_thread="mvp_sga_discussion",',
    ),
    # Thread 1: MVP Discussion - Query 2
    (
        r'(question="Why do fans on Reddit consider him an MVP favorite\?",.*?category="hybrid_conversational_mvp",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="mvp_sga_discussion",',
    ),
    # Thread 1: MVP Discussion - Query 3
    (
        r'(question="How does his efficiency compare to the historical playoff scorers that fans debate about\?",.*?category="hybrid_conversational_mvp",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="mvp_sga_discussion",',
    ),

    # Thread 2: Team Deep Dive - Query 1
    (
        r'(# --- Thread: Team Deep Dive.*?\n.*?question="Show me the Celtics\' team statistics this season",.*?category="hybrid_conversational_team",)',
        r'\1\n        conversation_thread="team_celtics_deepdive",',
    ),
    # Thread 2: Team Deep Dive - Query 2
    (
        r'(question="What do fans think about their chances of repeating as champions\?",.*?category="hybrid_conversational_team",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="team_celtics_deepdive",',
    ),
    # Thread 2: Team Deep Dive - Query 3
    (
        r'(question="Compare their stats to the Nuggets — which team is statistically better\?",.*?category="hybrid_conversational_team",)(?!\n        conversation_thread)',
        r'\1\n        conversation_thread="team_celtics_deepdive",',
    ),
]

# Apply replacements
modified_content = content
for pattern, replacement in replacements:
    modified_content = re.sub(pattern, replacement, modified_content, flags=re.DOTALL)

# Write back
test_cases_path.write_text(modified_content, encoding="utf-8")
print(f"✅ Updated Hybrid test cases with conversation_thread IDs")
print(f"📄 File: {test_cases_path}")
print(f"\nAdded thread IDs:")
print("  1. mvp_sga_discussion (3 queries)")
print("  2. team_celtics_deepdive (3 queries)")
print(f"\nTotal: 6 conversational queries marked")
