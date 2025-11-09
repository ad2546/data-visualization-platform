# How to Run the Application

## Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment
You already have a `.env` file! Just make sure it contains:
```
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
PORT=8000
```

If you need to edit it:
```bash
nano .env
# or
code .env
```

### Step 3: Run the Application

**Option A: Simple (Recommended)**
```bash
python main.py
```

**Option B: With auto-reload (for development)**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Option C: Using the startup script**
```bash
./run.sh
```

## Access the Application

Once running, open your browser:
```
http://localhost:8000
```

## What Happens Next?

1. **Upload a file** (CSV, Excel, or JSON)
2. **Wait for processing** - The 3-stage pipeline will:
   - Stage 0: Analyze business context (free LLM)
   - Stage 1: Generate visualization recommendations
   - Stage 2: Generate dashboard code (qwen3-coder)
3. **View your dashboard** - Interactive visualizations!

## Check if It's Running

Visit: `http://localhost:8000/health`

You should see:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "openrouter_configured": true,
  "model": "anthropic/claude-3.5-sonnet"
}
```

## Troubleshooting

### Port Already in Use?
```bash
PORT=8080 python main.py
```
Then access at `http://localhost:8080`

### Missing Dependencies?
```bash
pip install -r requirements.txt
```

### API Key Issues?
Check your `.env` file has:
```
OPENROUTER_API_KEY=sk-or-v1-...
```

### Need to See Logs?
The application logs to console. For more detail, set in `.env`:
```
LOG_LEVEL=DEBUG
```

## Stop the Application

Press `Ctrl+C` in the terminal where it's running.

