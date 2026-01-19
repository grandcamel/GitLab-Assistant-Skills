# Skill Routing Decision Tree

## Primary Decision: What does the user want to do?

```
User Request
    │
    ├─ Mentions specific skill? ──────► Use that skill
    │
    ├─ Search/query/find? ────────────► gitlab-search
    │
    ├─ Single item CRUD? ─────────────► gitlab-resource
    │   ├─ Create
    │   ├─ Read/Get
    │   ├─ Update
    │   └─ Delete
    │
    ├─ Multiple items (10+)? ─────────► gitlab-bulk
    │   └─ "bulk", "batch", "all"
    │
    └─ Ambiguous? ────────────────────► Ask for clarification
```

## Keyword-Based Routing

| Keywords | Route to |
|----------|----------|
| search, find, query, list, filter | gitlab-search |
| create, new, add, make | gitlab-resource |
| get, show, view, display | gitlab-resource |
| update, edit, modify, change | gitlab-resource |
| delete, remove, destroy | gitlab-resource |
| bulk, batch, mass, multiple | gitlab-bulk |

## Context-Based Routing

| Context | Consideration |
|---------|---------------|
| Previous skill used | Continue with same skill if follow-up |
| Item ID mentioned | Route to resource skill |
| Count > 10 | Route to bulk skill |

## Disambiguation Questions

When unclear, ask:

- "How many items are you working with?"
- "Do you want to search or view a specific item?"
- "Should I use bulk operations for this?"
