# Routing System

## Step 1: Identify Advisory Role

Query analysis to determine which advisory domain to use:

- **Crop related query** → Crop Advisory
- **Pest symptoms** → Pest Advisory
- **Soil issues** → Soil Advisory
- **Weather questions** → Weather Advisory
- **Livestock queries** → Livestock Advisory
- **Aquaculture questions** → Aquaculture Advisory
- **Irrigation needs** → Irrigation Advisory
- **Fertilizer questions** → Fertilizer Advisory
- **Disease symptoms** → Disease Advisory
- **Harvest/storage** → Post Harvest Advisory
- **Economics/profit** → Farm Economics Advisory
- **Horticulture** → Horticulture Advisory
- **Commercial scale** → Commercial Farming Advisory

## Step 2: Identify Crop Category

Extract crop name and determine category:

### Example Flow
```
Query: "My tomato leaves have yellow spots"

Routing:
1. Identify role: Disease symptoms → Disease Advisory
2. Extract crop: tomato → Vegetables category
3. Identify issue: yellow spots → leaf_disease
4. Execute skill: Disease Advisory → Vegetable Category → Tomato Advisory → Disease Detection
```

## Step 3: Execute Skill

Route to appropriate skill handler:

```
Skill → Tool → Response

Example:
Disease Advisory (skill)
  ↓
Tomato (crop)
  ↓
Leaf Disease Detection (tool)
  ↓
Generate response with fungicide recommendations
```

## Routing Rules

### Priority Order
1. Check for explicit crop mention
2. Identify primary advisory domain
3. Check conversation history for context
4. Apply fallback rules if needed

### Context Preservation
- Maintain crop context across conversation
- Remember previous queries in same session
- Use conversation history for ambiguous queries

### Fallback Strategy
- If online: Use LLM router for complex queries
- If offline: Use rule-based routing
- If no match: Use general advisory
