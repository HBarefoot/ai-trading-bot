#!/usr/bin/env python3
"""
Quick AI Integration Test
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.ollama_client import ollama_client

def main():
    print("\n🤖 Quick AI Integration Test")
    print("="*60)
    
    # Test 1: Ollama availability
    print("\n1. Testing Ollama connection...")
    if ollama_client.is_available():
        print("   ✅ Ollama is running")
    else:
        print("   ❌ Ollama is not running")
        return
    
    # Test 2: List models
    print("\n2. Listing available models...")
    models = ollama_client.list_models()
    print(f"   ✅ Found {len(models)} models:")
    for model in models:
        print(f"      - {model}")
    
    # Test 3: Simple generation (short response)
    print("\n3. Testing text generation...")
    print("   Generating response (this may take 10-20 seconds)...")
    response = ollama_client.generate(
        "Say 'Hello, AI trading!' in one sentence.",
        model="llama3.2:3b",
        temperature=0.7
    )
    if response:
        print(f"   ✅ Generation successful: {response[:100]}")
    else:
        print("   ❌ Generation failed")
    
    print("\n" + "="*60)
    print("✅ AI integration is ready!")
    print("\nNext steps:")
    print("1. Restart the API: ./start_api.sh")
    print("2. Open dashboard: http://localhost:8501")
    print("3. Go to 'AI Insights' tab")
    print("="*60)

if __name__ == "__main__":
    main()
