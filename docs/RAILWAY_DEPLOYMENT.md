# 🚂 Railway Deployment Guide

Complete guide to deploy your AI Trading Bot backend to Railway.app

---

## 📋 Prerequisites

- GitHub account (your repo is already connected)
- Railway account (sign up at https://railway.app)
- Your trading bot repository

---

## 🚀 Step-by-Step Deployment

### Step 1: Sign Up for Railway

1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Sign in with GitHub
4. Authorize Railway to access your repositories

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository: `HBarefoot/ai-trading-bot`
4. Railway will detect the configuration automatically

### Step 3: Add PostgreSQL Database

1. In your Railway project dashboard, click **"New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically create a database and set the `DATABASE_URL` environment variable
4. Wait for the database to provision (takes ~30 seconds)

### Step 4: Configure Environment Variables

Click on your backend service, then go to **"Variables"** tab and add:

```bash
# Required
DATABASE_URL=postgresql://...  # Auto-set by Railway
PORT=8000                       # Railway will override this with $PORT

# Optional - Trading APIs (add if needed)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here

# Optional - Security
API_SECRET_KEY=your-secret-key-for-jwt-tokens
```

**Note:** `DATABASE_URL` is automatically set when you add PostgreSQL. Don't override it!

### Step 5: Deploy Backend

1. Railway will automatically deploy after configuration
2. Click **"Deploy"** if needed
3. Wait for deployment (~2-3 minutes)
4. Check the **"Deployments"** tab for progress

### Step 6: Get Your API URL

1. Go to your backend service in Railway
2. Click **"Settings"** tab
3. Under **"Domains"**, click **"Generate Domain"**
4. Copy the domain (e.g., `ai-trading-bot-production.up.railway.app`)
5. Your API URL will be: `https://your-domain.up.railway.app`

---

## 🔧 Important Configuration

### Railway Uses `requirements-backend.txt`

By default, Railway will use `requirements.txt`. To use the optimized backend requirements:

**Option A: Rename files (Recommended)**
```bash
# Already done for you!
# requirements.txt → lightweight (Streamlit Cloud)
# requirements-backend.txt → backend dependencies
```

**Option B: Configure Railway to use different file**
1. Go to Railway project settings
2. Find **"Build Command"**
3. Set: `pip install -r requirements-backend.txt`

### Database Schema Creation

The backend will automatically create the database schema on first startup. Check logs to verify:

```
INFO: Database tables created successfully
INFO: API started successfully
```

---

## 🧪 Testing Your Deployment

### 1. Test Health Endpoint

```bash
curl https://your-railway-domain.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T...",
  "version": "1.0.0"
}
```

### 2. Test API Documentation

Visit: `https://your-railway-domain.up.railway.app/docs`

You should see the interactive FastAPI documentation.

### 3. Check Logs

1. Go to Railway dashboard
2. Click your backend service
3. Check **"Logs"** tab for any errors

---

## 🔗 Connect Streamlit Frontend

### Update Streamlit Cloud Configuration

1. Go to Streamlit Cloud: https://share.streamlit.io
2. Open your app settings
3. Go to **"Secrets"** section
4. Add:

```toml
app_password = "your-secure-password"
api_url = "https://your-railway-domain.up.railway.app"
```

5. Save and redeploy

### Update Local Dashboard (Optional)

The dashboard will automatically use the Railway API when configured via secrets.

---

## 💰 Railway Pricing

### Free Tier (Hobby Plan)
- ✅ **$5 worth of usage free per month**
- ✅ PostgreSQL database included
- ✅ Automatic SSL certificates
- ✅ Custom domains
- ✅ Environment variables
- ⚠️ Enough for testing and light usage

### Usage Estimates
- Backend API: ~$0.30-1.00/day depending on usage
- PostgreSQL: ~$0.10-0.30/day
- **Total: ~$12-40/month** for moderate usage

### Tips to Stay in Free Tier
- Backend sleeps after 10 minutes of inactivity
- Database is always on (minimal cost)
- Use for testing/demo purposes

---

## 🔍 Troubleshooting

### Deployment Fails

**Problem:** Build errors
**Solution:** Check Railway logs for specific error
```bash
# Common fixes:
1. Ensure requirements-backend.txt has all dependencies
2. Check Python version (Railway uses 3.11 by default)
3. Verify no syntax errors in backend code
```

**Problem:** Database connection errors
**Solution:** 
1. Verify PostgreSQL is added to project
2. Check `DATABASE_URL` is set automatically
3. Wait for database to fully provision

### Health Check Fails

**Problem:** `/health` endpoint returns 404
**Solution:**
1. Check Railway is using correct start command
2. Verify: `uvicorn src.backend.main:app --host 0.0.0.0 --port $PORT`
3. Check logs for startup errors

### CORS Errors in Frontend

**Problem:** Frontend can't connect to backend
**Solution:** Backend already has CORS configured for `*` (all origins)
- Check Railway domain is correct in Streamlit secrets
- Verify HTTPS is used (not HTTP)

---

## 📊 Monitoring Your Deployment

### Railway Dashboard
- **Deployments:** View build and deployment history
- **Logs:** Real-time application logs
- **Metrics:** CPU, memory, and network usage
- **Database:** PostgreSQL connection and storage info

### Health Monitoring
Set up a simple health check with:
- **UptimeRobot** (free)
- **Healthchecks.io** (free)

Monitor: `https://your-domain.up.railway.app/health`

---

## 🔐 Security Best Practices

1. **Environment Variables:** Store all secrets in Railway
2. **API Keys:** Never commit to GitHub
3. **CORS:** Update to specific origins in production:
   ```python
   allow_origins=["https://your-streamlit-app.streamlit.app"]
   ```
4. **Database:** Railway PostgreSQL includes SSL by default

---

## 🚀 Next Steps After Deployment

1. ✅ Verify health endpoint works
2. ✅ Check API docs are accessible
3. ✅ Update Streamlit secrets with Railway URL
4. ✅ Test frontend → backend connection
5. ✅ Add exchange API keys if trading live
6. ✅ Monitor logs for first 24 hours

---

## 📝 Quick Reference

### Railway CLI (Optional)

Install Railway CLI for advanced management:
```bash
npm i -g @railway/cli
railway login
railway link
railway logs
```

### Important URLs
- **Railway Dashboard:** https://railway.app/project/[your-project-id]
- **API Docs:** https://your-domain.up.railway.app/docs
- **Health Check:** https://your-domain.up.railway.app/health
- **Database:** Accessible via Railway dashboard

---

## 🆘 Need Help?

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **GitHub Issues:** Open an issue in your repository

---

## ✨ Success Checklist

- [ ] Railway account created
- [ ] Project deployed from GitHub
- [ ] PostgreSQL database added
- [ ] Environment variables configured
- [ ] Custom domain generated
- [ ] Health endpoint returns 200
- [ ] API docs accessible
- [ ] Streamlit secrets updated with Railway URL
- [ ] Frontend successfully connects to backend
- [ ] Trading bot API responding correctly

**Congratulations! Your AI Trading Bot backend is now live on Railway! 🎉**
