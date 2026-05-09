"""
Central configuration loader using environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    DATABASE_URL = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{os.getenv('POSTGRES_DB')}"
    )

    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

settings = Settings()