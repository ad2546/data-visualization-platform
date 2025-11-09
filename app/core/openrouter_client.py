"""
Simple OpenRouter API client for LLM requests
"""
import os
import requests
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Ensure .env is loaded before any client initialization
# Try to find .env file in project root (parent of app directory)
import pathlib
env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback to default behavior
    load_dotenv()

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API"""
    
    def __init__(self, model: str = None):
        # Reload env to ensure we have the latest values
        import pathlib
        env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            load_dotenv(override=True)
        
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = model or os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set. API calls will fail.")
            logger.warning(f"Looking for .env at: {env_path}")
            logger.warning("Make sure .env file exists and contains OPENROUTER_API_KEY=your_key")
        else:
            logger.info(f"✓ OpenRouter API key loaded successfully (key starts with: {self.api_key[:10]}...)")
    
    def generate_content(self, prompt: str, system_prompt: str = None, max_tokens: int = 8192, temperature: float = 0.7) -> Optional[str]:
        """
        Generate content using OpenRouter API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text or None if error
        """
        if not self.api_key:
            logger.error("OpenRouter API key not configured")
            return None
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # Optional
                "X-Title": "Data Visualization Platform"  # Optional
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            logger.info(f"Calling OpenRouter API with model: {self.model}")
            logger.info(f"Request URL: {self.base_url}")
            logger.info(f"Max Tokens: {max_tokens}, Temperature: {temperature}")
            logger.info(f"Prompt Length: {len(prompt)} chars")
            if system_prompt:
                logger.info(f"System Prompt Length: {len(system_prompt)} chars")
            
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            
            # Log API response metadata
            if "usage" in result:
                usage = result["usage"]
                logger.info(f"API Usage - Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}, "
                          f"Completion Tokens: {usage.get('completion_tokens', 'N/A')}, "
                          f"Total: {usage.get('total_tokens', 'N/A')}")
            
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "finish_reason" in choice:
                    logger.info(f"Finish Reason: {choice['finish_reason']}")
                
                content = choice["message"]["content"]
                logger.info(f"Successfully generated {len(content)} characters")
                return content
            else:
                logger.error(f"Unexpected response format: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling OpenRouter: {str(e)}")
            return None


# Global instance
openrouter_client = OpenRouterClient()

