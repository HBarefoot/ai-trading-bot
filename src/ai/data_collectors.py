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
