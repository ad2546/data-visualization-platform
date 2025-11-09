# 3-Stage AI Pipeline Architecture

## Overview

The application now uses a sophisticated 3-stage pipeline for generating data visualizations:

```
Upload → Stage 0 (Business Context) → Stage 1 (Recommendations) → Stage 2 (Code Generation) → Dashboard
```

## Stage 0: Business Context Agent (Free LLM)

**Purpose**: Extract comprehensive business context and domain insights

**Model**: Uses free LLM (default: `google/gemini-flash-1.5`)

**What it does**:
- Analyzes dataset structure and content
- Detects business domain (sales, finance, marketing, HR, etc.)
- Identifies key business metrics and KPIs
- Generates business questions the data can answer
- Determines visualization focus and priorities
- Filters out technical columns (IDs, URLs, codes)
- Prioritizes business-relevant columns

**Output**: Comprehensive business context JSON with:
- Domain detection
- Key metrics
- Business questions
- Visualization focus
- Column filtering rules

**Why free LLM**: Business context analysis doesn't require the highest quality model, and using a free model reduces costs.

## Stage 1: Visualization Recommender

**Purpose**: Generate visualization recommendations based on business context

**Model**: Uses configured OpenRouter model (default: `anthropic/claude-3.5-sonnet`)

**What it does**:
- Takes business context from Stage 0
- Analyzes data with business focus
- Recommends 4-6 visualizations that answer business questions
- Prioritizes visualizations by business value
- Ensures recommendations align with business context

**Output**: JSON array of visualization recommendations with:
- Chart types
- Titles and descriptions
- Column mappings
- Priority levels

## Stage 2: Code Generator (qwen3-coder)

**Purpose**: Generate complete HTML dashboard code

**Model**: Uses `qwen/qwen2.5-coder-32b-instruct:free` (free coding model)

**What it does**:
- Takes recommendations from Stage 1
- Takes business context from Stage 0
- Generates complete, working HTML dashboard
- Creates Plotly.js visualizations
- Implements Power BI-inspired styling
- Embeds data in the HTML

**Output**: Complete HTML file with interactive dashboard

**Why qwen3-coder**: Specialized code generation model, free to use, produces clean code.

## Pipeline Flow

```
1. User uploads file
   ↓
2. Data loaded and validated
   ↓
3. Stage 0: Business Context Agent (free LLM)
   - Analyzes data
   - Extracts business context
   - Saves to business_context.json
   ↓
4. Stage 1: Visualization Recommender
   - Uses business context
   - Generates recommendations
   - Saves to recommendations.json
   ↓
5. Stage 2: Code Generator (qwen3-coder)
   - Uses recommendations + business context
   - Generates HTML dashboard
   - Saves to dashboard.html
   ↓
6. Dashboard ready for viewing
```

## Benefits

1. **Cost-Effective**: Uses free models where appropriate
2. **Better Context**: Business context improves all downstream stages
3. **Specialized Models**: Uses code-specific model for code generation
4. **Better Prompts**: Each stage has well-engineered prompts
5. **Modular**: Each stage can be improved independently

## Configuration

### Business Context Model (Stage 0)
Configured in `app/agents/business_context_agent.py`:
```python
free_model: str = "google/gemini-flash-1.5"
```

Other free options:
- `meta-llama/llama-3.2-3b-instruct:free`
- `qwen/qwen-2.5-7b-instruct:free`

### Recommendation Model (Stage 1)
Set in `.env`:
```
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

### Code Generation Model (Stage 2)
Configured in `app/agents/viz_generator.py`:
```python
self.code_model = "qwen/qwen2.5-coder-32b-instruct:free"
```

## API Endpoints

- `POST /api/v2/upload` - Start pipeline
- `GET /api/v2/status/{session_id}` - Check progress
- `GET /api/v2/business-context/{session_id}` - Get Stage 0 output
- `GET /api/v2/recommendations/{session_id}` - Get Stage 1 output
- `GET /api/v2/dashboard/{session_id}` - Get Stage 2 output (dashboard)

## Progress Tracking

The pipeline reports progress at each stage:
- 10%: Data loading
- 25%: Business context analysis (Stage 0)
- 50%: Visualization recommendations (Stage 1)
- 75%: Code generation (Stage 2)
- 100%: Complete

