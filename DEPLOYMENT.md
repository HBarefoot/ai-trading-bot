# Railway Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- Binance.US API credentials
- Git repository connected to Railway

## Quick Deploy Steps

### 1. Create New Project on Railway
```bash
# Option A: Deploy from GitHub
# Connect your repository in Railway dashboard

# Option B: Deploy from CLI
railway login
railway init
railway up
```

### 2. Add PostgreSQL Database
1. In Railway dashboard, click "New" → "Database" → "PostgreSQL"
2. Railway automatically sets `DATABASE_URL` environment variable
3. No manual configuration needed

### 3. Configure Environment Variables
Go to your Railway project → "Variables" and add:

**Required:**
```bash
BINANCE_API_KEY=your_actual_api_key
BINANCE_SECRET_KEY=your_actual_secret_key
SECRET_KEY=generate_random_string_here
APP_PASSWORD=your_dashboard_password
ENVIRONMENT=production
```

**Auto-provided by Railway:**
- `DATABASE_URL` (from PostgreSQL service)
- `PORT` (Railway assigns this)

**Optional (for AI features):**
```bash
OLLAMA_HOST=http://your-ollama-server:11434
OLLAMA_MODEL=llama3.2:3b
```

### 4. Deploy
```bash
git add .
git commit -m "Configure Railway deployment"
git push
```

Railway will automatically:
1. Detect Python project
2. Run `pip install -r requirements.txt`
3. Execute `python startup.py`
4. Check `/health` endpoint
5. Mark deployment as successful

## Verify Deployment

### Check Health Endpoint
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "version": "3.0.0"
}
```

### Check API Status
```bash
curl https://your-app.railway.app/api/status
```

### View Logs
```bash
railway logs
```

## Troubleshooting

### Build Fails: Missing Dependencies
**Problem:** `ModuleNotFoundError: No module named 'xyz'`

**Solution:**
1. Check `requirements.txt` has the missing package
2. Verify version compatibility
3. Check Railway build logs for pip errors

### Health Check Fails
**Problem:** Railway shows "Health check failed"

**Solution:**
1. Check logs: `railway logs`
2. Verify startup.py runs without errors
3. Test locally: `python startup.py`
4. Ensure `/health` endpoint is accessible

### Database Connection Issues
**Problem:** `sqlalchemy.exc.OperationalError`

**Solution:**
1. Verify PostgreSQL service is running
2. Check `DATABASE_URL` is set correctly
3. Ensure database is in same Railway project
4. Check connection string format

### Binance API Issues
**Problem:** App starts but no trading functionality

**Solution:**
1. Verify `BINANCE_API_KEY` and `BINANCE_SECRET_KEY` are set
2. Check API keys are valid on Binance.US
3. Ensure IP whitelist includes Railway's IPs (or set to 0.0.0.0/0)
4. App will run in "demo mode" without valid credentials

### Import Errors
**Problem:** Python can't find modules in `src/`

**Solution:**
- This is handled by `startup.py` which adds `src/` to Python path
- Verify file structure matches:
  ```
  /app
  ├── src/
  │   ├── api/
  │   ├── trading/
  │   └── ...
  ├── startup.py
  └── requirements.txt
  ```

## File Structure
```
ai-trading-bot/
├── src/                    # Main application code
│   ├── api/               # FastAPI endpoints
│   ├── trading/           # Trading engine
│   ├── strategies/        # Trading strategies
│   ├── data/              # Database models
│   └── ai/                # AI/sentiment analysis
├── startup.py             # Railway entry point
├── Procfile               # Process definition
├── railway.json           # Railway configuration
├── requirements.txt       # Python dependencies (MAIN)
├── requirements-backend.txt  # Legacy (not used)
├── requirements-minimal.txt  # For testing
├── .env.example           # Environment template
└── DEPLOYMENT.md          # This file
```

## Configuration Files

### Procfile
```
web: python startup.py
```

### railway.json
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python startup.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### requirements.txt
**Primary dependency file** - Optimized for cloud deployment with all trading features

## Development vs Production

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Run locally
python startup.py
```

### Production (Railway)
- Environment variables set in Railway dashboard
- PostgreSQL managed by Railway
- Auto-scaling and monitoring included
- HTTPS provided automatically

## Database Migrations

### Initial Setup
Railway will auto-create tables on first run via startup.py

### Manual Migrations
```bash
# If you need to run migrations manually
railway run alembic upgrade head
```

## Monitoring

### Check Application Status
```bash
# Via Railway CLI
railway logs --tail

# Via API
curl https://your-app.railway.app/api/status
```

### Key Metrics to Monitor
- Health check status
- API response times
- Database connection pool
- Trading signals generated
- Exchange API rate limits

## Scaling

Railway auto-scales based on:
- Memory usage
- CPU usage
- Request volume

For custom scaling:
1. Go to Railway dashboard
2. Select your service
3. Adjust "Settings" → "Deploy"

## Security Best Practices

1. **Never commit .env file**
   - Already in .gitignore
   - Use Railway environment variables

2. **Rotate API keys regularly**
   - Update in Railway dashboard
   - Restart deployment

3. **Use strong passwords**
   - Generate `SECRET_KEY` with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Use unique `APP_PASSWORD`

4. **Enable 2FA on Binance**
   - Required for API access
   - Reduces risk of unauthorized trading

5. **Monitor API usage**
   - Check Railway logs regularly
   - Set up alerts for errors

## Cost Optimization

### Free Tier Limits
- $5 free credits/month
- Hobby plan: $5/month
- Includes PostgreSQL

### Reduce Costs
1. **Remove ML dependencies** (if not needed)
   - Comment out scikit-learn, tensorflow, torch in requirements.txt
   - Saves ~500MB build space and reduces build time

2. **Use Nixpacks caching**
   - Railway caches pip packages between builds
   - Only reinstalls on requirements.txt changes

3. **Optimize database queries**
   - Ensure indexes on frequently queried columns
   - Use connection pooling (built into SQLAlchemy)

## Next Steps After Deployment

1. **Test all endpoints**
   - `/health` - Health check
   - `/api/status` - System status
   - `/api/trading/start` - Start trading engine
   - `/api/trades` - View trades

2. **Configure Binance API**
   - Verify API keys work
   - Test paper trading first
   - Enable live trading only when confident

3. **Set up monitoring**
   - Railway provides basic metrics
   - Consider external monitoring (Sentry, Datadog)

4. **Enable CORS properly**
   - Update `api_backend.py` with your frontend URL
   - Currently set to `["*"]` for development

5. **Add custom domain** (optional)
   - Configure in Railway dashboard
   - Update DNS records

## Support

- Railway Docs: https://docs.railway.app
- Project Issues: Check your repository issues
- Railway Discord: https://discord.gg/railway

---

**Last Updated:** 2024-01-01
**Railway Config Version:** 1.0
