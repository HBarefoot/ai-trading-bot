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
    """Generate natural language market commentary using LLM"""
    
    def __init__(self, model: str = "llama3.2:3b"):  # Changed from llama3.1:latest to faster model
        self.client = ollama_client
        self.model = model
    
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
        ]) if top_performers else "- No significant movements"
        
        sentiment_text = "\n".join([
            f"- {symbol}: {score:+.2f}"
            for symbol, score in market_sentiment.items()
        ]) if market_sentiment else "- Sentiment data unavailable"
        
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
        ]) if positions else "- No open positions"
        
        volatility_text = "\n".join([
            f"- {symbol}: {vol:.2f}%"
            for symbol, vol in market_volatility.items()
        ]) if market_volatility else "- Volatility data unavailable"
        
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
