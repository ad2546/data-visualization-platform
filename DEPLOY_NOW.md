# 🚀 Deploy Your App NOW (5 Minutes)

## Option 1: Render (RECOMMENDED - No Credit Card)

### Step 1: Sign Up
Go to: https://render.com
- Click "Get Started"
- Sign up with GitHub

### Step 2: Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub account if not already connected
3. Select repository: `data-visualization-platform`
4. Select branch: `feature/sample-data-kpi-visualizations`

### Step 3: Render Auto-Configures
Render will detect `render.yaml` and auto-fill:
- **Name**: data-viz-platform
- **Environment**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 4: Add Environment Variable
Scroll down to "Environment Variables":
- Click "Add Environment Variable"
- **Key**: `OPENROUTER_API_KEY`
- **Value**: Your OpenRouter API key
- Click "Add"

### Step 5: Deploy!
- Click "Create Web Service"
- Wait 2-3 minutes for build and deployment
- Your app will be live at: `https://data-viz-platform-xxxx.onrender.com`

### Step 6: Test Your App
- Open the URL Render provides
- Click a sample data button (e.g., "Sales Performance")
- Watch AI generate your dashboard!

**Done!** 🎉

---

## Option 2: Railway (Better Performance - Credit Card Required)

### Step 1: Sign Up
Go to: https://railway.app
- Click "Start a New Project"
- Sign up with GitHub

### Step 2: Deploy from GitHub
1. Click "Deploy from GitHub repo"
2. Select repository: `data-visualization-platform`
3. Select branch: `feature/sample-data-kpi-visualizations`
4. Railway auto-detects Python and deploys

### Step 3: Add Environment Variable
1. Click on your service
2. Go to "Variables" tab
3. Click "New Variable"
4. **Variable**: `OPENROUTER_API_KEY`
5. **Value**: Your OpenRouter API key
6. Click "Add"

### Step 4: Get Your URL
- Go to "Settings" tab
- Click "Generate Domain"
- Your app is live at: `https://your-app.up.railway.app`

**Done!** 🎉

---

## Option 3: Fly.io (Global Deployment - Credit Card Required)

### Step 1: Install Fly CLI
```bash
# macOS
brew install flyctl

# Linux/WSL
curl -L https://fly.io/install.sh | sh
```

### Step 2: Login
```bash
fly auth login
```

### Step 3: Launch App
```bash
cd /Users/atharvadeshmukh/data-visualization-platform
fly launch --name data-viz-platform
```

Follow prompts:
- Region: Choose closest to you
- Database: No
- Deploy now: Yes

### Step 4: Set Environment Variables
```bash
fly secrets set OPENROUTER_API_KEY=your_api_key_here
```

### Step 5: Deploy
```bash
fly deploy
```

### Step 6: Open Your App
```bash
fly open
```

**Done!** 🎉

---

## ⚡ Quick Comparison

| Feature | Render | Railway | Fly.io |
|---------|--------|---------|--------|
| **Setup Time** | 5 min | 3 min | 10 min |
| **Credit Card** | ❌ No | ✅ Required | ✅ Required |
| **Cold Starts** | 30s after 15min | None | None |
| **Free Tier** | 750h/month | $5 credit | 3 VMs |
| **Best For** | Quick demo | Production | Global app |

---

## 🎯 Recommendation

**For Quick Demo**: Use **Render**
- No credit card needed
- 5 minute setup
- Perfect for sharing with others

**For Production**: Use **Railway** or **Fly.io**
- Better performance
- No cold starts
- More reliable

---

## 📱 After Deployment

### Share Your App
Once deployed, you can share:
```
🎉 Check out my AI-powered data visualization platform!
👉 https://your-app.onrender.com

Features:
✨ Click "Sales Performance" to see AI-generated dashboards
📊 KPI-focused visualizations
🌙 Dark theme UI
⚡ 3-stage AI pipeline
```

### Monitor Your App
- **Render**: Dashboard → View logs
- **Railway**: Project → Deployments → Logs
- **Fly.io**: `fly logs`

### Update Your App
Just push to GitHub:
```bash
git push origin feature/sample-data-kpi-visualizations
```

All platforms will auto-deploy! 🚀

---

## ⚠️ Important Notes

### Large Files
The `hate_crime.csv` (54.81 MB) may cause deployment issues on some platforms. If you encounter problems:

```bash
# Remove large file from git
git rm sample_data/hate_crime.csv
git commit -m "Remove large file for deployment"
git push
```

### Free Tier Limitations
- **Render**: App sleeps after 15 min (30s cold start)
- **Railway**: $5/month credit (usually lasts full month)
- **Fly.io**: 3 VMs with 256MB RAM each

### Environment Variables
Make sure to set:
- `OPENROUTER_API_KEY` - Required for AI features
- `PYTHON_VERSION` - Set to 3.11 (auto-set on most platforms)

---

## 🆘 Troubleshooting

### Build Failed
- Check `requirements.txt` has all dependencies
- Verify Python version (should be 3.11)
- Check Render/Railway logs for errors

### App Won't Start
- Verify start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Check if `OPENROUTER_API_KEY` is set
- Review application logs

### Sample Data Not Working
- Ensure `sample_data/` folder is committed to git
- Check if files are in `.gitignore`
- Verify API endpoints are accessible

---

## 🎉 You're Ready!

Choose your platform and deploy in 5 minutes:

1. **Render**: https://render.com (No card required)
2. **Railway**: https://railway.app (Better performance)
3. **Fly.io**: https://fly.io (Global deployment)

**Questions?** Check [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md) for detailed comparison.

Happy deploying! 🚀
