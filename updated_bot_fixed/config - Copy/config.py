"""
Configuration settings for the AI Options Trading Bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Access Control
ADMIN_USER_IDS = [int(id) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id]
ALLOWED_USERS = {}  # Will be populated with user_id -> expiry_time

# Market Data API Configuration
NSE_API_KEY = os.getenv("NSE_API_KEY", "")
ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY", "")
ZERODHA_API_SECRET = os.getenv("ZERODHA_API_SECRET", "")

# Redis Configuration (for caching)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
USE_REDIS = os.getenv("USE_REDIS", "False").lower() == "true"

# SQLite Configuration (fallback if Redis is not available)
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cache.db")

# ML Model Configuration
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
USE_EXTERNAL_AI = os.getenv("USE_EXTERNAL_AI", "False").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "bot.log")

# Feature Flags
ENABLE_RULE_ENGINE = True
ENABLE_ML_ENGINE = os.getenv("ENABLE_ML_ENGINE", "True").lower() == "true"
ENABLE_REAL_TIME_ALERTS = os.getenv("ENABLE_REAL_TIME_ALERTS", "True").lower() == "true"

# Cache Settings
CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", "300"))  # 5 minutes default
MAX_INTERACTIONS_STORED = 2  # Store last 2 interactions per user

# Command Throttling
THROTTLE_RATE = int(os.getenv("THROTTLE_RATE", "3"))  # Max commands per minute
