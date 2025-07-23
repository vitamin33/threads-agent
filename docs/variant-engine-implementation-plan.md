# Variant Generation Engine - Implementation Plan

## Current State Analysis

### Existing Architecture
```
services/viral_engine/
├── hook_optimizer.py      # Core engine (ViralHookEngine)
├── patterns/              # JSON pattern files
│   ├── story_hooks.json   # Narrative patterns (8.3% avg ER)
│   ├── curiosity_gap.json # Information loops (9.1% avg ER)
│   ├── controversy.json   # Controversial statements
│   ├── emotion_triggers.json
│   ├── pattern_interrupt.json
│   └── social_proof.json
└── main.py               # FastAPI service endpoints
```

### Key Findings
1. **Pattern Structure**: Templates with variables like `{past_action}`, `{unexpected_outcome}`
2. **Variant Generation**: Already exists but limited to pattern selection
3. **Template Filling**: Basic string replacement (noted as "can be enhanced with AI")
4. **No Learning Loop**: Pattern performance not tracked or improved
5. **Missing Features**: No emotion variations, length variations, or style adaptations

## Enhancement Plan (Aligned with Current Code)

### 1. Extend Pattern Library (services/viral_engine/patterns/)
**New pattern files to add:**
```
patterns/
├── question_hooks.json     # Questions that demand answers
├── number_hooks.json       # Statistics and listicles
├── how_to_hooks.json      # Educational promises
├── mistake_hooks.json     # Common mistakes/warnings
└── announcement_hooks.json # Breaking news style
```

**Pattern template structure (maintain compatibility):**
```json
{
  "category": "question_hooks",
  "avg_engagement_rate": 0.087,
  "patterns": [
    {
      "id": "question_001",
      "template": "Why do {group} always {action}? The answer might surprise you:",
      "variables": ["group", "action"],
      "avg_er": 0.091,
      "examples": [...]
    }
  ]
}
```

### 2. Enhance ViralHookEngine Class

#### A. Add Emotion Variation System
```python
# Add to hook_optimizer.py
class ViralHookEngine:
    def __init__(self):
        # ... existing code ...
        
        # NEW: Emotion modifiers
        self.emotion_modifiers = {
            "curiosity": {
                "prefix": ["Ever wondered", "Did you know", "The truth about"],
                "suffix": ["...and what happened next", "...the answer will shock you"]
            },
            "urgency": {
                "prefix": ["Breaking:", "Just in:", "Alert:"],
                "suffix": ["...before it's too late", "...act now"]
            },
            "inspiration": {
                "prefix": ["How I", "The day I", "When I finally"],
                "suffix": ["...changed everything", "...and you can too"]
            },
            "fear": {
                "prefix": ["Warning:", "The hidden danger of", "Why you should stop"],
                "suffix": ["...before it's too late", "...could cost you"]
            }
        }
```

#### B. Improve Pattern Selection
```python
def _select_optimal_patterns(self, persona_id, topic_category, variant_count):
    """Enhanced to select diverse patterns for A/B testing"""
    # Current: Returns multiple patterns
    # Enhancement: Ensure pattern diversity
    
    selected_patterns = []
    used_categories = set()
    
    # Get persona preferences
    preferences = self.persona_preferences.get(persona_id, {})
    preferred_categories = preferences.get("preferred_categories", [])
    
    # First, select from preferred categories
    for category in preferred_categories:
        if category not in used_categories and len(selected_patterns) < variant_count:
            patterns = self.patterns.get(category, {}).get("patterns", [])
            if patterns:
                # Select best performing pattern from category
                best_pattern = max(patterns, key=lambda p: p.get("avg_er", 0))
                selected_patterns.append((category, best_pattern))
                used_categories.add(category)
    
    # Fill remaining slots with other high-performing patterns
    # ... existing logic enhanced ...
    
    return selected_patterns[:variant_count]
```

#### C. AI-Enhanced Template Filling
```python
def _fill_pattern_template_ai(self, pattern, base_content, persona_id):
    """Use GPT to intelligently fill pattern templates"""
    # Extract key concepts from base_content
    # Generate contextually appropriate variable values
    # Maintain persona voice
    
    prompt = f"""
    Base content: {base_content}
    Pattern template: {pattern['template']}
    Variables needed: {pattern['variables']}
    Persona: {persona_id}
    
    Generate variable values that:
    1. Are relevant to the base content
    2. Match the {self.persona_preferences[persona_id]['tone']} tone
    3. Create maximum curiosity/engagement
    
    Return as JSON: {{"variable_name": "value", ...}}
    """
    
    # Call OpenAI API (using existing wrapper)
    # Fill template with AI-generated values
    # Return enhanced hook
```

### 3. Add Variant Tracking Database Schema

```sql
-- New migration: add_variant_tracking.py
CREATE TABLE hook_variants (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT REFERENCES posts(id),
    variant_id VARCHAR(50) UNIQUE,
    pattern_id VARCHAR(50),
    pattern_category VARCHAR(50),
    emotion_modifier VARCHAR(50),
    hook_content TEXT,
    expected_engagement_rate FLOAT,
    actual_engagement_rate FLOAT,
    impressions INT DEFAULT 0,
    engagements INT DEFAULT 0,
    selected_for_posting BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_variants_performance ON hook_variants(actual_engagement_rate DESC);
CREATE INDEX idx_variants_pattern ON hook_variants(pattern_id);
```

### 4. Enhance Batch Generation API

```python
# In services/orchestrator/main.py
@app.post("/variants/generate-batch")
async def generate_batch_variants(request: BatchVariantRequest):
    """Generate variants for multiple topics in one call"""
    
    results = []
    for topic in request.topics:
        # Call viral engine for each topic
        variants = await viral_engine.generate_variants(
            persona_id=request.persona_id,
            base_content=topic.content,
            topic_category=topic.category,
            variant_count=request.variants_per_topic
        )
        
        # Store variants in database
        for variant in variants:
            db_variant = HookVariant(
                variant_id=variant['variant_id'],
                pattern_id=variant['pattern'],
                pattern_category=variant['pattern_category'],
                hook_content=variant['content'],
                expected_engagement_rate=variant['expected_engagement_rate']
            )
            db.session.add(db_variant)
        
        results.append({
            "topic": topic.content,
            "variants": variants
        })
    
    db.session.commit()
    return {"batch_id": str(uuid4()), "results": results}
```

### 5. Learning Loop Enhancement

```python
# New method in ViralHookEngine
def update_pattern_performance(self, pattern_id: str, actual_engagement_rate: float):
    """Update pattern performance based on real results"""
    
    # Track in pattern_performance dict
    if pattern_id not in self.pattern_performance:
        self.pattern_performance[pattern_id] = {
            "uses": 0,
            "total_engagement": 0,
            "avg_engagement": 0
        }
    
    perf = self.pattern_performance[pattern_id]
    perf["uses"] += 1
    perf["total_engagement"] += actual_engagement_rate
    perf["avg_engagement"] = perf["total_engagement"] / perf["uses"]
    
    # Persist to database for long-term learning
    # Adjust pattern selection weights based on performance
```

## Implementation Steps

### Phase 1: Extend Pattern Library (4 hours)
1. Create 5 new pattern JSON files
2. Add 10+ templates per category
3. Include high-performing examples
4. Set initial engagement rates

### Phase 2: Enhance Engine (8 hours)
1. Add emotion modifier system
2. Implement diverse pattern selection
3. Add AI-enhanced template filling
4. Create length variation logic

### Phase 3: Database & Tracking (4 hours)
1. Create variant tracking migration
2. Add variant storage logic
3. Implement performance tracking
4. Build learning loop

### Phase 4: API Enhancement (6 hours)
1. Create batch generation endpoint
2. Add variant management endpoints
3. Build performance reporting API
4. Add A/B test setup endpoint

## Success Metrics
- Generate 100+ unique variants per week
- Achieve 20% of variants with >6% engagement
- Reduce time to identify winners by 50%
- Improve average engagement rate by 2% within 2 weeks

## Risk Mitigation
- Maintain backward compatibility with existing code
- Add feature flags for new functionality
- Implement gradual rollout
- Monitor performance impact