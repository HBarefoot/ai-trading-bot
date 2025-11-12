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
        timeout: int = 60  # Increased from 30 to 60 seconds
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
