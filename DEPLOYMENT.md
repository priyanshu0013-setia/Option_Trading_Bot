# AI-Powered Options Trading Telegram Bot - Deployment Guide

## Overview

This document provides detailed instructions for deploying the AI-powered options trading Telegram bot with Zerodha API integration. The bot provides market analysis, option chain data, and trading ideas through a user-friendly Telegram interface.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Steps](#deployment-steps)
3. [Environment Variables](#environment-variables)
4. [Zerodha API Integration](#zerodha-api-integration)
5. [How the Bot Delivers Output](#how-the-bot-delivers-output)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the bot, ensure you have:

- A Telegram bot token (obtained from [@BotFather](https://t.me/BotFather))
- Your Telegram user ID (get it from [@userinfobot](https://t.me/userinfobot))
- (Optional) Zerodha API credentials for live market data
- A Render.com account for hosting

## Deployment Steps

### 1. Prepare Your GitHub Repository

1. Create a new GitHub repository or use your existing one
2. Upload all the files from this package to your repository
3. Ensure the following files are at the root level:
   - `app.py`
   - `Procfile`
   - `requirements.txt`

### 2. Deploy to Render

1. Log in to your [Render dashboard](https://dashboard.render.com/)
2. Click "New" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: Choose a name for your service (e.g., "options-trading-bot")
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

### 3. Configure Environment Variables

In your Render dashboard, add the following environment variables:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `ADMIN_USER_IDS`: Your Telegram user ID (comma-separated if multiple)
- `ZERODHA_API_KEY`: Your Zerodha API key (if available)
- `ZERODHA_API_SECRET`: Your Zerodha API secret (if available)

### 4. Deploy and Monitor

1. Click "Create Web Service"
2. Monitor the deployment logs for any errors
3. Once deployed, your bot should be running and accessible via Telegram

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Your Telegram bot token from BotFather |
| `ADMIN_USER_IDS` | Yes | Comma-separated list of admin Telegram user IDs |
| `ZERODHA_API_KEY` | No | Your Zerodha API key for live market data |
| `ZERODHA_API_SECRET` | No | Your Zerodha API secret for live market data |

## Zerodha API Integration

The bot includes integration with the Zerodha API for live market data. To use this feature:

1. Create an account on [Zerodha](https://zerodha.com/)
2. Apply for API access through Zerodha Kite Connect
3. Add your API key and secret to the environment variables
4. The bot will automatically use Zerodha data when credentials are provided

If Zerodha credentials are not provided, the bot will fall back to sample data for demonstration purposes.

## How the Bot Delivers Output

The bot delivers all output directly through Telegram. Here's how it works:

1. **Command-Based Interaction**: Users send commands to the bot (e.g., `/trend NIFTY`)
2. **Text Responses**: The bot responds with formatted text analysis
3. **Charts and Visualizations**: For visual data like trends and heatmaps, the bot generates and sends images
4. **Interactive Menus**: The bot provides button-based menus for easy navigation
5. **Alerts**: When configured, the bot can send real-time alerts for market events

All interaction happens within the Telegram chat interface, making it accessible from any device with Telegram installed.

### Example Commands

- `/start` - Initialize the bot and check authentication
- `/help` - Display help information and available commands
- `/trend [symbol]` - Get market trend analysis for a symbol
- `/options [symbol]` - Get option chain summary for a symbol
- `/ideas [symbol] [count]` - Get trade ideas for a symbol
- `/heatmap [symbol]` - Get OI and volume heatmap for a symbol
- `/summary [symbol]` - Get daily market summary for a symbol

## Troubleshooting

### Common Deployment Issues

1. **Missing app.py error**:
   - Ensure `app.py` is at the root level of your repository
   - Check that the file name matches exactly (case-sensitive)

2. **Module not found errors**:
   - Verify that `requirements.txt` contains all necessary dependencies
   - Check for any typos in import statements

3. **Authentication failures**:
   - Confirm your Telegram bot token is correct
   - Verify your user ID is correctly added to `ADMIN_USER_IDS`

### Logs and Debugging

- Check the Render logs for detailed error information
- The bot includes comprehensive logging to help diagnose issues
- If you encounter persistent problems, try redeploying the service

For additional assistance, refer to the [Render documentation](https://render.com/docs) or [Telegram Bot API documentation](https://core.telegram.org/bots/api).
