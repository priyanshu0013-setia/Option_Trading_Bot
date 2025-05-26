# AI-Powered Options Trading Telegram Bot

## Setup and Installation Guide

This document provides comprehensive instructions for setting up and running the AI-powered options trading Telegram bot.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Bot](#running-the-bot)
5. [Bot Commands](#bot-commands)
6. [Admin Functions](#admin-functions)
7. [Customization](#customization)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before installing the bot, ensure you have the following:

- Python 3.9 or higher
- pip (Python package installer)
- A Telegram account
- A Telegram bot token (obtained from [@BotFather](https://t.me/BotFather))
- (Optional) API keys for market data sources (NSE India, Zerodha Kite Connect)
- (Optional) Redis server for caching (SQLite is used as fallback)

## Installation

1. **Clone or download the repository**

   Download and extract the project files to your desired location.

2. **Set up a virtual environment**

   ```bash
   # Navigate to the project directory
   cd ai_options_bot

   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install python-telegram-bot pandas numpy scikit-learn matplotlib plotly redis python-dotenv
   ```

## Configuration

1. **Create an environment file**

   Create a `.env` file in the project root directory with the following variables:

   ```
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

   # Admin User IDs (comma-separated list of Telegram user IDs)
   ADMIN_USER_IDS=123456789,987654321

   # Market Data API Configuration (optional)
   NSE_API_KEY=your_nse_api_key
   ZERODHA_API_KEY=your_zerodha_api_key
   ZERODHA_API_SECRET=your_zerodha_api_secret

   # Redis Configuration (optional)
   REDIS_URL=redis://localhost:6379/0
   USE_REDIS=False

   # ML Model Configuration
   ENABLE_ML_ENGINE=True
   USE_EXTERNAL_AI=False
   OPENAI_API_KEY=your_openai_api_key_if_using_external_ai

   # Feature Flags
   ENABLE_REAL_TIME_ALERTS=True

   # Logging Configuration
   LOG_LEVEL=INFO
   ```

2. **Configure admin users**

   Add your Telegram user ID to the `ADMIN_USER_IDS` in the `.env` file. You can get your Telegram user ID by sending a message to [@userinfobot](https://t.me/userinfobot).

3. **Directory structure**

   Ensure the following directories exist in the project root:
   - `logs/` - For log files
   - `data/` - For temporary data storage
   - `models/` - For ML models (if using)

## Running the Bot

1. **Start the bot**

   ```bash
   # Make sure you're in the project directory with the virtual environment activated
   python -m bot.telegram_bot
   ```

2. **First-time setup**

   - Once the bot is running, open Telegram and search for your bot by username
   - Start a conversation with the bot by clicking "Start" or sending `/start`
   - As an admin, you can generate invite links for other users with `/invite`

3. **Inviting users**

   - Use the `/invite` command to generate a unique invite link
   - Share this link with users you want to give access to
   - When users click the link, they will be automatically authenticated

## Bot Commands

The bot supports the following commands:

- `/start` - Initialize the bot and check authentication
- `/help` - Display help information and available commands
- `/trend [symbol]` - Get market trend analysis for a symbol
- `/options [symbol]` - Get option chain summary for a symbol
- `/ideas [symbol] [count]` - Get trade ideas for a symbol (count is optional, default is 3)
- `/heatmap [symbol]` - Get OI and volume heatmap for a symbol
- `/summary [symbol]` - Get daily market summary for a symbol

If no symbol is provided, NIFTY is used as the default.

## Admin Functions

Administrators have access to additional commands:

- `/admin` - Access the admin panel
- `/invite` - Generate invite links for new users

The admin panel provides the following functions:
- Generate invite links
- View user statistics
- Check system status

## Customization

### Adding new symbols

The bot is pre-configured with common Indian indices (NIFTY, BANKNIFTY, FINNIFTY, SENSEX). To add more symbols:

1. Modify the inline keyboards in the `handle_callback` method in `bot/telegram_bot.py`
2. Update the market data fetcher in `data/market_data.py` to handle the new symbols

### Customizing analysis rules

The rule-based analysis engine in `analysis/analysis_engine.py` can be customized:

1. Modify the `RuleBasedAnalysis` class to add or change analysis rules
2. Update the corresponding report formatters in `utils/visualization.py`

### Integrating with real market data

To use real market data instead of the sample data:

1. Obtain API keys for your preferred market data provider
2. Update the `.env` file with your API keys
3. Modify the `MarketDataFetcher` class in `data/market_data.py` to use the actual API endpoints

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if the bot is running
   - Verify your Telegram bot token is correct
   - Check the logs for errors

2. **Authentication failures**
   - Ensure your user ID is in the admin list or you've used a valid invite link
   - Check if the invite link has expired

3. **Missing charts or visualizations**
   - Ensure matplotlib and plotly are correctly installed
   - Check if the temporary directories have proper write permissions

### Logs

Log files are stored in the `logs/` directory. Check these files for detailed error information if you encounter issues.

### Getting Help

If you encounter persistent issues:
1. Check the logs for specific error messages
2. Verify all dependencies are correctly installed
3. Ensure your environment variables are properly set
