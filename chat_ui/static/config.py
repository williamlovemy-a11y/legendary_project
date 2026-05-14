import os
from pathlib import Path

# Настройки Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/chat")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma3:4b")

# Настройки API сервера
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8001"))

# Настройки хранилища
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)  # Автосоздание папки

# Настройки загрузки файлов
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "200"))
MAX_BYTES = MAX_UPLOAD_MB * 1024 * 1024
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet"}

# Настройки безопасности и лимитов
MAX_HISTORY_LENGTH = int(os.getenv("MAX_HISTORY_LENGTH", "20"))  # Максимальное число сообщений в истории
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))  # Таймаут запроса к Ollama в секундах

# CORS настройки (для разработки)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")