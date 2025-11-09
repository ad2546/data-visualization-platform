# Free Deployment Options for FastAPI Application

## 🚀 Best Free Hosting Platforms

### 1. **Render** ⭐ RECOMMENDED
**Best for**: Full-stack apps with databases and background workers

**Pros**:
- ✅ **Free tier**: 750 hours/month (enough for 1 app)
- ✅ Zero configuration deployment
- ✅ Auto-deploy from GitHub
- ✅ Custom domains
- ✅ SSL certificates included
- ✅ Environment variables support
- ✅ Persistent disk storage
- ✅ No credit card required

**Cons**:
- ⚠️ App sleeps after 15 min inactivity (30s cold start)

**Deploy Steps**:
```bash
# 1. Create render.yaml in project root
# 2. Push to GitHub
# 3. Connect repo on render.com
# 4. Deploy automatically
```

**Setup Time**: 5 minutes
**URL**: https://render.com

---

### 2. **Railway** ⭐ RECOMMENDED
**Best for**: Modern apps with databases

**Pros**:
- ✅ $5/month free credit
- ✅ Auto-deploy from GitHub
- ✅ Custom domains
- ✅ Environment variables
- ✅ PostgreSQL/Redis included
- ✅ No sleep/cold starts
- ✅ Great performance

**Cons**:
- ⚠️ Credit card required (won't charge if under $5)
- ⚠️ Usage-based (may run out of credits)

**Deploy Steps**:
```bash
# 1. Connect GitHub repo
# 2. Railway auto-detects Python
# 3. Add environment variables
# 4. Deploy
```

**Setup Time**: 3 minutes
**URL**: https://railway.app

---

### 3. **Fly.io**
**Best for**: Global edge deployment

**Pros**:
- ✅ Free tier: 3 VMs with 256MB RAM
- ✅ Global deployment (multiple regions)
- ✅ No sleep
- ✅ Persistent volumes
- ✅ Docker-based
- ✅ Fast cold starts

**Cons**:
- ⚠️ Credit card required
- ⚠️ CLI-based deployment

**Deploy Steps**:
```bash
# 1. Install Fly CLI
fly auth login

# 2. Launch app
fly launch

# 3. Deploy
fly deploy
```

**Setup Time**: 10 minutes
**URL**: https://fly.io

---

### 4. **Vercel** (with FastAPI)
**Best for**: Frontend + serverless API

**Pros**:
- ✅ Free tier included
- ✅ Auto-deploy from GitHub
- ✅ Custom domains
- ✅ Fast edge network
- ✅ Zero configuration

**Cons**:
- ⚠️ Serverless only (no persistent connections)
- ⚠️ 10s max execution time
- ⚠️ Not ideal for long-running tasks

**Deploy Steps**:
```bash
# 1. Create vercel.json
# 2. Push to GitHub
# 3. Import on Vercel
```

**Setup Time**: 5 minutes
**URL**: https://vercel.com

---

### 5. **PythonAnywhere**
**Best for**: Python-specific hosting

**Pros**:
- ✅ 100% free tier available
- ✅ Python-optimized
- ✅ No credit card required
- ✅ Persistent storage
- ✅ SSH access

**Cons**:
- ⚠️ Limited CPU (100s/day)
- ⚠️ Older Python versions
- ⚠️ Manual deployment

**Deploy Steps**:
```bash
# 1. Upload code via web interface
# 2. Configure WSGI
# 3. Set environment variables
```

**Setup Time**: 15 minutes
**URL**: https://www.pythonanywhere.com

---

### 6. **Koyeb**
**Best for**: Dockerized apps

**Pros**:
- ✅ Free tier included
- ✅ GitHub integration
- ✅ Auto-deploy
- ✅ No cold starts
- ✅ Good performance

**Cons**:
- ⚠️ Credit card required
- ⚠️ Smaller free tier

**Setup Time**: 5 minutes
**URL**: https://www.koyeb.com

---

## 📊 Comparison Table

| Platform | Free Tier | Cold Starts | Card Required | Best For |
|----------|-----------|-------------|---------------|----------|
| **Render** | 750h/month | Yes (30s) | No | General apps |
| **Railway** | $5 credit | No | Yes | Modern apps |
| **Fly.io** | 3 VMs | No | Yes | Global apps |
| **Vercel** | Unlimited | No | No | Serverless |
| **PythonAnywhere** | 100s CPU/day | No | No | Python only |
| **Koyeb** | Limited | No | Yes | Docker apps |

---

## 🎯 Recommended: Render Deployment

For your data visualization platform, **Render** is the best choice because:
- ✅ No credit card needed
- ✅ Perfect for FastAPI apps
- ✅ Handles file uploads
- ✅ Easy environment variables
- ✅ Auto-deploy from GitHub

### Quick Deploy to Render

**Step 1**: Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: data-viz-platform
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: OPENROUTER_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: 3.11
    disk:
      name: uploads
      mountPath: /app/uploads
      sizeGB: 1
```

**Step 2**: Create `render-build.sh`:

```bash
#!/usr/bin/env bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Step 3**: Push to GitHub

**Step 4**: Go to https://render.com
1. Sign up with GitHub
2. Click "New +"
3. Select "Web Service"
4. Connect your repo
5. Render auto-detects `render.yaml`
6. Add `OPENROUTER_API_KEY` in environment
7. Click "Create Web Service"

**Step 5**: Wait 2-3 minutes for deployment

**Step 6**: Your app is live at:
```
https://data-viz-platform-xxxx.onrender.com
```

---

## 🔧 Alternative: Railway Deployment

**Step 1**: Push to GitHub

**Step 2**: Go to https://railway.app
1. Sign up with GitHub
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repo
5. Railway auto-detects Python

**Step 3**: Add environment variables:
```
OPENROUTER_API_KEY=your_key_here
```

**Step 4**: Railway deploys automatically

**Your app**: `https://your-app.up.railway.app`

---

## 🚀 Alternative: Fly.io Deployment

**Step 1**: Install Fly CLI:
```bash
# macOS
brew install flyctl

# Linux/WSL
curl -L https://fly.io/install.sh | sh
```

**Step 2**: Login:
```bash
fly auth login
```

**Step 3**: Launch app:
```bash
fly launch
# Follow prompts
```

**Step 4**: Set secrets:
```bash
fly secrets set OPENROUTER_API_KEY=your_key_here
```

**Step 5**: Deploy:
```bash
fly deploy
```

**Your app**: `https://your-app.fly.dev`

---

## ⚠️ Important Notes

### File Uploads
For platforms with ephemeral filesystems (Render free tier):
- Files uploaded to `/app/uploads` are temporary
- Consider using cloud storage (AWS S3, Cloudinary) for persistence
- Or upgrade to Render paid tier with persistent disk

### Environment Variables
Always set:
```
OPENROUTER_API_KEY=your_api_key
PYTHON_VERSION=3.11
PORT=8000 (auto-set by most platforms)
```

### Performance
Free tiers typically have:
- 512MB - 1GB RAM
- 0.5 - 1 CPU
- Good enough for demo/testing
- May timeout on large datasets (219k row hate_crime.csv)

### Sleep/Cold Starts
**Platforms with sleep**:
- Render (15 min inactivity → 30s cold start)
- PythonAnywhere (daily timeout)

**No sleep**:
- Railway (until credits run out)
- Fly.io (always on)
- Koyeb (always on)

---

## 🎯 My Recommendation

**For This Project**: Use **Render**

**Why**:
1. ✅ No credit card required
2. ✅ Perfect for FastAPI
3. ✅ GitHub auto-deploy
4. ✅ Free SSL
5. ✅ Environment variables
6. ✅ 750 hours free (enough for 1 app)

**Trade-off**: 30s cold start after 15 min inactivity (acceptable for demo)

---

## 📝 Next Steps

Choose your platform and I can help you:
1. Create the deployment configuration files
2. Set up the deployment
3. Configure environment variables
4. Test the deployed app

**Which platform would you like to use?**
- Render (recommended, no card)
- Railway (better performance, card required)
- Fly.io (global, card required)
