# 🚀 Quick Start - Railway Deployment

Your AI Trading Bot is ready for Railway deployment!

## 📦 What's Included

- ✅ `railway.json` - Railway configuration
- ✅ `Procfile` - Process definition for deployment
- ✅ `requirements-backend.txt` - Optimized backend dependencies
- ✅ `docs/RAILWAY_DEPLOYMENT.md` - Complete deployment guide

## ⚡ Quick Deploy (5 minutes)

1. **Sign up for Railway**: https://railway.app
2. **Create new project** → Deploy from GitHub → Select `ai-trading-bot`
3. **Add PostgreSQL database** → New → Database → PostgreSQL
4. **Generate domain** → Settings → Generate Domain
5. **Update Streamlit secrets** with your Railway URL

**Done!** Your backend is live. 🎉

## 📚 Full Documentation

See [RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md) for:
- Step-by-step instructions with screenshots
- Environment variable configuration
- Testing and troubleshooting
- Connecting frontend to backend
- Security best practices

## 🔗 Architecture

```
┌─────────────────────────────────────────────┐
│  Streamlit Cloud (Frontend)                 │
│  - Dashboard UI                             │
│  - Charts & Visualizations                  │
│  - Authentication                           │
└──────────────────┬──────────────────────────┘
                   │
                   │ HTTPS API Calls
                   │
┌──────────────────▼──────────────────────────┐
│  Railway (Backend)                          │
│  - FastAPI REST API                         │
│  - Trading Engine                           │
│  - Market Data Collection                   │
└──────────────────┬──────────────────────────┘
                   │
                   │ SQL Queries
                   │
┌──────────────────▼──────────────────────────┐
│  Railway PostgreSQL                         │
│  - Trades, Strategies, Portfolio            │
│  - Market Data, Alerts                      │
└─────────────────────────────────────────────┘
```

## 🎯 Next Steps

1. Deploy backend to Railway (5 min)
2. Update Streamlit secrets with Railway API URL
3. Test connection from dashboard
4. Add exchange API keys (optional)
5. Start trading! 📈

## 💡 Need Help?

- Full guide: [docs/RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md)
- Railway support: https://railway.app/help
- GitHub issues: Open an issue if you encounter problems
