# Data Visualization Platform

A simplified AI-powered data visualization platform that uses OpenRouter to generate interactive dashboards from uploaded data files.

## Features

- **Sample Data for Testing**: NEW! One-click access to pre-loaded sample datasets with KPI-focused visualizations
- **Dark Theme Single-Page App**: Modern GitHub-inspired dark interface with inline chart rendering
- **AI-Powered Analysis**: Uses OpenRouter API for intelligent data analysis and visualization generation
- **KPI-Focused Visualizations**: Intelligent column analysis ensures business-meaningful charts (no ID fields as metrics)
- **Template + Snippets Architecture**: 85% token reduction using base template with LLM-generated chart snippets
- **Real-Time Processing**: Watch your dashboard generate in real-time with live progress updates
- **Error Visibility**: See LLM errors, fallback indicators, and detailed error messages per chart
- **Multiple File Formats**: Supports CSV, Excel (XLSX), and JSON files
- **Interactive Dashboards**: Generates beautiful, interactive HTML dashboards with Plotly.js
- **Business-Focused**: Automatically filters technical columns and focuses on business insights
- **Simple & Local**: Runs entirely locally, no cloud dependencies
- **Well-formed HTML**: Base template ensures perfect HTML structure every time

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure OpenRouter

1. Get your API key from [OpenRouter](https://openrouter.ai/)
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
   ```

### 3. Run the Application

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or use the main entry point:

```bash
python main.py
```

The application will be available at:
- `http://localhost:8000` - Dark theme single-page app (NEW!)
- `http://localhost:8000/v2` - Legacy light theme interface

## Usage

### Quick Start with Sample Data (30 seconds!)

1. **Open App**: Go to `http://localhost:8000`
2. **Click Sample Data**: Choose any pre-loaded sample dataset (Sales, HR, Website Analytics)
3. **Watch Processing**: Real-time progress updates as AI generates your dashboard
4. **Explore Charts**: Interactive visualizations appear inline on the same page

See [QUICKSTART_SAMPLE_DATA.md](QUICKSTART_SAMPLE_DATA.md) for details.

### Upload Your Own Data

1. **Upload Data**: Go to `http://localhost:8000` and upload a CSV, Excel, or JSON file
2. **Add Context** (Optional): Provide business context for better AI analysis
3. **Wait for Processing**: The system will analyze your data and generate recommendations
4. **View Dashboard**: Once complete, view your interactive dashboard with KPI-focused visualizations

## API Endpoints

### V2 API (Agent-Based)

- `POST /api/v2/upload` - Upload data file and start processing
- `GET /api/v2/status/{session_id}` - Check processing status
- `GET /api/v2/dashboard/{session_id}` - Retrieve generated dashboard
- `GET /api/v2/recommendations/{session_id}` - Get AI recommendations
- `GET /api/v2/business-context/{session_id}` - Get business context analysis
- `DELETE /api/v2/session/{session_id}` - Clean up session

### Sample Data Endpoints (NEW!)

- `GET /api/v2/sample-data/list` - List available sample datasets
- `GET /api/v2/sample-data/download/{filename}` - Download a sample dataset
- `POST /api/v2/sample-data/load/{filename}` - Load sample data and start processing

### Utility Endpoints

- `GET /health` - Health check
- `GET /` - Main dark theme interface
- `GET /v2` - Legacy light theme interface

## Architecture

The platform uses a dual-agent architecture with a template-based generation system:

1. **Agent 1 (Viz Recommender)**: Analyzes data and recommends visualizations
2. **Agent 2 (Viz Generator)**: Generates chart snippets and combines with base template

Both agents use OpenRouter API for AI-powered generation.

### Template + Snippets Approach

The platform uses an efficient **template + snippets** architecture:

- **Base Template** ([app/templates/dashboard_base.html](app/templates/dashboard_base.html)): Pre-built HTML structure with placeholders
- **LLM Snippets**: AI generates only small Plotly trace configurations (not full HTML)
- **Python Assembly**: Combines snippets with template to create complete dashboard

**Benefits**:
- 85% reduction in token usage vs. full HTML generation
- Guaranteed well-formed HTML structure
- Consistent Power BI-themed styling
- Better reliability and error handling

See [TEMPLATE_APPROACH.md](TEMPLATE_APPROACH.md) for detailed documentation.

## Supported Models

You can use any model supported by OpenRouter. Popular options:

- `anthropic/claude-3.5-sonnet` (default, recommended)
- `openai/gpt-4-turbo`
- `google/gemini-pro-1.5`
- `anthropic/claude-3-opus`

Set the model in your `.env` file using `OPENROUTER_MODEL`.

## Project Structure

```
.
├── app/
│   ├── agents/
│   │   ├── business_context_agent.py # Stage 0: Business context analysis
│   │   ├── viz_recommender.py        # Stage 1: Recommendation engine
│   │   └── viz_generator.py          # Stage 2: Dashboard generator
│   ├── api/
│   │   └── v2_endpoints.py           # API routes (includes sample data endpoints)
│   ├── core/
│   │   └── openrouter_client.py      # OpenRouter API client
│   ├── templates/
│   │   ├── index_dark.html           # Dark theme single-page app
│   │   ├── v2_index.html             # Legacy light theme
│   │   └── dashboard_base.html       # Base template for generated dashboards
│   └── main.py                       # FastAPI application
├── sample_data/                      # Sample datasets for testing
│   ├── sales_performance.csv
│   ├── hr_metrics.csv
│   └── website_analytics.csv
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
└── README.md                         # This file
```

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your OpenRouter API key

# Run the server
python -m uvicorn app.main:app --reload
```

### Logging

Set log level in `.env`:
```
LOG_LEVEL=DEBUG  # Options: DEBUG, INFO, WARNING, ERROR
```

## Documentation

### Quick Guides
- [QUICKSTART_SAMPLE_DATA.md](QUICKSTART_SAMPLE_DATA.md) - Get started in 30 seconds with sample data

### Feature Documentation
- [WHATS_NEW_V3.md](WHATS_NEW_V3.md) - Dark theme and inline chart rendering
- [SAMPLE_DATA_FEATURE.md](SAMPLE_DATA_FEATURE.md) - Complete sample data documentation
- [SAMPLE_DATA_IMPLEMENTATION.md](SAMPLE_DATA_IMPLEMENTATION.md) - Technical implementation details
- [TEMPLATE_APPROACH.md](TEMPLATE_APPROACH.md) - Template + snippets architecture
- [DARK_THEME_GUIDE.md](DARK_THEME_GUIDE.md) - Dark theme design system
- [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) - Prompt optimization details
- [PROMPT_OPTIMIZATION.md](PROMPT_OPTIMIZATION.md) - LLM prompt engineering guide

### Pipeline Documentation
- [PIPELINE.md](PIPELINE.md) - 3-stage processing pipeline
- [FREE_MODELS.md](FREE_MODELS.md) - Using free LLM models
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Platform improvements log

### Changelogs
- [CHANGES.md](CHANGES.md) - Version history
- [RUN.md](RUN.md) - Running the application

## License

MIT License
