"""
Unified LLM Client
Automatically uses OpenAI or falls back to Ollama
"""
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class UnifiedLLMClient:
    """Unified client that supports both OpenAI and Ollama"""
    
    def __init__(self):
        self.client = None
        self.provider = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the best available LLM client"""
        # Try OpenAI first if API key is available
        if os.getenv("OPENAI_API_KEY"):
            try:
                from ai.openai_client import get_openai_client
                self.client = get_openai_client()
                if self.client and self.client.is_available():
                    self.provider = "openai"
                    logger.info("Using OpenAI API for LLM")
                    return
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Fall back to Ollama
        try:
            from ai.ollama_client import ollama_client
            if ollama_client.is_available():
                self.client = ollama_client
                self.provider = "ollama"
                logger.info("Using Ollama for LLM")
                return
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama client: {e}")
        
        logger.error("No LLM provider available! Install OpenAI library and set OPENAI_API_KEY, or run Ollama locally")
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text using available LLM"""
        if not self.client:
            logger.error("No LLM client available")
            return ""
        
        return self.client.generate(
            prompt=prompt,
            model=model,
            system=system,
            temperature=temperature,
            **kwargs
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Chat completion"""
        if not self.client:
            logger.error("No LLM client available")
            return ""
        
        return self.client.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            **kwargs
        )
    
    def get_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Get text embedding"""
        if not self.client:
            logger.error("No LLM client available")
            return []
        
        return self.client.get_embedding(text, model=model or "text-embedding-3-small")
    
    def is_available(self) -> bool:
        """Check if any LLM client is available"""
        return self.client is not None and self.client.is_available()
    
    def get_provider(self) -> Optional[str]:
        """Get current provider name"""
        return self.provider


# Global instance
llm_client = UnifiedLLMClient()
