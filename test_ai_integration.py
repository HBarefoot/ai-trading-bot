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
    print("\n📰 Testing news collection...")
    news = news_collector.collect_headlines("BTC", hours=24, max_results=5)
    print(f"   Collected {len(news)} news headlines")
    for i, headline in enumerate(news[:3], 1):
        print(f"   {i}. {headline}")
    
    # Test Reddit
    print("\n💬 Testing Reddit collection...")
    posts = reddit_collector.collect_posts("BTC", hours=24, max_results=5)
    print(f"   Collected {len(posts)} Reddit posts")
    for i, post in enumerate(posts[:3], 1):
        print(f"   {i}. {post[:100]}...")

def test_commentary():
    """Test market commentary"""
    print("\n" + "="*60)
    print("Testing Market Commentary")
    print("="*60)
    
    # Test trade explanation
    print("\n💡 Generating trade explanation...")
    explanation = market_commentary.explain_trade(
        symbol="BTC",
        action="BUY",
        price=35000.0,
        technical_signal=0.8,
        sentiment_signal=0.6,
        lstm_signal=0.3
    )
    print(f"\n{explanation}")

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
