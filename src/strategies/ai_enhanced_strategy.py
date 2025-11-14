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
        # Placeholder for now - add small random signal for testing
        # In Phase 3, we'll integrate the actual LSTM model
        import random
        return random.uniform(-0.2, 0.2)  # Small random signal for testing
    
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
            
            # Apply threshold (reduced for better signal detection)
            if combined > 0.3:  # Reduced from 0.6 for more sensitive detection
                combined_signals.iloc[i] = 1.0  # Strong BUY
            elif combined < -0.3:  # Reduced from -0.6 for more sensitive detection
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
