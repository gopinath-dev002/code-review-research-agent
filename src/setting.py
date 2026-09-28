from dotenv import load_dotenv
load_dotenv()
from dataclasses import dataclass
import os


@dataclass
class Setting:
    db_port: int
    db_host: str
    db_name: str
    db_username: str
    db_password: str
    port: int
    host: str
    log_level: str  
    groq_api_key: str
    groq_model: str


def get_credentials():
    return Setting(
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_host=os.getenv("DB_HOST", "localhost"),
        db_name=os.getenv("DB_NAME", "updated_mcp_coffee_db"),
        db_username=os.getenv("DB_USERNAME", "postgres"),
        db_password=os.getenv("DB_PASSWORD", "postroot123"),
        port=int(os.getenv("PORT", "8001")),
        host=os.getenv("HOST", "0.0.0.0"),
        log_level=os.getenv("LOG_LEVEL", "info"),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        )

credentials = get_credentials()