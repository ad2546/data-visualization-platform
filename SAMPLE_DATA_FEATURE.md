# Sample Data Feature - Documentation

## Overview

The platform now includes a **Sample Data** feature that allows users to test the AI-powered visualization pipeline with pre-loaded datasets. This feature ensures all visualizations are KPI-focused and demonstrates the platform's capabilities without requiring users to upload their own data.

## Features

✅ **Pre-loaded Datasets** - 4 sample datasets with realistic business data
✅ **One-Click Loading** - Click a button to instantly start processing
✅ **KPI-Focused** - All samples designed to showcase meaningful metrics
✅ **Automatic Context** - Each sample includes business context for better AI analysis
✅ **Inline Integration** - Seamlessly integrated into the dark theme UI

## Available Sample Datasets

### 1. Sales Performance 📊
- **File**: `sales_performance.csv`
- **Rows**: 30
- **Columns**: 10
- **Description**: E-commerce sales data with revenue, profit, and customer satisfaction metrics by region and product category
- **Key Metrics**: revenue, profit, units_sold, customer_satisfaction
- **Dimensions**: region, product_category, date, sales_rep

### 2. HR Metrics 👥
- **File**: `hr_metrics.csv`
- **Rows**: 20
- **Columns**: 10
- **Description**: Human resources data with employee performance, salary, training hours, and satisfaction scores by department
- **Key Metrics**: salary, performance_score, training_hours, satisfaction_score, projects_completed
- **Dimensions**: department, position, hire_date

### 3. Website Analytics 🌐
- **File**: `website_analytics.csv`
- **Rows**: 30
- **Columns**: 10
- **Description**: Website traffic and conversion metrics including page views, bounce rate, and revenue by traffic source and device type
- **Key Metrics**: page_views, unique_visitors, conversions, revenue, bounce_rate, avg_session_duration
- **Dimensions**: traffic_source, device_type, country, date

### 4. Hate Crime Statistics 📊
- **File**: `hate_crime.csv`
- **Rows**: 219,073
- **Columns**: 28
- **Description**: Large-scale public dataset demonstrating platform's ability to handle substantial data volumes
- **Key Metrics**: ADULT_VICTIM_COUNT, JUVENILE_VICTIM_COUNT, TOTAL_OFFENDER_COUNT, VICTIM_COUNT
- **Dimensions**: DATA_YEAR, STATE_NAME, AGENCY_TYPE_NAME, BIAS_DESC, OFFENSE_NAME

## API Endpoints

### 1. List Sample Datasets

**Endpoint**: `GET /api/v2/sample-data/list`

**Description**: Returns all available sample datasets with metadata

**Response**:
```json
{
  "samples": [
    {
      "filename": "sales_performance.csv",
      "name": "Sales Performance",
      "size": 2216,
      "rows": 30,
      "columns": 10,
      "column_names": ["order_id", "date", "region", ...],
      "description": "E-commerce sales data with revenue, profit..."
    },
    ...
  ],
  "count": 4
}
```

### 2. Download Sample Dataset

**Endpoint**: `GET /api/v2/sample-data/download/{filename}`

**Description**: Download a specific sample dataset file

**Example**: `GET /api/v2/sample-data/download/sales_performance.csv`

**Response**: File download

### 3. Load Sample Dataset

**Endpoint**: `POST /api/v2/sample-data/load/{filename}`

**Description**: Load a sample dataset and start the 3-stage AI processing pipeline

**Example**: `POST /api/v2/sample-data/load/sales_performance.csv`

**Response**:
```json
{
  "session_id": "abc-123-def-456",
  "status": "processing",
  "message": "Sample dataset 'sales_performance.csv' loaded successfully...",
  "filename": "sales_performance.csv",
  "estimated_completion": "2-4 minutes",
  "pipeline_stages": [
    "Stage 0: Business Context Analysis (free LLM)",
    "Stage 1: Visualization Recommendations",
    "Stage 2: Code Generation (qwen3-coder)"
  ]
}
```

## UI Implementation

### Location
The sample data section appears in the upload area on the main page (`/`) below the file upload zone and business context input.

### Visual Design
- **Section Header**: "🎯 Try with Sample Data"
- **Description**: "Test the platform with pre-loaded datasets featuring KPI-focused visualizations"
- **Button Grid**: Responsive grid layout (3 columns on desktop, 1 on mobile)
- **Button Content**:
  - Icon (📊, 👥, 🌐)
  - Dataset name
  - Description
  - Metadata (rows, columns)

### Interaction Flow
```
1. User clicks sample data button
   ↓
2. Button disables (prevents double-click)
   ↓
3. Upload section hides
   ↓
4. Status section shows with progress
   ↓
5. POST /api/v2/sample-data/load/{filename}
   ↓
6. Poll /api/v2/status/{session_id}
   ↓
7. Charts render inline when complete
```

## File Structure

```
data-visualization-platform/
├── sample_data/               # Sample datasets directory
│   ├── sales_performance.csv
│   ├── hr_metrics.csv
│   ├── website_analytics.csv
│   └── hate_crime.csv
├── app/
│   ├── api/
│   │   └── v2_endpoints.py   # Sample data endpoints
│   └── templates/
│       └── index_dark.html   # UI with sample data buttons
```

## Code Components

### Backend (v2_endpoints.py)

**New Functions**:
- `list_sample_datasets()` - Lists all sample files with metadata
- `_get_sample_description(filename)` - Returns description for known samples
- `download_sample_dataset(filename)` - Downloads sample file
- `load_sample_dataset(filename)` - Loads sample and starts processing

**Security**:
- Path traversal protection (checks for `..`, `/`, `\`)
- File existence validation
- Proper error handling

### Frontend (index_dark.html)

**New Functions**:
- `loadSampleDatasets()` - Fetches and renders sample data buttons
- `getSampleIcon(filename)` - Returns emoji icon based on filename
- `loadSampleData(filename)` - Triggers sample data processing

**New CSS Classes**:
- `.sample-data-buttons` - Button grid container
- `.sample-data-btn` - Individual sample button
- `.sample-name` - Dataset name with icon
- `.sample-description` - Dataset description
- `.sample-meta` - Row/column metadata

## KPI-Focused Visualizations

All sample datasets are designed to generate **meaningful, business-focused visualizations**:

### What Makes a Good Visualization?

✅ **Good Examples**:
- "Revenue by Region" - Shows geographic performance
- "Average Salary by Department" - Compares compensation
- "Conversion Rate by Traffic Source" - Analyzes marketing effectiveness
- "Victim Count Trend by Year" - Shows temporal patterns

❌ **Bad Examples** (Prevented):
- "INCIDENT_ID by ORI" - ID fields are not metrics
- "Count of order_id" - Counting IDs is meaningless
- "employee_id Distribution" - IDs don't have distributions

### Column Analysis

The platform's column analysis (from `viz_recommender.py`) automatically:
1. **Identifies ID columns** - Excludes from metric usage
2. **Detects metrics** - Numeric columns with business meaning
3. **Finds dimensions** - Categorical/date fields for grouping
4. **Validates relationships** - Ensures meaningful X/Y pairings

## Testing

### Manual Testing

1. **Start server**:
   ```bash
   source .venv/bin/activate
   python -m uvicorn app.main:app --reload
   ```

2. **Open browser**: http://localhost:8000

3. **Click sample data button**: Choose any sample dataset

4. **Watch processing**: Real-time progress updates

5. **View results**: Interactive charts render inline

### API Testing

```bash
# List sample datasets
curl http://localhost:8000/api/v2/sample-data/list

# Load sample dataset
curl -X POST http://localhost:8000/api/v2/sample-data/load/sales_performance.csv

# Check status
curl http://localhost:8000/api/v2/status/{session_id}

# View dashboard
curl http://localhost:8000/api/v2/dashboard/{session_id}
```

## Performance

| Dataset | Rows | Columns | Processing Time | Charts Generated |
|---------|------|---------|-----------------|------------------|
| Sales Performance | 30 | 10 | ~2-3 min | 6 |
| HR Metrics | 20 | 10 | ~2-3 min | 6 |
| Website Analytics | 30 | 10 | ~2-3 min | 6 |
| Hate Crime | 219,073 | 28 | ~3-5 min | 6 |

**Note**: Large datasets (50k+ rows) are automatically sampled to 50,000 rows for processing.

## Error Handling

### UI Errors
- **Load failure**: Shows error alert with message
- **Network error**: Re-enables buttons for retry
- **Invalid file**: Displays validation error

### API Errors
- **File not found**: 404 with "Sample dataset not found"
- **Invalid filename**: 400 with "Invalid filename"
- **Processing error**: 500 with detailed error message

## Future Enhancements

1. **More Sample Datasets**
   - Financial data (stock prices, budgets)
   - Marketing data (campaigns, ROI)
   - Operations data (supply chain, inventory)

2. **Custom Sample Data**
   - Allow users to upload and share sample datasets
   - Community-contributed samples

3. **Sample Templates**
   - Pre-configured dashboard templates
   - Industry-specific layouts

4. **Sample Data Categories**
   - Group by industry (retail, healthcare, finance)
   - Filter by complexity (beginner, advanced)

## Troubleshooting

### Sample Data Buttons Not Showing

**Check**:
1. Is the server running? `ps aux | grep uvicorn`
2. Is the `/api/v2/sample-data/list` endpoint accessible?
3. Check browser console for JavaScript errors

**Solution**:
```bash
# Restart server
python -m uvicorn app.main:app --reload
```

### Sample Data Load Fails

**Check**:
1. Does the file exist in `sample_data/` directory?
2. Is the file readable? `ls -la sample_data/`
3. Check server logs for errors

**Solution**:
```bash
# Verify files
ls -lh sample_data/
# Check permissions
chmod 644 sample_data/*.csv
```

### Charts Don't Generate for Sample Data

**Check**:
1. Is OpenRouter API key set? `echo $OPENROUTER_API_KEY`
2. Are LLMs responding? Check server logs
3. Is column analysis working?

**Solution**:
- Review logs for LLM errors
- Check if fallback templates are being used
- Verify column analysis results in logs

## Summary

The Sample Data feature provides:
- ✅ Easy testing without user data
- ✅ Demonstration of platform capabilities
- ✅ KPI-focused visualization examples
- ✅ Seamless UI integration
- ✅ Robust error handling
- ✅ Automatic business context

**Result**: Users can instantly see the platform in action with meaningful, business-oriented visualizations! 🎉
