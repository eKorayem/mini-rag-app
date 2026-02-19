from .LLMEnums import LLMEnums
from .providers import OPENAIProvider, COHEREProvider, GroqProvider

class LLMProviderFactory:
    def __init__(self, config: dict):
        self.config = config
    
    def create(self, provider: str):
        if provider == LLMEnums.OPENAI.value:
            return OPENAIProvider(
                api_key=self.config.OPENAI_API_KEY,
                api_url=self.config.OPENAI_API_URL,
                defualt_input_max_characters=self.config.INPUT_DAFAULT_MAX_CHARACTERS,
                defualt_generation_max_out_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DAFAULT_TEMPERATURE
            )
        
        elif provider == LLMEnums.COHERE.value:
            return COHEREProvider(
                api_key=self.config.COHERE_API_KEY,
                defualt_input_max_characters=self.config.INPUT_DAFAULT_MAX_CHARACTERS, 
                defualt_generation_max_out_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DAFAULT_TEMPERATURE
            )
        
        elif provider == LLMEnums.GROQ.value:
            return GroqProvider(
                api_key=self.config.GROQ_API_KEY,
                defualt_input_max_characters=self.config.INPUT_DAFAULT_MAX_CHARACTERS, 
                defualt_generation_max_out_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                default_generation_temperature=self.config.GENERATION_DAFAULT_TEMPERATURE
            )
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")