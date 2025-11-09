# Template + Snippets Approach

## Overview

The new approach uses a **base HTML template** with **LLM-generated snippets** instead of generating full HTML. This provides several benefits:

### Benefits

1. **Lower Token Usage** - LLM only generates small trace config objects instead of full HTML
2. **Well-formed HTML** - Base template ensures proper structure every time
3. **Consistent Styling** - All dashboards use the same Power BI-themed design
4. **Better Reliability** - Less chance of malformed HTML or syntax errors
5. **Easier Maintenance** - Update template once, affects all generated dashboards

## Architecture

### Components

1. **[app/templates/dashboard_base.html](app/templates/dashboard_base.html)**
   - Base HTML template with placeholders
   - Includes all CSS styling
   - Has proper structure (DOCTYPE, head, body, etc.)
   - Responsive grid layout

2. **[app/agents/viz_generator.py](app/agents/viz_generator.py)**
   - Generates only Plotly trace configurations
   - Combines traces with base template
   - Creates individual chart functions with error handling

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LLM generates ONLY trace config (minimal tokens)         │
│    {                                                         │
│      x: data.map(d => d.region),                            │
│      y: data.map(d => d.sales),                             │
│      type: 'bar',                                            │
│      marker: { color: '#118DFF' }                           │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Python wraps trace in function with error handling       │
│    function createChart1() {                                 │
│      try {                                                   │
│        const trace = { ... };                               │
│        Plotly.newPlot('chart1', [trace], layout, config);   │
│      } catch (error) { ... }                                │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Inject into base template placeholders                   │
│    {{CHART_CONTAINERS}} → HTML divs for each chart          │
│    {{CHART_SCRIPTS}} → All chart functions                  │
│    {{CHART_INITIALIZERS}} → createChart1(); createChart2(); │
│    {{DATA}} → Embedded dataset                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Output: Complete, well-formed HTML dashboard             │
└─────────────────────────────────────────────────────────────┘
```

## Token Savings

### Before (Full HTML Generation)
- **Prompt**: ~2000 tokens (includes full HTML example)
- **Response**: ~3000 tokens (full HTML document)
- **Total per chart**: ~5000 tokens
- **For 6 charts**: ~30,000 tokens

### After (Snippet Generation)
- **Prompt**: ~500 tokens (just trace config example)
- **Response**: ~200 tokens (small trace object)
- **Total per chart**: ~700 tokens
- **For 6 charts**: ~4,200 tokens

**Savings: ~85% reduction in token usage!**

## Prompt Changes

### Old Prompt (Full HTML)
```
Generate a complete HTML dashboard with 6 charts...
Include DOCTYPE, head, body, CSS, JavaScript...
[3000+ character prompt]
```

### New Prompt (Trace Only)
```
Generate ONLY a Plotly.js trace configuration object.

CHART: bar chart
X_COLUMN: region
Y_COLUMN: sales

Return ONLY:
{
  x: data.map(d => d.region),
  y: data.map(d => d.sales),
  type: 'bar'
}
```

## Testing

Run the test script to verify:

```bash
source .venv/bin/activate
python test_template_approach.py
```

Expected output:
```
✓ Dashboard generated successfully!
✓ Dashboard size: 5849 bytes
✓ Number of charts: 2
✓ All tests passed!
```

## Template Placeholders

The base template uses these placeholders:

- `{{DASHBOARD_TITLE}}` - Dashboard title
- `{{DASHBOARD_SUBTITLE}}` - Dataset info and domain
- `{{CHART_CONTAINERS}}` - HTML divs for each chart
- `{{DATA}}` - Embedded JSON dataset
- `{{CHART_SCRIPTS}}` - Chart generation functions
- `{{CHART_INITIALIZERS}}` - Function calls to create charts

## Error Handling

Each chart has try-catch error handling:

```javascript
function createChart1() {
    try {
        const trace = { /* LLM generated */ };
        Plotly.newPlot('chart1', [trace], layout, config);
        console.log('Chart 1 created successfully');
    } catch (error) {
        console.error('Error creating chart 1:', error);
        document.getElementById('chart1').innerHTML =
            '<div class="loading">Error loading chart</div>';
    }
}
```

If a chart fails, others still render correctly.

## Key Code Changes

### viz_generator.py:_create_single_chart_prompt()
- Changed to request ONLY trace config object
- Reduced prompt size by ~75%
- More focused instructions for LLM

### viz_generator.py:_combine_charts_into_dashboard()
- Loads base template from file
- Wraps each trace in error-handling function
- Replaces placeholders with generated content
- Returns complete, well-formed HTML

### viz_generator.py:_get_code_system_prompt()
- Updated to emphasize: "Return ONLY trace objects"
- No markdown, no explanations, just pure JavaScript

## Future Enhancements

Potential improvements:

1. **Chart Type Templates** - Pre-defined templates for common chart types
2. **Theme Switching** - Multiple color schemes (Power BI, Material, Dark mode)
3. **Custom CSS Injection** - Allow users to customize styling
4. **Template Versioning** - Support multiple template versions
5. **Fallback Traces** - Pre-built fallback configs for when LLM fails

## Example Output

The generated HTML is:
- ✓ Valid HTML5
- ✓ Properly formatted
- ✓ Includes error handling
- ✓ Responsive design
- ✓ Power BI themed
- ✓ Works without internet (except Plotly CDN)

See `test_dashboard.html` for an example.
