# M3: Prompt Registry System

## Overview

The Prompt Registry treats prompts as **first-class code assets** with:
- **Semantic versioning** (v1.0.0, v1.1.0, v2.0.0)
- **A/B testing capability** 
- **Performance tracking**
- **Automatic rollback** on quality degradation
- **Contract validation** for tool integrations

## Structure

```
prompts/registry/
├── persona_runtime/
│   ├── content_generation/
│   │   ├── v1.0.0.yaml
│   │   ├── v1.1.0.yaml  
│   │   └── v2.0.0.yaml
│   └── hook_optimization/
│       ├── v1.0.0.yaml
│       └── v1.1.0.yaml
├── viral_engine/
│   ├── engagement_prediction/
│   └── viral_scoring/
└── orchestrator/
    ├── task_routing/
    └── error_handling/
```

## Prompt Format

Each prompt version is a YAML file with metadata:

```yaml
# prompts/registry/persona_runtime/content_generation/v1.2.0.yaml
metadata:
  name: "content_generation"
  version: "1.2.0"
  agent: "persona_runtime"
  created: "2025-08-19"
  author: "vitalii"
  description: "Generates viral content with engagement optimization"
  
prompt:
  system: |
    You are an expert content creator specializing in viral social media posts.
    Your goal is to create engaging, authentic content that drives meaningful engagement.
    
  user_template: |
    Create a viral post about: {topic}
    Target audience: {audience}
    Tone: {tone}
    
    Requirements:
    - Hook that creates curiosity gap
    - Personal story or insight
    - Clear value proposition
    - Call to action
    
performance:
  target_engagement_score: 0.75
  max_tokens: 200
  estimated_cost: 0.02
  
validation:
  required_variables: ["topic", "audience", "tone"]
  output_requirements:
    - "has_hook"
    - "has_cta"
    - "length_150_280"
    
test_cases:
  - input:
      topic: "AI productivity tools"
      audience: "software_engineers"
      tone: "informative"
    expected:
      engagement_score: 0.75
      contains: ["AI", "productivity"]
```