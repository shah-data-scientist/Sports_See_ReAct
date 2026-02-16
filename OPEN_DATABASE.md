# Quick Database Access

## Using SQLite Extension (alexcvzz)

### Open Database:
1. Press `Ctrl+Shift+P`
2. Type: `SQLite: Open Database`
3. Select: `data/sql/interactions.db`

### Full Path:
```
C:\Users\shahu\Documents\OneDrive\OPEN CLASSROOMS\PROJET 10\Sports_See_ReAct\data\sql\interactions.db
```

### Alternative - Use Python Script:
```bash
poetry run python scripts/explore_db.py
```

## Database Contents:
- **conversations** - 763 conversations
- **chat_interactions** - 965 messages
- **feedback** - 32 feedback entries

## Useful Queries:

### Get all conversations with message counts:
```sql
SELECT c.id, c.title, c.status, COUNT(ci.id) as messages
FROM conversations c
LEFT JOIN chat_interactions ci ON c.id = ci.conversation_id
GROUP BY c.id
ORDER BY c.updated_at DESC
LIMIT 20;
```

### Get feedback statistics:
```sql
SELECT rating, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM feedback), 2) as percentage
FROM feedback
GROUP BY rating;
```

### Get recent interactions with feedback:
```sql
SELECT
    ci.query,
    SUBSTR(ci.response, 1, 100) as response_preview,
    f.rating,
    f.comment,
    ci.created_at
FROM chat_interactions ci
LEFT JOIN feedback f ON ci.id = f.interaction_id
ORDER BY ci.created_at DESC
LIMIT 10;
```

### Find conversations with multiple turns:
```sql
SELECT
    conversation_id,
    COUNT(*) as turn_count,
    MIN(created_at) as started_at,
    MAX(created_at) as last_message_at
FROM chat_interactions
GROUP BY conversation_id
HAVING COUNT(*) > 1
ORDER BY turn_count DESC
LIMIT 10;
```
