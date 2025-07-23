# Data Visualization with Gemini and FastAPI

This project demonstrates a web application that leverages Google's Gemini model (via the Agent Development Kit - ADK) to generate data visualizations from uploaded CSV files. The backend is built with FastAPI, and the frontend uses a simple HTML interface with Bootstrap for styling and JavaScript for interactivity.

## Features

*   **CSV Upload:** Users can upload CSV files through a web interface (now supports files up to 1GB).
*   **AI-Powered Visualization:** A Gemini-powered agent analyzes the CSV data and generates multiple HTML-based visualizations.
*   **Interactive Frontend:** The generated visualizations are displayed directly in the browser.
*   **Vertex AI Integration:** Configured to use Vertex AI for model inference.
*   **Blob Storage Support:** Automatic cloud storage for large files using Google Cloud Storage.
*   **Asynchronous Processing:** Separate upload and generation processes with real-time progress tracking.
*   **Session Management:** Track and manage processing sessions with cleanup capabilities.

## Recent Enhancements

### Large Dataset Support
- Added support for files up to 1GB
- Automatic sampling for datasets > 100,000 rows (samples 50,000 rows)
- Efficient memory usage with chunked processing using aiofiles

### Blob Storage Integration
- Google Cloud Storage integration for large files
- Automatic fallback to local storage when cloud storage is unavailable
- Configurable bucket settings via environment variables

### Two-Step Process
1. **Upload**: Files are uploaded and stored (locally or in cloud)
2. **Generate**: Visualizations are generated asynchronously with progress tracking

### New API Endpoints

- `POST /upload-csv/` - Upload CSV file (returns session ID)
- `POST /generate/{session_id}` - Start visualization generation
- `GET /status/{session_id}` - Check processing status with progress
- `GET /session/{session_id}` - Get session results
- `DELETE /session/{session_id}` - Delete session and files
- `GET /cleanup` - Clean up old sessions (now includes blob storage cleanup)
- `GET /health` - Health check with blob storage status

## Project Structure

```
Google-ADK_Test/
├── .env
├── pyproject.toml
├── poetry.lock
├── readme.md
├── uploads/ (generated at runtime for uploaded CSVs and visualizations)
└── app/
    ├── main.py
    ├── core/
    │   └── visualization.py
    ├── static/
    │   └── (empty - for future CSS/JS)
    ├── templates/
    │   └── index.html
    ├── agents/ (original agents directory, now under app)
    └── web/ (original web directory, now under app)
```

*   **`.env`**: Environment variables for configuring API keys and Vertex AI settings.
*   **`pyproject.toml` / `poetry.lock`**: Poetry dependency management files.
*   **`readme.md`**: This documentation file.
*   **`uploads/`**: Directory where uploaded CSV files and generated HTML visualizations are stored.
*   **`app/`**: Contains the main application logic.
    *   **`main.py`**: The FastAPI application entry point, handling routes for the web interface and CSV uploads.
    *   **`core/visualization.py`**: Contains the core logic for processing CSVs, interacting with the Gemini agent, and generating visualizations.
    *   **`static/`**: Directory for static assets like CSS and JavaScript files (currently empty).
    *   **`templates/`**: Contains Jinja2 HTML templates for the web interface.
    *   **`agents/`**: The original `agents` directory, now nested under `app`.
    *   **`web/`**: The original `web` directory, now nested under `app`.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd Google-ADK_Test
    ```

2.  **Install Poetry (if you haven't already):**
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

3.  **Install dependencies:**
    ```bash
    poetry install
    ```

4.  **Configure environment variables:**
    Create or update the `.env` file in the project root with your Google Cloud and API keys. Ensure `GOOGLE_GENAI_USE_VERTEXAI` is set to `1` for Vertex AI usage.

    ```dotenv
    # Choose Model Backend: 0 -> ML Dev, 1 -> Vertex
    GOOGLE_GENAI_USE_VERTEXAI=1

    # Vertex backend config
    GOOGLE_CLOUD_PROJECT=your-gcp-project-id
    GOOGLE_CLOUD_LOCATION=your-gcp-region # e.g., us-central1

    # Blob Storage Configuration (optional)
    STORAGE_BUCKET_NAME=your-bucket-name

    # If using ML Dev backend (GOOGLE_GENAI_USE_VERTEXAI=0), provide your API key:
    # GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
    ```
    Replace `your-gcp-project-id` and `your-gcp-region` with your actual Google Cloud Project ID and desired region.
    
    For blob storage, create a Google Cloud Storage bucket and set `STORAGE_BUCKET_NAME` to enable large file support.

5.  **Run the application:**
    ```bash
    poetry run python app/main.py
    ```

    The application will be accessible at `http://0.0.0.0:8000`.

## How it Works

1.  **Frontend (HTML/JavaScript):**
    *   `app/templates/index.html` provides a simple form to upload a CSV file.
    *   JavaScript handles the form submission, sending the CSV to the FastAPI backend.
    *   It displays a loading spinner while the visualization is being generated and then renders the resulting HTML visualization.

2.  **Backend (FastAPI):**
    *   `app/main.py` defines the API endpoints:
        *   `/` (GET): Serves the `index.html` page.
        *   `/upload-csv/` (POST): Receives the uploaded CSV file.
    *   Upon receiving a CSV, it saves the file to the `uploads/` directory.
    *   It then calls `generate_visualization` from `app/core/visualization.py`.

3.  **Visualization Generation (Gemini Agent):**
    *   `app/core/visualization.py` contains the `generate_visualization` asynchronous function.
    *   It reads the uploaded CSV into a Pandas DataFrame.
    *   It initializes a `google.adk.agents.LlmAgent` with specific instructions for data visualization and a `get_data` tool.
    *   The `get_data` tool provides the Pandas DataFrame to the Gemini model.
    *   The agent is configured to use Vertex AI based on the `.env` settings.
    *   The agent processes the data and generates raw HTML content for the visualization.
    *   The generated HTML is saved as a new `.html` file in the `uploads/` directory.
    *   The path to this HTML file is returned to the frontend.

## Vertex AI Configuration

This application is set up to use Vertex AI as the backend for the Gemini model. Ensure your Google Cloud project is enabled for the Gemini API and that you have authenticated your environment (e.g., `gcloud auth application-default login`).

The `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` variables in your `.env` file are crucial for connecting to the correct Vertex AI endpoint.

## Error Handling

The application includes basic error handling for file uploads and visualization generation. Errors are caught and displayed on the frontend.

## Future Enhancements

*   More sophisticated error handling and logging.
*   User authentication and session management.
*   Support for different visualization libraries (e.g., D3.js, Bokeh).
*   Advanced data preprocessing options.
*   More detailed agent instructions and tool capabilities.
