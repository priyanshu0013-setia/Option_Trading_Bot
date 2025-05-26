"""
Main entry point for the AI Options Trading Bot.
"""
import os
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.telegram_bot import main

if __name__ == "__main__":
    main()
