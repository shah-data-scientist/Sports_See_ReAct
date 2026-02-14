# Development Rules for NBA RAG Assistant

## 🚨 CRITICAL RULES

### 1. **NEVER Use Archived Code in Production**
**Rule:** Code in the `archive/` directory must NEVER be imported or used in production code.

**Why:** Archived code is:
- Not maintained
- May have security vulnerabilities
- May conflict with current architecture
- Kept for historical reference only

**Enforcement:**
```python
# ❌ FORBIDDEN
from archive.query_classifier_legacy import QueryClassifier

# ❌ FORBIDDEN  
import sys
sys.path.append('archive/')

# ✅ CORRECT
# Only use code from src/, not archive/
from src.tools.sql_tool import NBAGSQLTool
```

**CI/CD Check:**
```bash
# Add to pre-commit hook or CI pipeline
if grep -r "from archive\." src/; then
    echo "ERROR: Production code imports from archive/"
    exit 1
fi
```

---

### 2. **LangChain Best Practices**
- Use official LangChain tools (create_sql_agent, VectorStoreRetriever)
- Follow ReAct pattern for agent-based routing
- Pre-load static schema to reduce LLM calls

### 3. **Database Schema is Static**
- Never call `sql_db_list_tables` or `sql_db_schema` dynamically
- Schema is pre-loaded in prompts
- Optimize for static data

### 4. **Security First**
- SQL injection validation on all queries
- Read-only database access
- No destructive operations (DROP, DELETE, UPDATE, etc.)

---

**Last Updated:** 2026-02-14  
**Status:** Active
