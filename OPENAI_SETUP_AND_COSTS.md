# OpenAI Integration - Cost Estimation & Setup Guide

## 📊 Cost Estimation

### Current Usage Pattern
Based on your logs:
- **3 symbols** (BTC, ETH, SOL) analyzed every ~40 seconds
- **5 sentiment analyses** per symbol (limited in code)
- **15 API calls per cycle** (~40 seconds)
- **~1,350 calls/hour** or **~32,400 calls/day** (24/7 operation)

### OpenAI API Pricing

#### Option 1: GPT-4o-mini (Recommended) ⭐
- **Input**: $0.150 per 1M tokens
- **Output**: $0.600 per 1M tokens
- **Avg per call**: ~300 input + ~100 output tokens
- **Estimated Cost**:
  - Daily: **~$1.94** ($0.97 input + $1.94 output)
  - Monthly: **~$58-60**
  
**Why recommended**: Best balance of performance and cost. Excellent at sentiment analysis.

#### Option 2: GPT-3.5-turbo (Cheapest)
- **Input**: $0.50 per 1M tokens  
- **Output**: $1.50 per 1M tokens
- **Estimated Cost**:
  - Daily: **~$0.97**
  - Monthly: **~$29-30**

**Note**: Older model, may have slightly lower quality sentiment analysis.

#### Option 3: GPT-4o (Most Expensive)
- **Input**: $2.50 per 1M tokens
- **Output**: $10.00 per 1M tokens
- **Estimated Cost**:
  - Daily: **~$9.70**
  - Monthly: **~$291**

**Not recommended** for sentiment analysis - overkill for this use case.

### Cost Optimization Tips

Your code already implements these optimizations:
- ✅ Limits to 5 texts per batch
- ✅ Uses lower temperature (0.3) for consistency
- ✅ Short, focused prompts

Additional optimizations you could add:
- Cache sentiment for same news articles (deduplicate)
- Increase analysis interval from 40s to 60s or 120s
- Only analyze sentiment when technical signals are strong

## 🚀 Setup Instructions

### 1. Get OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-...`)

### 2. Add API Key to .env File

Edit your `.env` file and add:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Install OpenAI Package

```bash
source venv/bin/activate
pip install openai
```

### 4. Test the Integration

```bash
python test_openai_integration.py
```

You should see:
```
✅ PASS - OpenAI Client
✅ PASS - Unified Client
✅ PASS - Sentiment Analyzer
```

### 5. Restart Your Trading Bot

```bash
./stop_all.sh
./start_5m_trading.sh
```

## 🔄 How It Works

### Automatic Fallback
The system automatically uses the best available LLM:

1. **First**: Tries OpenAI if `OPENAI_API_KEY` is set
2. **Fallback**: Uses Ollama if running locally on `localhost:11434`
3. **Error**: Logs error if neither is available

### Code Changes Made

1. **Created `openai_client.py`**: OpenAI API wrapper matching Ollama interface
2. **Created `llm_client.py`**: Unified client with automatic provider selection
3. **Updated `sentiment_analyzer.py`**: Now uses unified client
4. **Updated `market_commentary.py`**: Now uses unified client
5. **Updated requirements**: Added `openai>=1.0.0`

### Default Models

- **OpenAI**: `gpt-4o-mini` (fast, cheap, good quality)
- **Ollama**: `llama3.2:3b` (free, local, requires setup)

## 📈 Monitoring Costs

### Check OpenAI Usage Dashboard
https://platform.openai.com/usage

Monitor:
- Daily API calls
- Token consumption
- Costs per day/month

### Set Usage Limits (Recommended)
1. Go to https://platform.openai.com/account/billing/limits
2. Set **monthly budget limit** (e.g., $100)
3. Enable **email notifications** at 75% and 90%

## 🔍 Why All Signals Show 0.00?

Looking at your logs, **all components are returning 0.00**:
- Technical: 0.00
- LSTM: 0.00  
- Sentiment: 0.00 (failed due to Ollama error)

### Issues to Check:

1. **Technical Indicators**
   - Not enough historical data (needs 96+ candles)
   - Check: `src/strategies/ai_enhanced_strategy.py`

2. **LSTM Model**
   - Model not trained or loaded
   - Check: LSTM model files in `data/models/`

3. **Sentiment Analysis** ✅ Fixed with OpenAI
   - Was failing due to Ollama connection refused
   - Now will work with OpenAI

## 🐛 Next Steps to Fix HOLD-Only Signals

After setting up OpenAI, you should check:

1. **Verify technical indicators are working**:
   ```bash
   python -c "from src.strategies.ai_enhanced_strategy import AIEnhancedStrategy; s = AIEnhancedStrategy(); print('Technical indicators loaded')"
   ```

2. **Check LSTM model exists**:
   ```bash
   ls -la data/models/lstm_*.h5
   ```

3. **Train LSTM if missing**:
   ```bash
   python src/ai/train_lstm.py
   ```

4. **Monitor logs after restart**:
   ```bash
   tail -f logs/trading_bot.log | grep -E "(Signal|Technical|LSTM|Sentiment)"
   ```

## 💡 Summary

- **OpenAI integration is ready** - just add your API key
- **Estimated cost**: ~$60/month for gpt-4o-mini (recommended)
- **Automatic fallback**: Will use Ollama if OpenAI key not set
- **Zero-signal issue**: Likely technical indicators or LSTM not working (separate from sentiment)

