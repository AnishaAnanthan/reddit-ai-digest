from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # Reddit config
    SUBREDDITS: List[str] = [
        "MutualfundsIndia",
        "personalfinanceindia",
        "IndiaInvestments",
        "FIREIndia",
        "fatFIREIndia"
    ]
    POST_LIMIT: int = 10
    COMMENT_LIMIT: int = 5
    STAGE1_BATCH_SIZE: int = 5
    STAGE1_COMMENT_CHAR_LIMIT: int = 320
    STAGE1_COMMENT_SUMMARY_CHAR_LIMIT: int = 900
    STAGE1_TOTAL_COMMENT_CHAR_BUDGET: int = 1800
    
    # Schedule config (24-hour format HH:MM)
    PIPELINE_SCHEDULE_TIME: str = "22:05"

    # OpenAI config
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Email config
    EMAIL_USER: str = ""
    EMAIL_PASS: str = ""
    EMAIL_RECEIVER: str = "anishaak06@gmail.com, jeevaneniyavan@gmail.com"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        extra="ignore"
    )


settings = Settings()
