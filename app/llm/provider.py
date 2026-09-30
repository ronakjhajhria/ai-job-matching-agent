from typing import Any, Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class LLMProviderError(Exception):
    """Base exception for LLM provider failures."""
    pass

class LLMProvider(Protocol):
    """Protocol defining the interface for LLM interactions.
    
    This abstraction allows us to swap out OpenAI for Anthropic, local models, 
    or mock providers during testing without changing our application logic.
    """
    
    def generate_structured(
        self, 
        messages: list[dict[str, str]], 
        response_model: type[T]
    ) -> T:
        """
        Generate a structured response constrained by a Pydantic model.
        
        Args:
            messages: List of message dictionaries (e.g., [{"role": "user", "content": "..."}]).
            response_model: The Pydantic model class to validate and structure the output.
            
        Returns:
            An instance of the response_model.
            
        Raises:
            LLMProviderError: If the provider fails to generate or validate the output.
        """
        ...
