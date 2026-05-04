from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import field_validator

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
    
    # Schedule config (comma-separated HH:MM)
    PIPELINE_SCHEDULE_TIME: str = "08:00,12:00,14:00,15:00,18:00"

    # OpenAI config
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.4-mini"

    # Email config
    EMAIL_USER: str = ""
    EMAIL_PASS: str = ""
    EMAIL_RECEIVER: str = "anishaak06@gmail.com, jeevaneniyavan@gmail.com,kayal@qonfido.com,vasant@qonfido.com,vikram@qonfido.com,gehna@qonfido.com"
    # SendGrid config (optional) - if present, SendGrid will be used instead of SMTP
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM: str = ""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        extra="ignore"
    )

    @field_validator("SUBREDDITS", mode="before")
    @classmethod
    def parse_subreddits(cls, value):
        if value is None:
            return value
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                import json
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


settings = Settings()
