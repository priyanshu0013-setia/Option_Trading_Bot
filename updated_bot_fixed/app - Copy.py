"""
Main entry point for the AI Options Trading Bot.
This file handles environment setup and bot initialization.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Set default Telegram token for testing
if not os.environ.get("TELEGRAM_BOT_TOKEN"):
    os.environ["TELEGRAM_BOT_TOKEN"] = "YOUR_BOT_TOKEN_HERE"

# Set default admin user IDs
if not os.environ.get("ADMIN_USER_IDS"):
    os.environ["ADMIN_USER_IDS"] = ""

# Set default Zerodha API credentials
if not os.environ.get("ZERODHA_API_KEY"):
    os.environ["ZERODHA_API_KEY"] = ""

if not os.environ.get("ZERODHA_API_SECRET"):
    os.environ["ZERODHA_API_SECRET"] = ""

# Create necessary directories
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("models", exist_ok=True)

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the bot
from bot.telegram_bot import main

if __name__ == "__main__":
    main()
