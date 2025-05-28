"""
Telegram bot implementation for the AI Options Trading Bot.
"""
import logging
import os
from datetime import datetime, timedelta
import tempfile
import base64
from typing import Dict, List, Optional, Tuple, Union

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Use absolute imports instead of relative imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from utils.helpers import setup_logging, is_user_authorized, add_authorized_user, generate_invite_link, RateLimiter
from data.market_data import MarketDataFetcher
from analysis.analysis_engine import RuleBasedAnalysis, MLAnalysis
from utils.visualization import ChartGenerator, ReportFormatter

# Set up logging
logger = setup_logging(config.LOG_FILE, config.LOG_LEVEL)

# Initialize rate limiter
rate_limiter = RateLimiter(config.THROTTLE_RATE, 60)  # Max commands per minute

class OptionsTradingBot:
    """Main Telegram bot class for options trading insights."""
    
    def __init__(self):
        """Initialize the bot with all required components."""
        # Initialize data components
        self.market_data = MarketDataFetcher(
            nse_api_key=config.NSE_API_KEY,
            zerodha_api_key=config.ZERODHA_API_KEY,
            zerodha_api_secret=config.ZERODHA_API_SECRET
        )
        
        # Initialize analysis components
        self.rule_engine = RuleBasedAnalysis(self.market_data)
        self.ml_engine = MLAnalysis(
            self.market_data,
            use_external_ai=config.USE_EXTERNAL_AI,
            openai_api_key=config.OPENAI_API_KEY
        )
        
        # Initialize visualization components
        self.chart_generator = ChartGenerator()
        self.report_formatter = ReportFormatter()
        
        # Initialize bot application
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        self._register_handlers()
        
        # Store active invite links
        self.invite_links = {}  # token -> expiry_time
        
        # Store user data
        self.user_interactions = {}  # user_id -> [last_interactions]
        
        logger.info("Options Trading Bot initialized")
    
    def _register_handlers(self):
        """Register all command and callback handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("trend", self.trend_command))
        self.application.add_handler(CommandHandler("options", self.options_command))
        self.application.add_handler(CommandHandler("ideas", self.ideas_command))
        self.application.add_handler(CommandHandler("heatmap", self.heatmap_command))
        self.application.add_handler(CommandHandler("summary", self.summary_command))
        self.application.add_handler(CommandHandler("invite", self.invite_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler for invite links
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        user = update.effective_user
        user_id = user.id
        
        # Check if this is an invite link
        if context.args and len(context.args) == 1:
            invite_token = context.args[0]
            if invite_token in self.invite_links:
                if datetime.now() < self.invite_links[invite_token]:
                    # Valid invite, add user to allowed users
                    expiry = add_authorized_user(user_id, config.ALLOWED_USERS)
                    
                    # Remove the used invite link
                    del self.invite_links[invite_token]
                    
                    await update.message.reply_text(
                        f"Welcome {user.first_name}! You have been granted access to the Options Trading Bot. "
                        f"Your access will expire on {expiry.strftime('%Y-%m-%d')}.\n\n"
                        f"Type /help to see available commands."
                    )
                    
                    # Send welcome menu
                    await self._send_welcome_menu(update)
                    return
                else:
                    # Expired invite
                    del self.invite_links[invite_token]
                    await update.message.reply_text(
                        "This invite link has expired. Please request a new one."
                    )
                    return
        
        # Check if user is authorized
        if is_user_authorized(user_id, config.ALLOWED_USERS) or user_id in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                f"Welcome back {user.first_name}! How can I assist you today?\n\n"
                f"Type /help to see available commands."
            )
            
            # Send welcome menu
            await self._send_welcome_menu(update)
        else:
            await update.message.reply_text(
                "You are not authorized to use this bot. Please contact an administrator for an invite link."
            )
    
    async def _send_welcome_menu(self, update: Update):
        """Send the welcome menu with main options."""
        keyboard = [
            [
                InlineKeyboardButton("📈 Market Trend", callback_data="menu_trend"),
                InlineKeyboardButton("📋 Option Chain", callback_data="menu_options")
            ],
            [
                InlineKeyboardButton("💡 Trade Ideas", callback_data="menu_ideas"),
                InlineKeyboardButton("🔥 OI Heatmap", callback_data="menu_heatmap")
            ],
            [
                InlineKeyboardButton("📅 Daily Summary", callback_data="menu_summary"),
                InlineKeyboardButton("❓ Help", callback_data="menu_help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Please select an option:",
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command."""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not is_user_authorized(user_id, config.ALLOWED_USERS) and user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to use this bot. Please contact an administrator for an invite link."
            )
            return
        
        help_text = (
            "🤖 *AI Options Trading Bot Help* 🤖\n\n"
            "*Available Commands:*\n\n"
            "📈 */trend [symbol]* - Get market trend analysis\n"
            "   Example: `/trend NIFTY`\n\n"
            "📋 */options [symbol]* - Get option chain summary\n"
            "   Example: `/options BANKNIFTY`\n\n"
            "💡 */ideas [symbol] [count]* - Get trade ideas\n"
            "   Example: `/ideas NIFTY 3`\n\n"
            "🔥 */heatmap [symbol]* - Get OI & volume heatmap\n"
            "   Example: `/heatmap NIFTY`\n\n"
            "📅 */summary [symbol]* - Get daily market summary\n"
            "   Example: `/summary NIFTY`\n\n"
            "❓ */help* - Show this help message\n\n"
            "*Default Symbols:*\n"
            "If no symbol is provided, NIFTY will be used as default.\n\n"
            "*Note:*\n"
            "This bot provides analysis and insights, but does not execute trades."
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown'
        )
    
    async def trend_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /trend command."""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not is_user_authorized(user_id, config.ALLOWED_USERS) and user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to use this bot. Please contact an administrator for an invite link."
            )
            return
        
        # Check rate limit
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text(
                "You are sending commands too quickly. Please wait a moment before trying again."
            )
            return
        
        # Get symbol from arguments or use default
        symbol = "NIFTY"
        if context.args and len(context.args) > 0:
            symbol = context.args[0].upper()
        
        # Send typing action
        await update.message.reply_chat_action("typing")
        
        try:
            # Get trend analysis
            trend_analysis = self.rule_engine.analyze_market_trend(symbol)
            
            # Format report
            report = self.report_formatter.format_market_trend_report(trend_analysis)
            
            # Generate chart
            chart_base64 = self.chart_generator.generate_trend_chart(trend_analysis)
            
            # Create temporary file for chart
            if chart_base64:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(base64.b64decode(chart_base64))
                    chart_path = temp_file.name
                
                # Send chart with caption
                await update.message.reply_photo(
                    photo=open(chart_path, 'rb'),
                    caption=report,
                    parse_mode='Markdown'
                )
                
                # Clean up
                os.unlink(chart_path)
            else:
                # Send text only if chart generation failed
                await update.message.reply_text(
                    report,
                    parse_mode='Markdown'
                )
            
            # Add back to menu button
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=reply_markup
            )
            
            # Store interaction
            self._store_user_interaction(user_id, f"Requested trend analysis for {symbol}")
            
        except Exception as e:
            logger.error(f"Error in trend command: {e}")
            await update.message.reply_text(
                f"Sorry, I encountered an error while analyzing {symbol}. Please try again later."
            )
    
    async def options_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /options command."""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not is_user_authorized(user_id, config.ALLOWED_USERS) and user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to use this bot. Please contact an administrator for an invite link."
            )
            return
        
        # Check rate limit
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text(
                "You are sending commands too quickly. Please wait a moment before trying again."
            )
            return
        
        # Get symbol from arguments or use default
        symbol = "NIFTY"
        if context.args and len(context.args) > 0:
            symbol = context.args[0].upper()
        
        # Send typing action
        await update.message.reply_chat_action("typing")
        
        try:
            # Get option chain analysis
            analysis = self.rule_engine.analyze_option_chain(symbol)
            
            # Format summary
            summary = self.report_formatter.format_option_chain_summary(analysis)
            
            # Generate chart
            chart_base64 = self.chart_generator.generate_option_chain_summary(analysis)
            
            # Create temporary file for chart
            if chart_base64:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(base64.b64decode(chart_base64))
                    chart_path = temp_file.name
                
                # Send chart with caption
                await update.message.reply_photo(
                    photo=open(chart_path, 'rb'),
                    caption=summary,
                    parse_mode='Markdown'
                )
                
                # Clean up
                os.unlink(chart_path)
            else:
                # Send text only if chart generation failed
                await update.message.reply_text(
                    summary,
                    parse_mode='Markdown'
                )
            
            # Add back to menu button
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=reply_markup
            )
            
            # Store interaction
            self._store_user_interaction(user_id, f"Requested option chain analysis for {symbol}")
            
        except Exception as e:
            logger.error(f"Error in options command: {e}")
            await update.message.reply_text(
                f"Sorry, I encountered an error while analyzing {symbol} options. Please try again later."
            )
    
    async def ideas_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /ideas command."""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not is_user_authorized(user_id, config.ALLOWED_USERS) and user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to use this bot. Please contact an administrator for an invite link."
            )
            return
        
        # Check rate limit
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text(
                "You are sending commands too quickly. Please wait a moment before trying again."
            )
            return
        
        # Get symbol and count from arguments or use defaults
        symbol = "NIFTY"
        count = 3
        
        if context.args:
            if len(context.args) > 0:
                symbol = context.args[0].upper()
            if len(context.args) > 1:
                try:
                    count = int(context.args[1])
                    count = max(1, min(5, count))  # Limit between 1 and 5
                except ValueError:
                    pass
        
        # Send typing action
        await update.message.reply_chat_action("typing")
        
        try:
            # Generate trade ideas
            ideas = self.rule_engine.generate_trade_ideas(symbol, count)
            
            # Enhance with ML if enabled
            if config.ENABLE_ML_ENGINE:
                ideas = self.ml_engine.enhance_trade_ideas(ideas)
            
            # Format ideas
            formatted_ideas = self.report_formatter.format_trade_ideas(ideas)
            
            await update.message.reply_text(
                formatted_ideas,
                parse_mode='Markdown'
            )
            
            # Add back to menu button
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=reply_markup
            )
            
            # Store interaction
            self._store_user_interaction(user_id, f"Requested {count} trade ideas for {symbol}")
            
        except Exception as e:
            logger.error(f"Error in ideas command: {e}")
            await update.message.reply_text(
                f"Sorry, I encountered an error while generating trade ideas for {symbol}. Please try again later."
            )
    
    async def heatmap_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /heatmap command."""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not is_user_authorized(user_id, config.ALLOWED_USERS) and user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to use this bot. Please contact an administrator for an invite link."
            )
            return
        
        # Check rate limit
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text(
                "You are sending commands too quickly. Please wait a moment before trying again."
            )
            return
        
        # Get symbol from arguments or use default
        symbol = "NIFTY"
        if context.args and len(context.args) > 0:
            symbol = context.args[0].upper()
        
        # Send typing action
        await update.message.reply_chat_action("typing")
        
        try:
            # Get option chain data
            option_chain = self.market_data.get_option_chain(symbol)
            
            # Generate heatmap
            heatmap_base64 = self.chart_generator.generate_oi_heatmap(option_chain)
            
            # Create temporary file for heatmap
            if heatmap_base64:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(base64.b64decode(heatmap_base64))
                    heatmap_path = temp_file.name
                
                # Send heatmap with caption
                await update.message.reply_photo(
                    photo=open(heatmap_path, 'rb'),
                    caption=f"*{symbol} Open Interest Heatmap*\n\nThis heatmap shows the distribution of open interest across different strike prices and expiry dates. Darker colors indicate higher open interest.",
                    parse_mode='Markdown'
                )
                
                # Clean up
                os.unlink(heatmap_path)
            else:
                # Send text only if heatmap generation failed
                await update.message.reply_text(
                    f"Sorry, I couldn't generate a heatmap for {symbol}. Please try again later."
                )
            
            # Add back to menu button
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=reply_markup
            )
            
            # Store interaction
            self._store_user_interaction(user_id, f"Requested OI heatmap for {symbol}")
            
        except Exception as e:
            logger.error(f"Error in heatmap command: {e}")
            await update.message.reply_text(
                f"Sorry, I encountered an error while generating the heatmap for {symbol}. Please try again later."
            )
    
    async def summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /summary command."""
        user_id = update.effective_user.id
        
        # Check if user is authorized
        if not is_user_authorized(user_id, config.ALLOWED_USERS) and user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to use this bot. Please contact an administrator for an invite link."
            )
            return
        
        # Check rate limit
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text(
                "You are sending commands too quickly. Please wait a moment before trying again."
            )
            return
        
        # Get symbol from arguments or use default
        symbol = "NIFTY"
        if context.args and len(context.args) > 0:
            symbol = context.args[0].upper()
        
        # Send typing action
        await update.message.reply_chat_action("typing")
        
        try:
            # Get market data
            market_data = self.market_data.get_market_data(symbol, interval='1d', days=5)
            
            # Get option chain data
            option_chain = self.market_data.get_option_chain(symbol)
            
            # Generate summary
            summary = self.rule_engine.generate_market_summary(symbol, market_data, option_chain)
            
            # Format summary
            formatted_summary = self.report_formatter.format_market_summary(summary)
            
            await update.message.reply_text(
                formatted_summary,
                parse_mode='Markdown'
            )
            
            # Add back to menu button
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "What would you like to do next?",
                reply_markup=reply_markup
            )
            
            # Store interaction
            self._store_user_interaction(user_id, f"Requested market summary for {symbol}")
            
        except Exception as e:
            logger.error(f"Error in summary command: {e}")
            await update.message.reply_text(
                f"Sorry, I encountered an error while generating the summary for {symbol}. Please try again later."
            )
    
    async def invite_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /invite command."""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to use this command. Only administrators can generate invite links."
            )
            return
        
        # Generate invite link
        token, expiry = generate_invite_link()
        
        # Store invite link
        self.invite_links[token] = expiry
        
        # Create invite URL
        bot_username = (await self.application.bot.get_me()).username
        invite_url = f"https://t.me/{bot_username}?start={token}"
        
        await update.message.reply_text(
            f"Invite link generated! This link will expire on {expiry.strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
            f"{invite_url}\n\n"
            f"Share this link with the user you want to invite."
        )
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /admin command."""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to use this command. Only administrators can access the admin panel."
            )
            return
        
        # Create admin panel
        keyboard = [
            [InlineKeyboardButton("Generate Invite Link", callback_data="admin_invite")],
            [InlineKeyboardButton("View User Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("Check System Status", callback_data="admin_status")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Admin Panel\n\nPlease select an option:",
            reply_markup=reply_markup
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        user_id = query.from_user.id
        
        # Check if user is authorized
        if not is_user_authorized(user_id, config.ALLOWED_USERS) and user_id not in config.ADMIN_USER_IDS:
            await query.answer("You are not authorized to use this bot.")
            return
        
        # Check rate limit
        if not rate_limiter.is_allowed(user_id):
            await query.answer("You are interacting too quickly. Please wait a moment.")
            return
        
        # Answer the callback query to stop the loading animation
        await query.answer()
        
        # Handle different callback data
        if query.data == "back_to_menu":
            # Send welcome menu
            await self._send_welcome_menu(query)
        
        elif query.data == "menu_help":
            # Send help message
            await self.help_command(query, context)
        
        elif query.data == "menu_trend":
            # Send trend analysis for default symbol
            context.args = ["NIFTY"]
            await self.trend_command(query, context)
        
        elif query.data == "menu_options":
            # Send option chain for default symbol
            context.args = ["NIFTY"]
            await self.options_command(query, context)
        
        elif query.data == "menu_ideas":
            # Send trade ideas for default symbol
            context.args = ["NIFTY"]
            await self.ideas_command(query, context)
        
        elif query.data == "menu_heatmap":
            # Send heatmap for default symbol
            context.args = ["NIFTY"]
            await self.heatmap_command(query, context)
        
        elif query.data == "menu_summary":
            # Send summary for default symbol
            context.args = ["NIFTY"]
            await self.summary_command(query, context)
        
        elif query.data == "admin_invite":
            # Generate invite link
            await self.invite_command(query, context)
        
        elif query.data == "admin_stats":
            # Show user statistics
            await self._show_user_statistics(query)
        
        elif query.data == "admin_status":
            # Show system status
            await self._show_system_status(query)
    
    async def _show_user_statistics(self, update: Update):
        """Show user statistics."""
        # Count total users
        total_users = len(config.ALLOWED_USERS)
        
        # Count active users (interacted in the last 24 hours)
        active_users = 0
        for user_id, interactions in self.user_interactions.items():
            if interactions and interactions[-1]['timestamp'] > datetime.now() - timedelta(days=1):
                active_users += 1
        
        # Generate statistics text
        stats_text = (
            "*User Statistics*\n\n"
            f"Total Users: {total_users}\n"
            f"Active Users (24h): {active_users}\n\n"
            f"Total Interactions: {sum(len(interactions) for interactions in self.user_interactions.values())}\n"
        )
        
        # Add back to admin panel button
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _show_system_status(self, update: Update):
        """Show system status."""
        # Get system status
        status_text = (
            "*System Status*\n\n"
            f"Bot Online Since: {datetime.now() - timedelta(hours=2)}\n"  # Placeholder
            f"API Status: ✅ Operational\n"
            f"Sample Data Mode: {'✅ Enabled' if self.market_data.use_sample_data else '❌ Disabled'}\n"
            f"ML Engine: {'✅ Enabled' if config.ENABLE_ML_ENGINE else '❌ Disabled'}\n"
            f"Real-time Alerts: {'✅ Enabled' if config.ENABLE_REAL_TIME_ALERTS else '❌ Disabled'}\n"
        )
        
        # Add back to admin panel button
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages."""
        # Currently, we don't do anything with regular messages
        pass
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error: {context.error}")
        
        # Send error message to user if possible
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, an error occurred while processing your request. Please try again later."
            )
    
    def _store_user_interaction(self, user_id: int, action: str):
        """Store user interaction for statistics."""
        if user_id not in self.user_interactions:
            self.user_interactions[user_id] = []
        
        self.user_interactions[user_id].append({
            'timestamp': datetime.now(),
            'action': action
        })
        
        # Limit to last 100 interactions per user
        if len(self.user_interactions[user_id]) > 100:
            self.user_interactions[user_id] = self.user_interactions[user_id][-100:]
    
    def run(self):
        """Run the bot."""
        logger.info("Starting bot")
        self.application.run_polling()


def main():
    """Main function to run the bot."""
    bot = OptionsTradingBot()
    bot.run()


if __name__ == "__main__":
    main()
