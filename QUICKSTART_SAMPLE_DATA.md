# Quick Start - Sample Data Feature

## 🚀 Try It Now (30 seconds)

### 1. Start the Server

```bash
cd data-visualization-platform
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

### 2. Open Your Browser

```
http://localhost:8000
```

### 3. Click a Sample Data Button

Look for the section **"🎯 Try with Sample Data"** below the file upload area.

Click any of the sample datasets:
- 📊 **Sales Performance** - E-commerce sales data
- 👥 **HR Metrics** - Employee performance data
- 🌐 **Website Analytics** - Web traffic and conversions
- 📊 **Hate Crime** - Large public dataset (219k rows)

### 4. Watch the Magic

- Real-time progress bar updates
- See each processing stage
- Charts appear inline when complete
- All visualizations are KPI-focused!

### 5. Explore Your Dashboard

- Interactive charts powered by Plotly.js
- Zoom, pan, hover for details
- Download complete dashboard
- Upload new file to start over

---

## 📊 What You'll See

### Sample Data: Website Analytics

**Charts Generated**:
1. **Page Views by Date** - Bar chart showing traffic over time
2. **Page Views Trend** - Line chart showing temporal patterns
3. **Page Views vs Unique Visitors** - Scatter plot showing correlation
4. **Conversions by Traffic Source** - Pie chart showing channel performance

**Processing Time**: ~2-3 minutes

---

## 🎯 Key Features

✅ **No Upload Required** - Click and go
✅ **KPI-Focused** - Only meaningful metrics
✅ **Real-Time Updates** - See progress live
✅ **Inline Charts** - No page reloads
✅ **Error Visibility** - See what worked/failed

---

## 🔧 Troubleshooting

### Sample Data Buttons Not Showing?

**Check**:
```bash
# Is server running?
ps aux | grep uvicorn

# Test API directly
curl http://localhost:8000/api/v2/sample-data/list
```

### Processing Stuck?

**Check**:
```bash
# Check server logs
# Look for "Stage 0", "Stage 1", "Stage 2" messages
```

### No Charts Appearing?

**Check**:
1. Open browser console (F12)
2. Look for JavaScript errors
3. Check if session completed: `curl http://localhost:8000/api/v2/status/{session_id}`

---

## 📚 Learn More

- [SAMPLE_DATA_FEATURE.md](SAMPLE_DATA_FEATURE.md) - Complete documentation
- [SAMPLE_DATA_IMPLEMENTATION.md](SAMPLE_DATA_IMPLEMENTATION.md) - Technical details
- [WHATS_NEW_V3.md](WHATS_NEW_V3.md) - All V3 features

---

## 💡 Pro Tips

1. **Try different samples** - Each has unique chart types
2. **Watch the badges** - See if charts are AI-generated or fallback
3. **Check browser console** - See processing logs
4. **Download dashboard** - Works offline (except Plotly CDN)

---

**Enjoy exploring your data! 🎉**
