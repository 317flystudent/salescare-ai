from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "salescare.db"

CHATBOT_HOST = os.getenv("CHATBOT_HOST", "127.0.0.1")
CHATBOT_PORT = int(os.getenv("CHATBOT_PORT", "8000"))
CHATBOT_DB_ENGINE = os.getenv("CHATBOT_DB_ENGINE", "sqlite").lower()
CHATBOT_DB = Path(os.getenv("CHATBOT_DB", str(DEFAULT_DB_PATH)))

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "salescare_ai")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv(
    "DEEPSEEK_BASE_URL",
    "https://api.deepseek.com/v1/chat/completions",
)
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT = int(os.getenv("DEEPSEEK_TIMEOUT", "15"))
