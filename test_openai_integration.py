#!/usr/bin/env python3
"""
Test OpenAI Integration
Verify that OpenAI API is working correctly
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_openai_client():
    """Test OpenAI client directly"""
    print("=" * 60)
    print("Testing OpenAI Client")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        return False
    
    print(f"✓ API Key found: {api_key[:20]}...")
    
    try:
        from ai.openai_client import get_openai_client
        client = get_openai_client()
        
        if not client:
            print("❌ Failed to create OpenAI client")
            return False
        
        print("✓ OpenAI client created")
        
        # Test availability
        if client.is_available():
            print("✓ OpenAI API is available")
        else:
            print("❌ OpenAI API is not available")
            return False
        
        # Test generation
        print("\nTesting text generation...")
        response = client.generate(
            prompt="What is Bitcoin?",
            system="You are a helpful assistant. Answer in one sentence.",
            temperature=0.7,
            max_tokens=50
        )
        
        if response:
            print(f"✓ Generation successful: {response[:100]}...")
        else:
            print("❌ Generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_unified_client():
    """Test unified LLM client"""
    print("\n" + "=" * 60)
    print("Testing Unified LLM Client")
    print("=" * 60)
    
    try:
        from ai.llm_client import llm_client
        
        provider = llm_client.get_provider()
        print(f"✓ Using provider: {provider}")
        
        if not llm_client.is_available():
            print("❌ LLM client not available")
            return False
        
        print("✓ LLM client is available")
        
        # Test generation
        print("\nTesting unified client generation...")
        response = llm_client.generate(
            prompt="Explain Ethereum in one sentence.",
            system="You are a crypto expert.",
            temperature=0.7
        )
        
        if response:
            print(f"✓ Generation successful: {response[:100]}...")
        else:
            print("❌ Generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_sentiment_analyzer():
    """Test sentiment analyzer with OpenAI"""
    print("\n" + "=" * 60)
    print("Testing Sentiment Analyzer")
    print("=" * 60)
    
    try:
        from ai.sentiment_analyzer import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        print("✓ Sentiment analyzer created")
        
        # Test analysis
        print("\nAnalyzing test text...")
        result = analyzer.analyze_text(
            text="Bitcoin surges past $90,000 as institutional adoption accelerates",
            symbol="BTC"
        )
        
        if result:
            print(f"✓ Sentiment: {result.sentiment:.2f}")
            print(f"✓ Confidence: {result.confidence:.2f}")
            print(f"✓ Reason: {result.reason}")
        else:
            print("❌ Sentiment analysis failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🧪 OpenAI Integration Tests\n")
    
    results = {
        "OpenAI Client": test_openai_client(),
        "Unified Client": test_unified_client(),
        "Sentiment Analyzer": test_sentiment_analyzer()
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All tests passed! OpenAI integration is working.")
    else:
        print("\n❌ Some tests failed. Check the output above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
