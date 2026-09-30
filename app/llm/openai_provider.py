from typing import TypeVar
import openai
from pydantic import BaseModel

from app.llm.provider import LLMProvider, LLMProviderError

T = TypeVar("T", bound=BaseModel)

class OpenAIProvider(LLMProvider):
    """OpenAI implementation of the LLMProvider protocol."""

    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-4o-mini", 
        timeout: float = 30.0, 
        max_retries: int = 2
    ):
        self.model = model
        # Configure client with retries and timeout for robust network calls
        self.client = openai.OpenAI(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    def generate_structured(
        self, 
        messages: list[dict[str, str]], 
        response_model: type[T]
    ) -> T:
        try:
            # We use the beta.responses.parse feature for guaranteed structured outputs
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=response_model,
            )
            
            # Extract and return the strongly-typed parsed Pydantic object
            parsed_result = response.choices[0].message.parsed
            
            if parsed_result is None:
                raise LLMProviderError("Provider returned a null parsed object.")
                
            return parsed_result
            
        except openai.APIError as e:
            raise LLMProviderError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            raise LLMProviderError(f"Unexpected error during generation: {str(e)}") from e
