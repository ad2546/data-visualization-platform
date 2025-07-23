# Power BI Data Visualization Platform

An AI-powered business intelligence platform with authentic Power BI design, built with FastAPI and deployed on Google Cloud Platform.

## 🚀 Live Application

**Production URL:** https://data-viz-app-957109990200.us-central1.run.app

## ✨ Features

### 🎨 Authentic Power BI Design
- Official Power BI color scheme and styling
- Professional navigation and sidebar interface
- Microsoft-inspired design system
- Responsive layout optimized for business users

### 📊 Business Intelligence Dashboard
- **Agent-based Architecture**: Dual AI agents for optimal visualization recommendations
  - **Agent 1**: Analyzes data and recommends business-focused visualizations
  - **Agent 2**: Generates interactive HTML dashboards with Plotly.js
- **Domain-Aware Analysis**: Automatically detects business domains (sales, finance, marketing, HR, operations, entertainment)
- **Business-Focused Visualizations**: Filters out technical columns and focuses on actionable insights

### 🤖 AI-Powered Features
- **Smart Column Detection**: Automatically identifies KPIs, trend metrics, and business segments
- **Business Context Integration**: Optional user context enhances recommendation accuracy
- **Intelligent Aggregations**: Suggests appropriate data aggregations for meaningful insights

### 🔄 Enhanced User Experience
- **Dual New Session Options**: Start fresh from upload area or after viewing dashboard
- **New Tab Dashboard Opening**: Dashboards open in new browser tabs for better workflow
- **Real-time Progress Tracking**: Visual feedback during data processing
- **Drag & Drop File Upload**: Intuitive file upload with validation

### 📈 Supported Data Formats
- **CSV Files**: Up to 1GB
- **Excel Files (.xlsx)**: Full spreadsheet support
- **JSON Files**: Structured data import

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI (Python 3.12)
- **AI/ML**: Google Cloud Vertex AI, Google ADK
- **Frontend**: HTML/CSS/JavaScript with Power BI design system
- **Visualization**: Plotly.js for interactive charts
- **Storage**: Google Cloud Storage for file handling
- **Database**: Google Cloud BigQuery integration
- **Deployment**: Google Cloud Run with Docker

### Agent Architecture
```
User Upload → Agent 1 (Recommendations) → Agent 2 (Code Generation) → Dashboard Display
```

1. **VizRecommendationAgent**: Analyzes top 50 rows, detects business domain, recommends visualizations
2. **VizCodeGenerator**: Creates interactive HTML dashboards based on recommendations

## 🚀 Deployment

### Google Cloud Run
- **Platform**: Serverless container deployment
- **Resources**: 4GB RAM, 2 CPU cores
- **Scaling**: Automatic based on demand
- **Region**: us-central1

### Environment Variables
```bash
GOOGLE_CLOUD_PROJECT=viz-tool-465716
GOOGLE_CLOUD_LOCATION=us-central1
STORAGE_BUCKET_NAME=vector-db22072025
MAX_FILE_SIZE_MB=1024
SESSION_CLEANUP_HOURS=24
```

## 📊 Visualization Types

The platform generates the following business-focused visualizations:

- **KPI Performance Dashboard**: Executive metrics display
- **Business Trend Analysis**: Time-based performance tracking
- **Business Segment Analysis**: Category-wise performance comparison
- **Strategic Correlation Analysis**: Key relationship insights
- **Market Share Analysis**: Portfolio distribution charts
- **Performance Benchmarking**: Variance analysis with box plots

## 🎯 Business Domains

Automatically detects and optimizes for:
- **Sales**: Revenue, orders, customer analysis
- **Finance**: ROI, cash flow, profit tracking
- **Marketing**: Campaign performance, conversion analysis
- **HR**: Employee metrics, performance tracking
- **Operations**: Inventory, delivery, efficiency metrics
- **Entertainment**: Content performance, audience analysis

## 📝 API Endpoints

### V2 API (Agent-Based)
- `POST /api/v2/upload` - Upload data file and start processing
- `GET /api/v2/status/{session_id}` - Check processing status
- `GET /api/v2/dashboard/{session_id}` - Retrieve generated dashboard
- `GET /api/v2/recommendations/{session_id}` - Get AI recommendations

### Utility Endpoints
- `GET /health` - Health check
- `GET /` - Power BI interface
- `DELETE /api/v2/session/{session_id}` - Clean up session

## 🛠️ Development

### Prerequisites
- Python 3.12+
- Google Cloud SDK
- Docker (for containerization)

### Local Development
```bash
# Clone the repository
git clone https://github.com/ad2546/data-visualization-platform.git
cd data-visualization-platform

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Google Cloud credentials

# Run locally
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment
```bash
# Build container
docker build -t powerbi-viz-platform .

# Run container
docker run -p 8080:8080 powerbi-viz-platform
```

## 🚀 Getting Started

1. **Visit the Platform**: https://data-viz-app-957109990200.us-central1.run.app
2. **Upload Your Data**: Drag & drop or browse for CSV/Excel/JSON files
3. **Add Context** (Optional): Provide business context for better recommendations
4. **Generate Dashboard**: AI agents create your business intelligence dashboard
5. **Explore Insights**: Interactive visualizations open in new tab
6. **Start New Session**: Use refresh buttons for additional analyses

## 🔒 Security

- **File Validation**: Strict file type and size validation
- **Data Privacy**: No persistent storage of user data
- **Session Management**: Automatic cleanup of temporary files
- **Cloud Security**: Leverages Google Cloud security features

## Project Structure

```
Google-ADK_Test/
├── .env                    # Environment configuration
├── Dockerfile             # Container configuration
├── requirements.txt       # Python dependencies
├── main.py                # Application entry point
├── uploads/               # Temporary file storage
└── app/
    ├── main.py            # FastAPI application
    ├── agents/
    │   ├── viz_recommender.py    # Agent 1: Recommendation engine
    │   └── viz_generator.py      # Agent 2: Dashboard generator
    ├── api/
    │   └── v2_endpoints.py       # V2 API routes
    ├── core/
    │   ├── blob_storage.py       # Cloud storage integration
    │   ├── vertex_database.py    # BigQuery integration
    │   └── visualization.py     # Legacy visualization logic
    └── templates/
        ├── powerbi_index.html    # Main Power BI interface
        ├── v2_index.html         # V2 interface
        └── index.html            # Legacy interface
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Cloud Platform** for AI/ML infrastructure
- **Microsoft Power BI** for design inspiration
- **Plotly.js** for interactive visualizations
- **FastAPI** for the robust backend framework

## 📞 Support

For support, issues, or feature requests, please create an issue in the GitHub repository.

---

**Built with ❤️ using Google Cloud AI and FastAPI**
