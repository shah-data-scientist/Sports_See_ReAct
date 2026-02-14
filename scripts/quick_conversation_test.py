"""Quick SQL conversation test."""
import requests
import json

API = "http://localhost:8000/api/v1"

print("="*80)
print("SQL CONVERSATION TEST: correction_celtics")
print("="*80)

# Create conversation
conv = requests.post(f"{API}/conversations", json={}).json()
conv_id = conv["id"]
print(f"\n✅ Conversation ID: {conv_id}\n")

# Query 1: Warriors
print("\n" + "─"*80)
print("QUERY 1: Show me stats for the Warriors")
print("─"*80)
r1 = requests.post(f"{API}/chat", json={
    "query": "Show me stats for the Warriors",
    "conversation_id": conv_id,
    "turn_number": 1,
    "k": 5,
    "include_sources": True
}).json()
print(f"\n📝 RESPONSE:\n{r1['response']}\n")
print(f"🔍 QUERY TYPE: {r1['query_type']}")
if r1.get('sql_data', {}).get('query_generated'):
    print(f"💾 SQL: {r1['sql_data']['query_generated']}")

# Query 2: Correction to Celtics
print("\n" + "─"*80)
print("QUERY 2: Actually, I meant the Celtics")
print("─"*80)
r2 = requests.post(f"{API}/chat", json={
    "query": "Actually, I meant the Celtics",
    "conversation_id": conv_id,
    "turn_number": 2,
    "k": 5,
    "include_sources": True
}).json()
print(f"\n📝 RESPONSE:\n{r2['response']}\n")
print(f"🔍 QUERY TYPE: {r2['query_type']}")
if r2.get('sql_data', {}).get('query_generated'):
    print(f"💾 SQL: {r2['sql_data']['query_generated']}")

# Query 3: Pronoun resolution
print("\n" + "─"*80)
print("QUERY 3: Who is their top scorer?")
print("─"*80)
r3 = requests.post(f"{API}/chat", json={
    "query": "Who is their top scorer?",
    "conversation_id": conv_id,
    "turn_number": 3,
    "k": 5,
    "include_sources": True
}).json()
print(f"\n📝 RESPONSE:\n{r3['response']}\n")
print(f"🔍 QUERY TYPE: {r3['query_type']}")
if r3.get('sql_data', {}).get('query_generated'):
    print(f"💾 SQL: {r3['sql_data']['query_generated']}")

print("\n" + "="*80)
print("✅ CONVERSATION COMPLETE")
print("="*80)
