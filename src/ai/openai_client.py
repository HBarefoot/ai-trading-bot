"""
OpenAI LLM Integration
OpenAI API client for sentiment analysis and market commentary
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Try to import OpenAI, fall back gracefully
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Install with: pip install openai")


class OpenAIClient:
    """Client for interacting with OpenAI API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-3.5-turbo",
        timeout: int = 60
    ):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
            default_model: Model to use (gpt-3.5-turbo, gpt-4o-mini, etc.)
            timeout: Request timeout in seconds
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed")
            
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable")
            
        self.default_model = default_model
        self.timeout = timeout
        self.client = OpenAI(api_key=self.api_key, timeout=self.timeout)
        
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> str:
        """
        Generate text using OpenAI
        
        Args:
            prompt: User prompt
            model: Model name (default: gpt-3.5-turbo)
            system: System prompt for instructions
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Stream response (not implemented)
            
        Returns:
            Generated text
        """
        model = model or self.default_model
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"OpenAI generate error: {e}")
            return ""
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Chat completion with conversation history
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "text"}
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Assistant's response
        """
        model = model or self.default_model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return ""
    
    def get_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> List[float]:
        """
        Get text embedding for similarity search
        
        Args:
            text: Text to embed
            model: Embedding model (text-embedding-3-small is cheaper)
            
        Returns:
            List of embedding values
        """
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            # Simple test call
            self.client.models.list()
            return True
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []


# Global instance - will be initialized when imported
openai_client = None

def get_openai_client() -> Optional[OpenAIClient]:
    """Get or create OpenAI client singleton"""
    global openai_client
    
    if openai_client is None:
        try:
            openai_client = OpenAIClient()
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    
    return openai_client
