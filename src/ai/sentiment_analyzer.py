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
        for text in texts[:5]:  # Limit to 5 texts to avoid rate limits and speed up
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
