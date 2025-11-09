# Quick Start Guide

## Prerequisites

- Python 3.12+
- OpenRouter API key (get one at https://openrouter.ai/)

## Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure OpenRouter:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenRouter API key
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```
   
   Or use the startup script:
   ```bash
   ./run.sh
   ```

4. **Open your browser:**
   Navigate to `http://localhost:8000`

## Usage

1. Upload a CSV, Excel, or JSON file
2. Wait for AI analysis (1-3 minutes)
3. View your interactive dashboard!

## Troubleshooting

### "OpenRouter API key not configured"
- Make sure you've created `.env` file
- Add `OPENROUTER_API_KEY=your_key_here` to `.env`

### "Module not found"
- Run `pip install -r requirements.txt`
- Make sure you're in the project root directory

### Port already in use
- Change the port: `PORT=8080 python main.py`
- Or edit `.env` and set `PORT=8080`

## Supported Models

You can use any OpenRouter model. Popular choices:

- `anthropic/claude-3.5-sonnet` (default, best quality)
- `openai/gpt-4-turbo` (fast, good quality)
- `google/gemini-pro-1.5` (cost-effective)
- `anthropic/claude-3-opus` (highest quality, slower)

Set in `.env`:
```
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

