# Prompt Optimization Guide

## Overview

This document explains the comprehensive prompt optimization system designed to get high-quality chart trace configurations from free LLM models.

## Problem

Free LLM models often produce inconsistent output:
- ❌ Include markdown formatting (```javascript)
- ❌ Add explanations and comments
- ❌ Generate full functions instead of just objects
- ❌ Misunderstand chart types
- ❌ Use wrong syntax or property names

## Solution

A three-part optimization strategy:

### 1. **Comprehensive Prompts**
### 2. **Response Cleaning**
### 3. **Validation**

---

## 1. Comprehensive Prompts

### Structure

```
┌─────────────────────────────────────┐
│ TASK DESCRIPTION                    │
│ - Clear goal                        │
│ - What to generate                  │
│ - What NOT to include               │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ CHART DETAILS                       │
│ - Type, title, description          │
│ - X/Y columns                       │
│ - Color scheme                      │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ DATASET INFORMATION                 │
│ - Row count                         │
│ - Column list                       │
│ - Sample data (5 rows)              │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ INSTRUCTIONS                        │
│ 1. Numbered steps                   │
│ 2. Clear requirements               │
│ 3. Syntax rules                     │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ CHART-SPECIFIC REQUIREMENTS         │
│ - Instructions per chart type       │
│ - Examples for that specific type   │
│ - Common pitfalls to avoid          │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ EXAMPLE OUTPUT                      │
│ - Concrete example                  │
│ - With actual column names          │
│ - Shows exact format expected       │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ IMPORTANT REMINDERS                 │
│ - Repeat key constraints            │
│ - Emphasize format                  │
│ - Final call to action              │
└─────────────────────────────────────┘
```

### Key Components

#### Task Description
```
You are generating a Plotly.js trace configuration for a data visualization dashboard.

TASK: Create a JavaScript trace object for Plotly.js (NOT a full chart, just the trace config).
```

**Why**: Sets clear expectations upfront

#### Chart Details
```
CHART DETAILS:
- Type: bar
- Title: Sales by Region
- Description: Compare sales performance across regions
- X-axis column: region
- Y-axis column: sales
- Color: #118DFF
```

**Why**: Provides all context the model needs

#### Dataset Information
```
DATASET INFORMATION:
- Total rows: 1,000
- Available columns: region, sales, profit, quarter
- Data is accessible as JavaScript array: 'data'

SAMPLE DATA (first 5 rows):
[
  {"region": "North", "sales": 10000, "profit": 2000},
  {"region": "South", "sales": 15000, "profit": 3000},
  ...
]
```

**Why**: Shows actual data structure and column names

#### Chart-Specific Instructions

**For Bar Charts**:
```
For BAR charts:
- Use x: data.map(d => d.region) for categories
- Use y: data.map(d => d.sales) for values
- Set type: 'bar'
- Include marker color

Example:
{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar',
    marker: { color: '#118DFF' }
}
```

**For Scatter Plots**:
```
For SCATTER plots:
- Use x: data.map(d => d.sales)
- Use y: data.map(d => d.profit)
- Set type: 'scatter'
- Set mode: 'markers'

Example:
{
    x: data.map(d => d.sales),
    y: data.map(d => d.profit),
    type: 'scatter',
    mode: 'markers',
    marker: { color: '#118DFF', size: 8 }
}
```

**For Pie Charts**:
```
For PIE charts:
- Use labels: data.map(d => d.region)
- Use values: data.map(d => d.sales)
- Set type: 'pie'
- NO x or y properties

Example:
{
    labels: data.map(d => d.region),
    values: data.map(d => d.sales),
    type: 'pie'
}
```

**Why**: Each chart type has different requirements. Specific examples prevent confusion.

#### Example Output
```
EXAMPLE OUTPUT FORMAT:
{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar',
    mode: 'markers',
    marker: {
        color: '#118DFF',
        size: 8
    },
    name: 'Sales by Region'
}
```

**Why**: Shows exact format with proper JavaScript syntax

#### Important Reminders
```
IMPORTANT:
- Return ONLY the JavaScript object
- No explanations, no code blocks, no markdown
- Just the raw object starting with { and ending with }
- Use proper JavaScript syntax
- Access data columns like: data.map(d => d.column_name)

Generate the trace configuration now:
```

**Why**: Final emphasis on constraints helps models follow instructions

---

## 2. Response Cleaning

### Cleaning Pipeline

```python
def _clean_llm_response(response: str) -> str:
    """Clean LLM response to extract just the trace config"""

    # 1. Remove markdown code blocks
    if response.startswith('```'):
        # Remove ```javascript, ```js, or ```
        # Remove closing ```

    # 2. Remove common prefixes
    prefixes = [
        'Here is the trace configuration:',
        'Here is the JavaScript object:',
        'Sure, here is',
        ...
    ]

    # 3. Remove trailing explanations
    suffixes = [
        'This configuration',
        'Note:',
        'Remember',
        ...
    ]

    # 4. Extract object
    # Find first { and last }
    # Extract content between them

    # 5. Validate
    if starts_with('{') and ends_with('}'):
        return cleaned
```

### Common Issues Handled

| Issue | Solution |
|-------|----------|
| Markdown blocks | Strip ```javascript and ``` |
| Prefixes | Remove "Here is...", "Sure..." |
| Suffixes | Remove "Note:", "This will..." |
| Extra whitespace | Trim and clean |
| Multiple objects | Extract first valid one |

### Example Transformations

**Input 1**:
```
Here is the trace configuration:

```javascript
{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar'
}
```

This will create a bar chart.
```

**Output 1**:
```
{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar'
}
```

**Input 2**:
```
Sure, here is the JavaScript object:

{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar',
    marker: { color: '#118DFF' }
}

Note: Make sure to include this in your Plotly.newPlot call.
```

**Output 2**:
```
{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar',
    marker: { color: '#118DFF' }
}
```

---

## 3. Validation

### Validation Checks

```python
def _validate_trace_config(code: str) -> bool:
    """Validate that the trace config looks reasonable"""

    # 1. Length check
    if len(code) < 20:
        return False  # Too short

    # 2. Object structure
    if not (starts_with('{') and ends_with('}')):
        return False  # Not an object

    # 3. Content checks
    has_data_access = 'data.map' in code or 'data[' in code
    has_type = 'type:' in code
    has_valid_content = len(code) > 50

    # 4. Logic
    if has_data_access and has_valid_content:
        return True  # Has data access and content

    if has_type and len(code) > 40:
        return True  # Has type definition

    return False  # Doesn't meet criteria
```

### Validation Criteria

| Check | Requirement | Reason |
|-------|-------------|--------|
| Min length | > 20 chars | Basic sanity |
| Max length | < 10,000 chars | Prevent abuse |
| Starts with | `{` | Must be object |
| Ends with | `}` | Must be object |
| Data access | `data.map` or `data[` | Must use data |
| Type definition | `type:` | Should specify chart type |

### Valid Examples

✅ **Minimal but valid**:
```javascript
{
    x: data.map(d => d.region),
    type: 'bar'
}
```

✅ **Complete**:
```javascript
{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar',
    marker: { color: '#118DFF' },
    name: 'Sales'
}
```

### Invalid Examples

❌ **Too short**:
```javascript
{ type: 'bar' }
```

❌ **No data access**:
```javascript
{
    x: ['A', 'B', 'C'],
    y: [1, 2, 3],
    type: 'bar'
}
```

❌ **Not an object**:
```javascript
function createChart() { ... }
```

❌ **Markdown**:
```javascript
```javascript
{ ... }
```
```

---

## System Prompt

### Purpose
Reinforces constraints at the model level

### Content

```
You are a Plotly.js expert generating trace configurations for data visualizations.

RULES:
1. Return ONLY a JavaScript object (no functions, no Plotly.newPlot)
2. Start with { and end with }
3. NO markdown formatting (no ```, no code blocks)
4. NO explanations or comments
5. Use proper JavaScript syntax
6. Access data with: data.map(d => d.columnName)
7. Match column names exactly (case-sensitive)

VALID OUTPUT EXAMPLE:
{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar',
    marker: { color: '#118DFF' }
}

INVALID OUTPUTS:
- ```javascript ... ``` (NO markdown)
- function createChart() { ... } (NO functions)
- Plotly.newPlot(...) (NO plot calls)
- Here is the chart: { ... } (NO explanations)

Generate ONLY the trace object.
```

### Why It Works
- **Repetition**: Key points repeated multiple times
- **Examples**: Shows both valid and invalid
- **Explicit**: States exactly what NOT to do
- **Clear**: Simple, direct language

---

## Model Configuration

### Optimal Settings

```python
response = client.generate_content(
    prompt=prompt,
    system_prompt=system_prompt,
    max_tokens=2048,      # Enough for trace, not too much
    temperature=0.2       # Low but not zero (allows some creativity)
)
```

### Parameter Reasoning

| Parameter | Value | Why |
|-----------|-------|-----|
| max_tokens | 2048 | Trace configs ~200-500 tokens. 2048 gives buffer without waste |
| temperature | 0.2 | Low for consistency, but not 0 (too rigid) |
| top_p | Default | Let model handle |
| frequency_penalty | Default | Not needed for this task |

---

## Results

### Before Optimization

```
Response: "Sure, I can help you create a bar chart! Here's a function
that will create the visualization:

```javascript
function createBarChart() {
    const trace = {
        x: ['A', 'B', 'C'],
        y: [1, 2, 3],
        type: 'bar'
    };
    Plotly.newPlot('chart', [trace]);
}
```

This function creates a bar chart with..."
```

**Issues**:
- ❌ Has explanations
- ❌ Uses markdown
- ❌ Creates function (not just object)
- ❌ Doesn't use data.map()
- ❌ Hard-coded values

### After Optimization

```
Response: "{
    x: data.map(d => d.region),
    y: data.map(d => d.sales),
    type: 'bar',
    marker: { color: '#118DFF' },
    name: 'Sales by Region'
}"
```

**Success**:
- ✅ Just the object
- ✅ No markdown
- ✅ Uses data.map()
- ✅ Proper syntax
- ✅ Ready to use

---

## Testing

### Test Cases

```python
# Test 1: Clean markdown
input = "```javascript\n{...}\n```"
output = clean_response(input)
assert output == "{...}"

# Test 2: Remove prefix
input = "Here is the config: {...}"
output = clean_response(input)
assert output == "{...}"

# Test 3: Validate good config
code = "{ x: data.map(d => d.x), type: 'bar' }"
assert validate(code) == True

# Test 4: Reject bad config
code = "function() { ... }"
assert validate(code) == False
```

### Integration Test

```python
# Full pipeline test
response = llm.generate(prompt)
cleaned = clean_response(response)
valid = validate(cleaned)

if valid:
    use_in_dashboard(cleaned)
else:
    use_fallback()
```

---

## Maintenance

### When to Update Prompts

- **New LLM behaviors**: If models start producing new unwanted patterns
- **Better examples**: If you find clearer examples
- **New chart types**: When adding support for new visualizations
- **User feedback**: If generated charts consistently have issues

### How to Test Changes

1. Update prompt in code
2. Run test suite:
   ```bash
   python test_prompt_optimization.py
   ```
3. Generate sample charts
4. Review quality
5. Deploy if improved

---

## Best Practices

### DO ✅

1. **Be specific**: "Return ONLY a JavaScript object" > "Return the config"
2. **Show examples**: Real examples > Descriptions
3. **Repeat constraints**: Key rules mentioned 2-3 times
4. **Use formatting**: Clear sections with headers
5. **Provide context**: Sample data, column names, etc.
6. **Test thoroughly**: Try multiple models and inputs
7. **Log everything**: Track what works and what doesn't

### DON'T ❌

1. **Be vague**: "Generate a chart" is too broad
2. **Assume knowledge**: Free models may not know Plotly well
3. **Skip validation**: Always validate LLM output
4. **Trust blindly**: Clean and verify responses
5. **Over-complicate**: Keep prompts clear and focused
6. **Forget examples**: Examples are more valuable than prose
7. **Ignore failures**: Log and learn from failed generations

---

## Troubleshooting

### Issue: Model generates markdown

**Solution**:
- Strengthen system prompt emphasis on "NO markdown"
- Add cleaning step for ``` removal
- Try different model

### Issue: Model includes explanations

**Solution**:
- Add suffix removal in cleaning
- Emphasize "ONLY the object" in prompt
- Increase validation strictness

### Issue: Wrong column names

**Solution**:
- Include more sample data in prompt
- Emphasize "Match column names exactly"
- Show example with exact column names

### Issue: Invalid JavaScript syntax

**Solution**:
- Add syntax example to prompt
- Increase validation checks
- Use fallback for that chart

---

## Future Improvements

1. **Few-shot examples**: Include 2-3 perfect examples in prompt
2. **Syntax validation**: Parse JavaScript to verify validity
3. **Semantic validation**: Check that columns exist in data
4. **Model-specific prompts**: Optimize per model family
5. **Feedback loop**: Learn from successful/failed generations
6. **A/B testing**: Test prompt variations systematically
7. **Caching**: Cache successful prompts for similar charts

---

## Summary

The three-part optimization strategy:

```
Comprehensive Prompts
        ↓
    LLM generates response
        ↓
Response Cleaning
        ↓
    Validation
        ↓
    ✅ Use in dashboard
    ❌ Use fallback
```

**Result**:
- Higher success rate with free models
- More consistent output format
- Better error handling
- Graceful fallbacks when needed
