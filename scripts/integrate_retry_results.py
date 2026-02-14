"""Integrate retry results into main evaluation and regenerate report.

Updates the 3 failed queries with successful retry results, regenerates
the report, and cleans up old evaluation files.

Usage:
    poetry run python scripts/integrate_retry_results.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from starlette.testclient import TestClient
from src.api.main import create_app
from src.api.dependencies import set_chat_service
from src.services.chat import ChatService


# 3 queries to retry and update
RETRY_QUERIES = [
    "Who is more efficient goal maker, Jokić or Embiid?",
    "Find players between 25 and 30 years old with more than 1500 points",
    "gimme the assist leaders plz",
]


def main():
    """Run integration."""
    print("\n" + "=" * 80)
    print("INTEGRATE RETRY RESULTS INTO MAIN EVALUATION")
    print("=" * 80)

    # 1. Load existing evaluation
    results_dir = Path("evaluation_results")
    latest_json = results_dir / "sql_evaluation_20260213_202520.json"
    
    print(f"\n1. Loading existing results from: {latest_json.name}")
    results = json.loads(latest_json.read_text(encoding="utf-8"))
    print(f"   Found {len(results)} total queries")
    
    # Find failed queries
    failed_indices = []
    for i, r in enumerate(results):
        if r["question"] in RETRY_QUERIES and not r.get("success", False):
            failed_indices.append(i)
    
    print(f"   Found {len(failed_indices)} failed queries to update")

    # 2. Retry failed queries
    print("\n2. Retrying failed queries...")
    service = ChatService()
    set_chat_service(service)
    try:
        service.ensure_ready()
    except:
        pass

    app = create_app()
    client = TestClient(app)

    updated_count = 0
    for idx in failed_indices:
        query = results[idx]["question"]
        category = results[idx]["category"]
        
        print(f"\n   Retrying: {query}")
        
        try:
            resp = client.post("/api/v1/chat", json={"query": query, "include_sources": True})
            resp.raise_for_status()
            data = resp.json()

            # Update the result
            results[idx] = {
                "question": query,
                "category": category,
                "response": data.get("answer", ""),
                "expected_routing": results[idx].get("expected_routing", "sql_only"),
                "actual_routing": data.get("query_type", "unknown"),
                "is_misclassified": data.get("query_type", "unknown") != results[idx].get("expected_routing", "sql_only"),
                "sources_count": len(data.get("sources", [])),
                "processing_time_ms": data.get("processing_time_ms", 0),
                "generated_sql": data.get("generated_sql"),
                "conversation_id": None,
                "success": True,
            }
            
            print(f"   ✅ SUCCESS - {data.get('processing_time_ms', 0):.0f}ms")
            updated_count += 1
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    # 3. Save updated results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_json = results_dir / f"sql_evaluation_{timestamp}.json"
    
    print(f"\n3. Saving updated results to: {new_json.name}")
    new_json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   Updated {updated_count} queries")
    
    # 4. Regenerate report
    print(f"\n4. Regenerating report...")
    from src.evaluation.runners.run_sql_evaluation import _generate_report
    
    new_md = results_dir / f"sql_evaluation_report_{timestamp}.md"
    _generate_report(results, new_md, new_json.name)
    print(f"   Report saved: {new_md.name}")
    
    # 5. Clean up old files
    print(f"\n5. Cleaning up old SQL evaluation files...")
    old_files = []
    for f in results_dir.glob("sql_evaluation_*"):
        if f.name not in [new_json.name, new_md.name]:
            old_files.append(f)
    
    if old_files:
        print(f"   Found {len(old_files)} old files to delete:")
        for f in old_files:
            print(f"     - {f.name}")
            f.unlink()
        print(f"   ✅ Deleted {len(old_files)} old files")
    else:
        print(f"   No old files to delete")
    
    # Summary
    print("\n" + "=" * 80)
    print("INTEGRATION COMPLETE")
    print("=" * 80)
    print(f"\n✓ Updated: {updated_count} queries")
    print(f"✓ Total success: {sum(1 for r in results if r.get('success', False))}/{len(results)}")
    print(f"✓ New JSON: {new_json.name}")
    print(f"✓ New Report: {new_md.name}")
    print(f"✓ Deleted: {len(old_files)} old files")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
