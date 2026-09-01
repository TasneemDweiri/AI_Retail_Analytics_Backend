from .base import PBaseSettings


class MainSettings(PBaseSettings):
    # ClickHouse
    D_HOST: str = "localhost"
    D_PORT: int = 8123
    D_USER: str = "default"
    D_PASSWORD: str = ""

    # OpenAI-compatible LLM endpoint
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str

    # Mistral / Voxtral
    MISTRAL_API_KEY: str


settings = MainSettings()
