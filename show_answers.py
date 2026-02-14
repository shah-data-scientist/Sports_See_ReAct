"""
Show complete answers from LangChain components for the 9 test cases.
"""

import time
from src.tools.sql_tool import NBAGSQLTool
from src.repositories.vector_store_langchain import create_nba_retriever
from src.services.embedding import EmbeddingService


def show_sql_answer(question: str, test_num: int):
    """Show complete SQL agent answer."""
    print(f"\n{'='*80}")
    print(f"SQL TEST {test_num}: {question}")
    print(f"{'='*80}")

    sql_tool = NBAGSQLTool()
    result = sql_tool.query(question)

    print(f"\n🤖 COMPLETE ANSWER FROM SQL AGENT:")
    print(result.get('answer', 'N/A'))

    print(f"\n📊 GENERATED SQL:")
    print(result.get('sql', 'N/A'))

    print(f"\n📋 RAW RESULTS:")
    print(result.get('results', []))


def show_vector_answer(question: str, test_num: int):
    """Show complete vector search results."""
    print(f"\n{'='*80}")
    print(f"VECTOR TEST {test_num}: {question}")
    print(f"{'='*80}")

    embedding_service = EmbeddingService()
    retriever = create_nba_retriever(
        embedding_function=embedding_service,
        search_kwargs={"k": 5}
    )

    docs = retriever.invoke(question)

    print(f"\n🤖 RETRIEVED DOCUMENTS ({len(docs)} total):")
    for i, doc in enumerate(docs, 1):
        print(f"\n--- Document {i} ---")
        print(f"Source: {doc.metadata.get('source', 'N/A')}")
        print(f"Score: {doc.metadata.get('score', 'N/A')}")
        print(f"Content: {doc.page_content[:300]}...")


def show_hybrid_answer(question: str, test_num: int):
    """Show complete hybrid (SQL + Vector) results."""
    print(f"\n{'='*80}")
    print(f"HYBRID TEST {test_num}: {question}")
    print(f"{'='*80}")

    # SQL Part
    print(f"\n📊 PART 1: SQL AGENT ANSWER")
    print("─" * 80)
    sql_tool = NBAGSQLTool()
    sql_result = sql_tool.query(question)

    print(f"\n🤖 SQL Answer:")
    print(sql_result.get('answer', 'N/A'))

    print(f"\n📋 SQL Results:")
    results = sql_result.get('results', [])
    for i, row in enumerate(results[:5], 1):  # Show first 5 rows
        print(f"  {i}. {row}")

    # Vector Part
    print(f"\n📚 PART 2: VECTOR SEARCH RESULTS")
    print("─" * 80)
    embedding_service = EmbeddingService()
    retriever = create_nba_retriever(
        embedding_function=embedding_service,
        search_kwargs={"k": 3}  # Just top 3 for hybrid
    )

    docs = retriever.invoke(question)

    print(f"\n🤖 Top {len(docs)} Context Documents:")
    for i, doc in enumerate(docs, 1):
        print(f"\n  Document {i} ({doc.metadata.get('source', 'N/A')}):")
        print(f"  {doc.page_content[:250]}...")


def main():
    """Show all answers."""
    print("\n" + "🎯" * 40)
    print("COMPLETE ANSWERS FROM LANGCHAIN COMPONENTS")
    print("Showing actual chatbot responses for all 9 test cases")
    print("🎯" * 40)

    # ========== SQL TESTS ==========
    print("\n\n" + "█" * 80)
    print("SQL TEST CASES - Direct answers from LangChain SQL Agent")
    print("█" * 80)

    show_sql_answer("Who scored the most points this season?", 1)
    show_sql_answer("Who are the top 3 rebounders in the league?", 2)
    show_sql_answer("What is LeBron James' average points per game?", 3)

    # ========== VECTOR TESTS ==========
    print("\n\n" + "█" * 80)
    print("VECTOR TEST CASES - Documents retrieved by LangChain Retriever")
    print("█" * 80)

    show_vector_answer("What do Reddit users think about teams that have impressed in the playoffs?", 1)
    show_vector_answer("According to fan discussions, which teams exceeded expectations in the playoffs?", 2)
    show_vector_answer("What are the most popular opinions about playoff basketball strategies?", 3)

    # ========== HYBRID TESTS ==========
    print("\n\n" + "█" * 80)
    print("HYBRID TEST CASES - Combined SQL + Vector results")
    print("█" * 80)

    show_hybrid_answer("Who scored the most points this season and what makes them an effective scorer?", 1)
    show_hybrid_answer("Compare LeBron James and Kevin Durant's scoring this season and explain their scoring styles.", 2)
    show_hybrid_answer("Who are the most efficient scorers by true shooting percentage and what makes them efficient?", 3)

    print("\n\n" + "🎯" * 40)
    print("END OF ANSWERS")
    print("🎯" * 40 + "\n")


if __name__ == "__main__":
    main()
