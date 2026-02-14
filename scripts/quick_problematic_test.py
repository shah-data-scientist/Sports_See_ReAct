"""Quick test of 10 problematic queries with detailed reporting."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from starlette.testclient import TestClient
from src.api.main import create_app
from src.api.dependencies import set_chat_service
from src.services.chat import ChatService


QUERIES = [
    {"query": "Who is more efficient goal maker, Jokić or Embiid?", "issue": "Routing fallback (comparison)"},
    {"query": "How many players have more than 500 assists?", "issue": "LLM decline + JOIN bug"},
    {"query": "How many players played more than 50 games?", "issue": "Routing fallback + JOIN bug"},
    {"query": "Which teams have at least 3 players with more than 1000 points?", "issue": "LLM decline"},
    {"query": "Tell me about LeBron's stats", "issue": "Should be biographical HYBRID"},
    {"query": "What about his assists?", "issue": "Conversational context"},
    {"query": "Who is the MVP this season?", "issue": "Ambiguous query"},
    {"query": "Who is their top scorer?", "issue": "Conversational pronoun"},
    {"query": "Tell me about Jayson Tatum's scoring", "issue": "Should be biographical HYBRID"},
    {"query": "jokic rebounds total plzz", "issue": "Special char + informal"},
]


def main():
    print("\n" + "="*80)
    print("PROBLEMATIC QUERIES - FOCUSED TEST REPORT")
    print("="*80)

    # Initialize
    service = ChatService()
    set_chat_service(service)
    try:
        service.ensure_ready()
    except:
        pass

    app = create_app()
    client = TestClient(app)

    results = []
    for i, test in enumerate(QUERIES, 1):
        query = test["query"]
        issue = test["issue"]

        print(f"\n[{i}/10] {query}")
        print(f"  Issue: {issue}")

        try:
            resp = client.post("/api/v1/chat", json={"query": query, "include_sources": False})
            resp.raise_for_status()
            data = resp.json()

            answer = data.get("answer", "")
            query_type = data.get("query_type", "unknown")
            sql = data.get("generated_sql")
            time_ms = data.get("processing_time_ms", 0)

            # Analysis
            has_decline = any(p in answer.lower() for p in ["i can't", "i cannot", "unable to"])
            has_hedging = any(p in answer.lower() for p in ["appears to", "seems to", "approximately", "i think"])
            sql_worked = sql is not None and query_type in ["statistical", "hybrid"]

            status = "✅" if sql_worked and not has_decline else "⚠️" if sql_worked else "❌"

            print(f"  {status} Type: {query_type} | SQL: {'Yes' if sql else 'No'} | Time: {time_ms:.0f}ms")
            print(f"  Decline: {'❌' if has_decline else '✅'} | Hedging: {'❌' if has_hedging else '✅'}")
            print(f"  Answer: {answer[:120]}...")

            results.append({
                "success": True,
                "sql_worked": sql_worked,
                "has_decline": has_decline,
                "has_hedging": has_hedging,
            })

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)[:80]}")
            results.append({"success": False, "sql_worked": False, "has_decline": True, "has_hedging": False})

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    success = sum(1 for r in results if r["success"])
    sql_ok = sum(1 for r in results if r["sql_worked"])
    no_decline = sum(1 for r in results if not r["has_decline"])
    no_hedge = sum(1 for r in results if not r["has_hedging"])

    print(f"\n✓ Successful: {success}/10 ({success*10}%)")
    print(f"✓ SQL Working: {sql_ok}/10 ({sql_ok*10}%)")
    print(f"✓ No Declines: {no_decline}/10 ({no_decline*10}%)")
    print(f"✓ No Hedging: {no_hedge}/10 ({no_hedge*10}%)")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
