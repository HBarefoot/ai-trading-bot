# 🤖 AI Integration with Ollama - Implementation Prompt

**Date:** November 6, 2025  
**Current Status:** Phase 4 Complete, AI predictions not integrated  
**Ollama Version:** 0.12.10 (installed and ready)  
**Objective:** Integrate local LLMs via Ollama for sentiment analysis, market commentary, and advanced predictions

---

## 📊 Current State Analysis

### ✅ What's Working Now

**Trading System Uses:**
1. **Technical Indicators Only** - Trading decisions based on:
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Moving Averages (8, 21, 50 period)
   - Bollinger Bands
   - Volume analysis

2. **Strategy Signal Generation** (`src/strategies/phase2_final_test.py`):
   ```python
   def generate_signals(self, data: pd.DataFrame) -> pd.Series:
       # Uses MA crossover + RSI confirmation
       # Returns: 1.0 (BUY), -1.0 (SELL), 0.0 (HOLD)
   ```

3. **Live Trading Engine** (`src/trading/live_engine.py`):
   ```python
   # Line 266: Generates signals using strategy
   signals = self.strategy.generate_signals(df)
   latest_signal = signals.iloc[-1]
   
   # Line 274-277: Executes trades based on signals
   if latest_signal > 0:  # BUY signal
       await self.execute_buy(symbol, current_price)
   elif latest_signal < 0:  # SELL signal
       await self.execute_sell(symbol, current_price)
   ```

### ❌ What's NOT Being Used

**AI/ML Predictions:**
- LSTM model exists (`src/ml/lstm_model.py`) but **NOT integrated** into trading
- API endpoint `/api/predictions/{symbol}` returns placeholder data
- No sentiment analysis
- No news/social media analysis
- No LLM-based insights

**Answer to your question:**
> **Does the current web app use AI results to place orders?**  
> **NO** - Orders are placed based purely on technical indicators (RSI + Moving Averages).  
> The LSTM model exists but is not connected to the trading engine.

---

## 🎯 Implementation Goals

### Phase 1: Sentiment Analysis (Week 1-2)
1. Collect data from Twitter, Reddit, and news
2. Use Ollama with local LLMs for sentiment analysis
3. Generate sentiment scores for each cryptocurrency
4. Integrate sentiment into trading signals

### Phase 2: Market Commentary (Week 2-3)
1. Generate natural language explanations for trades
2. Create daily market summaries
3. Provide risk assessments in plain English
4. Add AI insights to dashboard

### Phase 3: Advanced Predictions (Week 3-4)
1. Integrate LSTM predictions into trading signals
2. Add Transformer models for price prediction
3. Create ensemble model (Technical + LSTM + Sentiment)
4. Implement attention mechanisms

---

## 🏗️ Architecture Design

### New AI Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                   DATA COLLECTION LAYER                      │
├─────────────────────────────────────────────────────────────┤
│  Twitter API  │  Reddit API  │  News RSS  │  Price Data    │
└────────┬────────────┬────────────┬─────────────┬────────────┘
         │            │            │             │
         ▼            ▼            ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI PROCESSING LAYER                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Sentiment  │  │    LSTM      │  │  Technical   │       │
│  │  Analysis   │  │  Predictor   │  │  Indicators  │       │
│  │  (Ollama)   │  │ (TensorFlow) │  │   (Pandas)   │       │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                │                  │               │
│         └────────────────┼──────────────────┘               │
│                          ▼                                  │
│                 ┌─────────────────┐                         │
│                 │  Signal Fusion  │                         │
│                 │   Weighted      │                         │
│                 │  Combination    │                         │
│                 └────────┬────────┘                         │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  TRADING DECISION LAYER                      │
├─────────────────────────────────────────────────────────────┤
│  Final Signal = (0.4 × Technical) + (0.3 × LSTM) +          │
│                 (0.3 × Sentiment)                            │
│                                                               │
│  if Final Signal > 0.6: BUY                                  │
│  if Final Signal < -0.6: SELL                                │
│  else: HOLD                                                  │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
                  Live Trading Engine
```

---

## 📝 Implementation Steps

## STEP 1: Ollama Setup & Testing (Day 1)

### 1.1 Install Ollama Models

```bash
# Pull recommended models for different tasks
ollama pull llama3.2:3b          # Fast, efficient for sentiment
ollama pull mistral:7b           # Good for analysis
ollama pull qwen2.5:14b          # Best for complex reasoning
ollama pull nomic-embed-text     # For embeddings

# Test models
ollama run llama3.2:3b "What is sentiment analysis?"
```

### 1.2 Create Ollama Integration Module

**Create:** `src/ai/ollama_client.py`

```python
"""
Ollama LLM Integration
Local LLM client for sentiment analysis and market commentary
"""
import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama local LLMs"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.2:3b",
        timeout: int = 30
    ):
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout
        
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        Generate text using Ollama
        
        Args:
            prompt: User prompt
            model: Model name (default: llama3.2:3b)
            system: System prompt for instructions
            temperature: Sampling temperature (0.0-1.0)
            stream: Stream response
            
        Returns:
            Generated text
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": stream
        }
        
        if system:
            payload["system"] = system
            
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Ollama generate error: {e}")
            return ""
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Chat completion with conversation history
        
        Args:
            messages: List of {"role": "user/assistant", "content": "text"}
            model: Model name
            temperature: Sampling temperature
            
        Returns:
            Assistant's response
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return ""
    
    def get_embedding(
        self,
        text: str,
        model: str = "nomic-embed-text"
    ) -> List[float]:
        """Get text embedding for similarity search"""
        payload = {
            "model": model,
            "prompt": text
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("embedding", [])
            
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []


# Global instance
ollama_client = OllamaClient()
```

---

## STEP 2: Sentiment Analysis Module (Day 2-3)

### 2.1 Create Sentiment Analyzer

**Create:** `src/ai/sentiment_analyzer.py`

```python
"""
Crypto Sentiment Analysis using Ollama
Analyzes sentiment from news, social media, and market commentary
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import json
import re

from ai.ollama_client import ollama_client

logger = logging.getLogger(__name__)

@dataclass
class SentimentScore:
    """Sentiment analysis result"""
    symbol: str
    sentiment: float  # -1.0 (bearish) to +1.0 (bullish)
    confidence: float  # 0.0 to 1.0
    reason: str
    sources: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "sentiment": self.sentiment,
            "confidence": self.confidence,
            "reason": self.reason,
            "sources": self.sources,
            "timestamp": self.timestamp.isoformat()
        }


class SentimentAnalyzer:
    """Analyzes sentiment for cryptocurrency markets"""
    
    def __init__(self, model: str = "llama3.2:3b"):
        self.model = model
        self.client = ollama_client
        
        # System prompt for sentiment analysis
        self.sentiment_system_prompt = """You are a cryptocurrency market sentiment analyst.
Analyze the given text and determine if it's BULLISH, BEARISH, or NEUTRAL for the mentioned cryptocurrency.

Rules:
1. Return ONLY a JSON object with: {"sentiment": "BULLISH/BEARISH/NEUTRAL", "confidence": 0-100, "reason": "brief explanation"}
2. Consider: price movements, adoption news, regulations, technical developments, market sentiment
3. Be objective and avoid bias
4. Higher confidence (closer to 100) means stronger conviction

Example:
Input: "Bitcoin surges past $40k as institutional adoption increases"
Output: {"sentiment": "BULLISH", "confidence": 85, "reason": "Strong price movement + positive adoption narrative"}
"""
    
    def analyze_text(
        self,
        text: str,
        symbol: str
    ) -> Optional[SentimentScore]:
        """
        Analyze sentiment of a single text
        
        Args:
            text: Text to analyze (tweet, headline, comment)
            symbol: Cryptocurrency symbol (BTC, ETH, etc.)
            
        Returns:
            SentimentScore object
        """
        if not text or len(text) < 10:
            return None
            
        # Create prompt
        prompt = f"Analyze sentiment for {symbol}:\n\n{text}"
        
        try:
            # Get sentiment from LLM
            response = self.client.generate(
                prompt=prompt,
                system=self.sentiment_system_prompt,
                model=self.model,
                temperature=0.3  # Lower temp for more consistent results
            )
            
            # Parse JSON response
            # Extract JSON from response (LLM might add extra text)
            json_match = re.search(r'\{[^}]+\}', response)
            if not json_match:
                logger.warning(f"No JSON found in response: {response}")
                return None
                
            result = json.loads(json_match.group())
            
            # Convert to SentimentScore
            sentiment_map = {
                "BULLISH": 1.0,
                "BEARISH": -1.0,
                "NEUTRAL": 0.0
            }
            
            sentiment_value = sentiment_map.get(
                result.get("sentiment", "NEUTRAL"),
                0.0
            )
            
            confidence = float(result.get("confidence", 50)) / 100.0
            reason = result.get("reason", "Unknown")
            
            return SentimentScore(
                symbol=symbol,
                sentiment=sentiment_value,
                confidence=confidence,
                reason=reason,
                sources=[text[:100]],  # Store first 100 chars
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return None
    
    def analyze_batch(
        self,
        texts: List[str],
        symbol: str
    ) -> Optional[SentimentScore]:
        """
        Analyze multiple texts and aggregate sentiment
        
        Args:
            texts: List of texts to analyze
            symbol: Cryptocurrency symbol
            
        Returns:
            Aggregated SentimentScore
        """
        if not texts:
            return None
            
        scores = []
        for text in texts[:20]:  # Limit to 20 texts to avoid rate limits
            score = self.analyze_text(text, symbol)
            if score:
                scores.append(score)
        
        if not scores:
            return None
        
        # Aggregate sentiments (weighted by confidence)
        total_weight = sum(s.confidence for s in scores)
        if total_weight == 0:
            return None
            
        weighted_sentiment = sum(
            s.sentiment * s.confidence for s in scores
        ) / total_weight
        
        avg_confidence = np.mean([s.confidence for s in scores])
        
        # Combine reasons
        reasons = [s.reason for s in scores[:3]]  # Top 3 reasons
        combined_reason = " | ".join(reasons)
        
        return SentimentScore(
            symbol=symbol,
            sentiment=weighted_sentiment,
            confidence=avg_confidence,
            reason=combined_reason,
            sources=[s.sources[0] for s in scores[:5]],
            timestamp=datetime.now()
        )
    
    def get_market_sentiment(
        self,
        symbol: str,
        news_headlines: List[str] = None,
        tweets: List[str] = None,
        reddit_posts: List[str] = None
    ) -> Optional[SentimentScore]:
        """
        Get overall market sentiment from multiple sources
        
        Args:
            symbol: Cryptocurrency symbol
            news_headlines: List of news headlines
            tweets: List of tweets
            reddit_posts: List of Reddit posts
            
        Returns:
            Aggregated SentimentScore
        """
        all_texts = []
        
        if news_headlines:
            all_texts.extend(news_headlines)
        if tweets:
            all_texts.extend(tweets)
        if reddit_posts:
            all_texts.extend(reddit_posts)
        
        if not all_texts:
            logger.warning(f"No texts provided for {symbol} sentiment analysis")
            return None
        
        return self.analyze_batch(all_texts, symbol)


# Global instance
sentiment_analyzer = SentimentAnalyzer()
```

### 2.2 Create Data Collectors

**Create:** `src/ai/data_collectors.py`

```python
"""
Data collectors for sentiment analysis
Collects data from Twitter, Reddit, news, etc.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import feedparser
import time

logger = logging.getLogger(__name__)

class NewsCollector:
    """Collect crypto news from RSS feeds"""
    
    def __init__(self):
        # Free crypto news RSS feeds
        self.feeds = [
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed",
            "https://cryptonews.com/news/feed/",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
        ]
    
    def collect_headlines(
        self,
        symbol: str,
        hours: int = 24,
        max_results: int = 20
    ) -> List[str]:
        """
        Collect recent news headlines mentioning the symbol
        
        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)
            hours: Look back period in hours
            max_results: Maximum number of headlines
            
        Returns:
            List of headlines
        """
        headlines = []
        symbol_keywords = {
            "BTC": ["bitcoin", "btc"],
            "ETH": ["ethereum", "eth", "ether"],
            "SOL": ["solana", "sol"],
            "ADA": ["cardano", "ada"],
            "DOT": ["polkadot", "dot"]
        }
        
        keywords = symbol_keywords.get(symbol, [symbol.lower()])
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Check if headline mentions symbol
                    title = entry.get("title", "").lower()
                    if any(kw in title for kw in keywords):
                        # Check recency
                        pub_date = entry.get("published_parsed")
                        if pub_date:
                            pub_datetime = datetime(*pub_date[:6])
                            if pub_datetime > cutoff_time:
                                headlines.append(entry.get("title", ""))
                
                if len(headlines) >= max_results:
                    break
                    
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error collecting from {feed_url}: {e}")
        
        return headlines[:max_results]


class RedditCollector:
    """Collect Reddit posts (using free Reddit API)"""
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.subreddits = [
            "CryptoCurrency",
            "Bitcoin",
            "ethereum",
            "CryptoMarkets"
        ]
    
    def collect_posts(
        self,
        symbol: str,
        hours: int = 24,
        max_results: int = 20
    ) -> List[str]:
        """
        Collect recent Reddit posts mentioning symbol
        
        Args:
            symbol: Crypto symbol
            hours: Look back period
            max_results: Maximum posts
            
        Returns:
            List of post titles + snippets
        """
        posts = []
        symbol_keywords = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "ADA": "cardano",
            "DOT": "polkadot"
        }
        
        keyword = symbol_keywords.get(symbol, symbol.lower())
        
        for subreddit in self.subreddits:
            try:
                # Use Reddit's JSON API (no auth needed for reading)
                url = f"{self.base_url}/r/{subreddit}/search.json"
                params = {
                    "q": keyword,
                    "sort": "new",
                    "limit": 10,
                    "t": "day"
                }
                
                headers = {"User-Agent": "CryptoTradingBot/1.0"}
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for post in data.get("data", {}).get("children", []):
                        post_data = post.get("data", {})
                        title = post_data.get("title", "")
                        selftext = post_data.get("selftext", "")[:200]
                        
                        combined = f"{title}. {selftext}"
                        posts.append(combined)
                
                if len(posts) >= max_results:
                    break
                    
                time.sleep(2)  # Reddit rate limit
                
            except Exception as e:
                logger.error(f"Error collecting from r/{subreddit}: {e}")
        
        return posts[:max_results]


class TwitterCollector:
    """Collect tweets (requires Twitter API - optional)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # Twitter API v2 would go here if you have credentials
        # For now, we'll use a mock collector
    
    def collect_tweets(
        self,
        symbol: str,
        hours: int = 24,
        max_results: int = 20
    ) -> List[str]:
        """
        Collect recent tweets mentioning symbol
        (Currently returns empty - requires Twitter API credentials)
        """
        if not self.api_key:
            logger.info("Twitter API key not configured, skipping tweets")
            return []
        
        # TODO: Implement Twitter API v2 integration
        # This would require:
        # 1. Twitter Developer account
        # 2. API credentials in .env
        # 3. tweepy library integration
        
        return []


# Global collectors
news_collector = NewsCollector()
reddit_collector = RedditCollector()
twitter_collector = TwitterCollector()
```

---

## STEP 3: Enhanced Strategy with AI (Day 4-5)

### 3.1 Create AI-Enhanced Strategy

**Create:** `src/strategies/ai_enhanced_strategy.py`

```python
"""
AI-Enhanced Trading Strategy
Combines technical indicators + LSTM predictions + sentiment analysis
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

from strategies.technical_indicators import TechnicalIndicators
from strategies.phase2_final_test import OptimizedPhase2Strategy
from ai.sentiment_analyzer import sentiment_analyzer
from ai.data_collectors import news_collector, reddit_collector

logger = logging.getLogger(__name__)

class AIEnhancedStrategy:
    """
    Trading strategy that combines:
    1. Technical indicators (40% weight)
    2. LSTM predictions (30% weight) - TODO: integrate
    3. Sentiment analysis (30% weight)
    """
    
    def __init__(
        self,
        technical_weight: float = 0.4,
        lstm_weight: float = 0.3,
        sentiment_weight: float = 0.3
    ):
        self.name = "AI Enhanced Strategy"
        
        # Weights for signal fusion
        self.technical_weight = technical_weight
        self.lstm_weight = lstm_weight
        self.sentiment_weight = sentiment_weight
        
        # Component strategies
        self.technical_strategy = OptimizedPhase2Strategy()
        self.indicators = TechnicalIndicators()
        
        # Cache for sentiment (refresh every 1 hour)
        self.sentiment_cache: Dict[str, Tuple[float, datetime]] = {}
        self.cache_ttl = 3600  # 1 hour in seconds
    
    def get_sentiment_signal(self, symbol: str) -> float:
        """
        Get sentiment signal for a symbol
        
        Returns:
            Float between -1.0 (bearish) and 1.0 (bullish)
        """
        # Check cache
        if symbol in self.sentiment_cache:
            cached_sentiment, cache_time = self.sentiment_cache[symbol]
            age = (datetime.now() - cache_time).total_seconds()
            if age < self.cache_ttl:
                logger.info(f"Using cached sentiment for {symbol}: {cached_sentiment:.2f}")
                return cached_sentiment
        
        try:
            # Collect data from sources
            logger.info(f"Collecting sentiment data for {symbol}...")
            
            news_headlines = news_collector.collect_headlines(symbol, hours=24, max_results=10)
            reddit_posts = reddit_collector.collect_posts(symbol, hours=24, max_results=10)
            
            logger.info(f"Collected {len(news_headlines)} news + {len(reddit_posts)} reddit posts")
            
            if not news_headlines and not reddit_posts:
                logger.warning(f"No data collected for {symbol}, using neutral sentiment")
                return 0.0
            
            # Analyze sentiment
            sentiment_score = sentiment_analyzer.get_market_sentiment(
                symbol=symbol,
                news_headlines=news_headlines,
                reddit_posts=reddit_posts
            )
            
            if sentiment_score:
                # Adjust by confidence
                adjusted_sentiment = sentiment_score.sentiment * sentiment_score.confidence
                
                logger.info(f"Sentiment for {symbol}: {adjusted_sentiment:.2f} "
                          f"(confidence: {sentiment_score.confidence:.2f})")
                logger.info(f"Reason: {sentiment_score.reason}")
                
                # Cache result
                self.sentiment_cache[symbol] = (adjusted_sentiment, datetime.now())
                
                return adjusted_sentiment
            else:
                logger.warning(f"Sentiment analysis failed for {symbol}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting sentiment for {symbol}: {e}")
            return 0.0
    
    def get_lstm_signal(self, data: pd.DataFrame, symbol: str) -> float:
        """
        Get LSTM prediction signal
        
        Returns:
            Float between -1.0 and 1.0
        
        TODO: Integrate LSTM model predictions
        """
        # Placeholder for now
        # In Phase 3, we'll integrate the actual LSTM model
        return 0.0
    
    def generate_signals(self, data: pd.DataFrame, symbol: str = "BTC") -> pd.Series:
        """
        Generate AI-enhanced trading signals
        
        Args:
            data: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            Series of signals: 1.0 (BUY), -1.0 (SELL), 0.0 (HOLD)
        """
        # 1. Get technical indicator signals
        technical_signals = self.technical_strategy.generate_signals(data)
        
        # 2. Get sentiment signal (same for all timestamps in this batch)
        sentiment_signal = self.get_sentiment_signal(symbol)
        
        # 3. Get LSTM signal (placeholder for now)
        lstm_signal = self.get_lstm_signal(data, symbol)
        
        # 4. Combine signals with weights
        combined_signals = pd.Series(index=data.index, dtype=float)
        
        for i in range(len(data)):
            # Weighted average of all signals
            combined = (
                self.technical_weight * technical_signals.iloc[i] +
                self.lstm_weight * lstm_signal +
                self.sentiment_weight * sentiment_signal
            )
            
            # Apply threshold (need stronger signal to trade)
            if combined > 0.6:
                combined_signals.iloc[i] = 1.0  # Strong BUY
            elif combined < -0.6:
                combined_signals.iloc[i] = -1.0  # Strong SELL
            else:
                combined_signals.iloc[i] = 0.0  # HOLD
        
        # Log signal breakdown for latest point
        latest_idx = len(data) - 1
        logger.info(f"\n{'='*60}")
        logger.info(f"Signal Breakdown for {symbol}:")
        logger.info(f"  Technical: {technical_signals.iloc[latest_idx]:.2f} "
                   f"(weight: {self.technical_weight})")
        logger.info(f"  LSTM:      {lstm_signal:.2f} "
                   f"(weight: {self.lstm_weight})")
        logger.info(f"  Sentiment: {sentiment_signal:.2f} "
                   f"(weight: {self.sentiment_weight})")
        logger.info(f"  Final:     {combined_signals.iloc[latest_idx]:.2f}")
        logger.info(f"{'='*60}\n")
        
        return combined_signals
```

### 3.2 Update Trading Engine to Use AI Strategy

**Edit:** `src/trading/live_engine.py`

Add at top of file (after imports):
```python
from strategies.ai_enhanced_strategy import AIEnhancedStrategy
```

In `LiveTradingEngine.__init__`, change strategy initialization:
```python
def __init__(
    self,
    symbols: List[str] = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
    initial_balance: float = 10000.0,
    use_ai_strategy: bool = True  # NEW PARAMETER
):
    # ... existing code ...
    
    # Strategy selection
    if use_ai_strategy:
        self.strategy = AIEnhancedStrategy()
        logger.info("Using AI-Enhanced Strategy")
    else:
        self.strategy = OptimizedPhase2Strategy()
        logger.info("Using Technical-Only Strategy")
```

In `process_symbol` method, pass symbol to strategy:
```python
# Line ~266, change from:
signals = self.strategy.generate_signals(df)

# To:
# Extract base symbol (remove /USDT)
base_symbol = symbol.split('/')[0]
signals = self.strategy.generate_signals(df, symbol=base_symbol)
```

---

## STEP 4: Market Commentary (Day 6-7)

### 4.1 Create Commentary Generator

**Create:** `src/ai/market_commentary.py`

```python
"""
Market Commentary Generator using Ollama
Generates natural language explanations and insights
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from ai.ollama_client import ollama_client

logger = logging.getLogger(__name__)

class MarketCommentary:
    """Generate natural language market commentary"""
    
    def __init__(self, model: str = "mistral:7b"):
        self.model = model
        self.client = ollama_client
    
    def explain_trade(
        self,
        symbol: str,
        action: str,  # BUY or SELL
        price: float,
        technical_signal: float,
        sentiment_signal: float,
        lstm_signal: float = 0.0,
        reason: str = ""
    ) -> str:
        """
        Generate explanation for a trade decision
        
        Returns:
            Natural language explanation
        """
        system_prompt = """You are a cryptocurrency trading analyst.
Explain trading decisions in clear, concise language (2-3 sentences).
Focus on the key factors driving the decision.
Be professional but accessible."""

        prompt = f"""Explain this trade decision:

Symbol: {symbol}
Action: {action}
Price: ${price:,.2f}
Technical Signal: {technical_signal:.2f}
Sentiment Signal: {sentiment_signal:.2f}
LSTM Prediction: {lstm_signal:.2f}

{f'Context: {reason}' if reason else ''}

Provide a brief explanation (2-3 sentences) of why this trade was made."""

        try:
            response = self.client.generate(
                prompt=prompt,
                system=system_prompt,
                model=self.model,
                temperature=0.7
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating trade explanation: {e}")
            return f"{action} {symbol} at ${price:,.2f} based on combined signals."
    
    def generate_daily_summary(
        self,
        portfolio_value: float,
        daily_pnl: float,
        daily_pnl_pct: float,
        trades_today: int,
        top_performers: List[Dict],
        market_sentiment: Dict[str, float]
    ) -> str:
        """
        Generate daily market summary
        
        Returns:
            Daily summary text
        """
        system_prompt = """You are a cryptocurrency portfolio manager.
Generate a concise daily summary (3-4 sentences) covering:
1. Overall portfolio performance
2. Key trades and decisions
3. Market sentiment
4. Outlook for tomorrow

Be professional, factual, and actionable."""

        # Format data for prompt
        performers_text = "\n".join([
            f"- {p['symbol']}: {p['pnl_pct']:+.2f}%"
            for p in top_performers[:3]
        ])
        
        sentiment_text = "\n".join([
            f"- {symbol}: {score:+.2f}"
            for symbol, score in market_sentiment.items()
        ])
        
        prompt = f"""Generate a daily trading summary:

Portfolio:
- Total Value: ${portfolio_value:,.2f}
- Daily P&L: ${daily_pnl:+,.2f} ({daily_pnl_pct:+.2f}%)
- Trades Today: {trades_today}

Top Performers:
{performers_text}

Market Sentiment:
{sentiment_text}

Write a professional daily summary."""

        try:
            response = self.client.generate(
                prompt=prompt,
                system=system_prompt,
                model=self.model,
                temperature=0.7
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return f"Portfolio: ${portfolio_value:,.2f} | Daily P&L: {daily_pnl_pct:+.2f}%"
    
    def assess_risk(
        self,
        portfolio_value: float,
        positions: List[Dict],
        market_volatility: Dict[str, float],
        max_drawdown: float
    ) -> str:
        """
        Generate risk assessment
        
        Returns:
            Risk assessment text
        """
        system_prompt = """You are a risk management analyst.
Assess the current portfolio risk and provide actionable recommendations.
Be specific about risks and mitigation strategies.
Format: Risk Level, Key Risks (bullet points), Recommendations (bullet points)."""

        positions_text = "\n".join([
            f"- {p['symbol']}: ${p['value']:,.2f} ({p['pct_of_portfolio']:.1f}%)"
            for p in positions
        ])
        
        volatility_text = "\n".join([
            f"- {symbol}: {vol:.2f}%"
            for symbol, vol in market_volatility.items()
        ])
        
        prompt = f"""Assess portfolio risk:

Portfolio Value: ${portfolio_value:,.2f}
Max Drawdown: {max_drawdown:.2f}%

Current Positions:
{positions_text}

Market Volatility (30-day):
{volatility_text}

Provide risk assessment with recommendations."""

        try:
            response = self.client.generate(
                prompt=prompt,
                system=system_prompt,
                model=self.model,
                temperature=0.6
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating risk assessment: {e}")
            return "Risk assessment unavailable."


# Global instance
market_commentary = MarketCommentary()
```

---

## STEP 5: Dashboard Integration (Day 8-9)

### 5.1 Update API Backend

**Edit:** `src/api/api_backend.py`

Add new endpoints for AI features:

```python
from ai.sentiment_analyzer import sentiment_analyzer
from ai.data_collectors import news_collector, reddit_collector
from ai.market_commentary import market_commentary

@app.get("/api/ai/sentiment/{symbol}")
async def get_ai_sentiment(symbol: str):
    """Get AI sentiment analysis for symbol"""
    try:
        # Collect data
        news = news_collector.collect_headlines(symbol, hours=24, max_results=10)
        reddit = reddit_collector.collect_posts(symbol, hours=24, max_results=10)
        
        # Analyze sentiment
        sentiment = sentiment_analyzer.get_market_sentiment(
            symbol=symbol,
            news_headlines=news,
            reddit_posts=reddit
        )
        
        if sentiment:
            return sentiment.to_dict()
        else:
            return {
                "symbol": symbol,
                "sentiment": 0.0,
                "confidence": 0.0,
                "reason": "No data available",
                "sources": [],
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Sentiment API error: {e}")
        return {"error": str(e)}

@app.get("/api/ai/commentary/daily")
async def get_daily_commentary():
    """Get AI-generated daily market summary"""
    try:
        # Get portfolio data
        # ... (use existing portfolio logic)
        
        commentary = market_commentary.generate_daily_summary(
            portfolio_value=10000.0,  # Get from DB
            daily_pnl=100.0,
            daily_pnl_pct=1.0,
            trades_today=5,
            top_performers=[],
            market_sentiment={}
        )
        
        return {
            "commentary": commentary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Commentary API error: {e}")
        return {"error": str(e)}

@app.post("/api/ai/explain-trade")
async def explain_trade(trade_data: dict):
    """Get AI explanation for a trade"""
    try:
        explanation = market_commentary.explain_trade(
            symbol=trade_data["symbol"],
            action=trade_data["action"],
            price=trade_data["price"],
            technical_signal=trade_data.get("technical_signal", 0.0),
            sentiment_signal=trade_data.get("sentiment_signal", 0.0),
            lstm_signal=trade_data.get("lstm_signal", 0.0)
        )
        
        return {
            "explanation": explanation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Explain trade API error: {e}")
        return {"error": str(e)}
```

### 5.2 Update Dashboard AI Insights Tab

**Edit:** `src/frontend/dashboard.py`

Replace the placeholder `render_ai_insights_tab` method:

```python
def render_ai_insights_tab(self):
    """AI-powered insights and predictions"""
    st.header("🤖 AI Insights")
    
    # Sentiment Analysis Section
    st.subheader("📊 Market Sentiment Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        symbol = st.selectbox(
            "Select Symbol",
            ["BTC", "ETH", "SOL", "ADA", "DOT"],
            key="sentiment_symbol"
        )
    
    with col2:
        if st.button("🔄 Refresh Sentiment", key="refresh_sentiment"):
            st.session_state.sentiment_cache = {}
    
    # Get sentiment
    sentiment_data = self.fetch_ai_sentiment(symbol)
    
    if sentiment_data and "sentiment" in sentiment_data:
        # Display sentiment gauge
        sentiment_value = sentiment_data["sentiment"]
        confidence = sentiment_data["confidence"]
        
        # Color based on sentiment
        if sentiment_value > 0.3:
            color = "🟢"
            label = "BULLISH"
        elif sentiment_value < -0.3:
            color = "🔴"
            label = "BEARISH"
        else:
            color = "🟡"
            label = "NEUTRAL"
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Sentiment", f"{color} {label}")
        col2.metric("Score", f"{sentiment_value:+.2f}")
        col3.metric("Confidence", f"{confidence:.0%}")
        
        # Reason
        st.info(f"**Analysis:** {sentiment_data.get('reason', 'N/A')}")
        
        # Sources
        if sentiment_data.get("sources"):
            with st.expander("📰 View Sources"):
                for i, source in enumerate(sentiment_data["sources"][:5], 1):
                    st.text(f"{i}. {source}")
    
    st.divider()
    
    # Daily Commentary Section
    st.subheader("📝 Daily Market Commentary")
    
    if st.button("Generate Daily Summary", key="gen_summary"):
        with st.spinner("Generating AI commentary..."):
            commentary = self.fetch_daily_commentary()
            if commentary and "commentary" in commentary:
                st.success(commentary["commentary"])
    
    st.divider()
    
    # Trade Explanations
    st.subheader("💡 Recent Trade Explanations")
    
    recent_trades = self.fetch_trades(limit=5)
    if recent_trades:
        for trade in recent_trades:
            with st.expander(f"{trade['symbol']} - {trade['side']} @ ${trade['price']:.2f}"):
                if st.button(f"Explain this trade", key=f"explain_{trade['id']}"):
                    with st.spinner("Generating explanation..."):
                        explanation = self.explain_trade(trade)
                        if explanation:
                            st.write(explanation)

def fetch_ai_sentiment(self, symbol: str) -> Optional[Dict]:
    """Fetch AI sentiment analysis"""
    try:
        response = self.api_client.get(
            f"/api/ai/sentiment/{symbol}",
            cache_ttl=3600  # Cache for 1 hour
        )
        return response
    except Exception as e:
        logger.error(f"Error fetching sentiment: {e}")
        return None

def fetch_daily_commentary(self) -> Optional[Dict]:
    """Fetch daily AI commentary"""
    try:
        response = self.api_client.get("/api/ai/commentary/daily")
        return response
    except Exception as e:
        logger.error(f"Error fetching commentary: {e}")
        return None

def explain_trade(self, trade: Dict) -> Optional[str]:
    """Get AI explanation for a trade"""
    try:
        response = self.api_client.post("/api/ai/explain-trade", json=trade)
        return response.get("explanation") if response else None
    except Exception as e:
        logger.error(f"Error explaining trade: {e}")
        return None
```

---

## STEP 6: Testing & Validation (Day 10)

### 6.1 Test Script

**Create:** `test_ai_integration.py`

```python
#!/usr/bin/env python3
"""
Test AI Integration
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.ollama_client import ollama_client
from ai.sentiment_analyzer import sentiment_analyzer
from ai.data_collectors import news_collector, reddit_collector
from ai.market_commentary import market_commentary

def test_ollama():
    """Test Ollama connection"""
    print("\n" + "="*60)
    print("Testing Ollama Connection")
    print("="*60)
    
    if ollama_client.is_available():
        print("✅ Ollama is running")
        
        models = ollama_client.list_models()
        print(f"✅ Available models: {', '.join(models)}")
        
        # Test generation
        response = ollama_client.generate(
            "What is cryptocurrency?",
            model="llama3.2:3b"
        )
        print(f"✅ Generation test: {response[:100]}...")
    else:
        print("❌ Ollama is not running. Start with: ollama serve")
        return False
    
    return True

def test_sentiment():
    """Test sentiment analysis"""
    print("\n" + "="*60)
    print("Testing Sentiment Analysis")
    print("="*60)
    
    test_texts = [
        "Bitcoin surges past $40k as institutional adoption increases",
        "Ethereum faces regulatory challenges in Europe",
        "Solana network experiences downtime, users concerned"
    ]
    
    for text in test_texts:
        result = sentiment_analyzer.analyze_text(text, "BTC")
        if result:
            print(f"\n📝 Text: {text}")
            print(f"   Sentiment: {result.sentiment:+.2f} (confidence: {result.confidence:.2f})")
            print(f"   Reason: {result.reason}")

def test_data_collection():
    """Test data collectors"""
    print("\n" + "="*60)
    print("Testing Data Collection")
    print("="*60)
    
    # Test news
    news = news_collector.collect_headlines("BTC", hours=24, max_results=5)
    print(f"\n📰 Collected {len(news)} news headlines")
    for i, headline in enumerate(news[:3], 1):
        print(f"   {i}. {headline}")
    
    # Test Reddit
    posts = reddit_collector.collect_posts("BTC", hours=24, max_results=5)
    print(f"\n💬 Collected {len(posts)} Reddit posts")
    for i, post in enumerate(posts[:3], 1):
        print(f"   {i}. {post[:100]}...")

def test_commentary():
    """Test market commentary"""
    print("\n" + "="*60)
    print("Testing Market Commentary")
    print("="*60)
    
    # Test trade explanation
    explanation = market_commentary.explain_trade(
        symbol="BTC",
        action="BUY",
        price=35000.0,
        technical_signal=0.8,
        sentiment_signal=0.6,
        lstm_signal=0.3
    )
    print(f"\n💡 Trade Explanation:\n{explanation}")

def main():
    print("\n🤖 AI Integration Test Suite")
    print("="*60)
    
    # Test Ollama
    if not test_ollama():
        print("\n❌ Ollama test failed. Please install and start Ollama.")
        return
    
    # Test sentiment
    test_sentiment()
    
    # Test data collection
    test_data_collection()
    
    # Test commentary
    test_commentary()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()
```

Run tests:
```bash
python test_ai_integration.py
```

---

## 📊 Success Metrics

After implementation, you should have:

1. **Sentiment Analysis Working**
   - ✅ Collecting news from 4+ sources
   - ✅ Collecting Reddit posts
   - ✅ Ollama analyzing sentiment locally
   - ✅ Sentiment scores influencing trades (30% weight)

2. **Market Commentary**
   - ✅ AI explanations for every trade
   - ✅ Daily summary generation
   - ✅ Risk assessments on demand

3. **Enhanced Trading**
   - ✅ AI strategy using 3 signal sources
   - ✅ Configurable weights
   - ✅ Better decision explanations

4. **Dashboard Integration**
   - ✅ AI Insights tab functional
   - ✅ Real-time sentiment display
   - ✅ Trade explanations visible

---

## 🚀 Quick Start Commands

```bash
# 1. Install Ollama models
ollama pull llama3.2:3b
ollama pull mistral:7b
ollama pull nomic-embed-text

# 2. Install Python dependencies
pip install feedparser beautifulsoup4 requests

# 3. Test AI integration
python test_ai_integration.py

# 4. Update trading engine to use AI strategy
# Edit src/trading/live_engine.py and set use_ai_strategy=True

# 5. Restart services
./stop_all.sh
./start_api.sh
./start_dashboard.sh

# 6. Check AI Insights tab in dashboard
open http://localhost:8501
```

---

## 📝 Next Steps (Phase 3)

After completing this implementation:

1. **Integrate LSTM Predictions**
   - Load trained LSTM model
   - Get predictions in strategy
   - Add to signal fusion

2. **Add Transformer Model**
   - Implement time-series Transformer
   - Train on historical data
   - Compare with LSTM

3. **Optimize Weights**
   - Backtest different weight combinations
   - Use walk-forward optimization
   - Find best balance

4. **Enhanced Data Collection**
   - Add Twitter API (if available)
   - Add more news sources
   - Implement real-time streaming

---

**This prompt provides everything needed to integrate Ollama-based AI into your trading bot while keeping it 100% local and private!** 🚀
