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

from ..config import config
from ..utils.helpers import setup_logging, is_user_authorized, add_authorized_user, generate_invite_link, RateLimiter
from ..data.market_data import MarketDataFetcher, DataProcessor
from ..analysis.analysis_engine import RuleBasedAnalysis, MLAnalysis
from ..utils.visualization import ChartGenerator, ReportFormatter

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
            
            if not ideas:
                await update.message.reply_text(
                    f"Sorry, I couldn't generate any trade ideas for {symbol} at this time. Please try again later."
                )
                return
            
            # Send each idea as a separate message
            for idea in ideas:
                formatted_idea = self.report_formatter.format_trade_idea(idea)
                
                # Add view chart button
                keyboard = [
                    [
                        InlineKeyboardButton("View Chart", callback_data=f"chart_{symbol}_{idea['strike']}_{idea['option_type']}")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    formatted_idea,
                    parse_mode='Markdown',
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
            # Generate heatmap data
            heatmap_data = self.rule_engine.generate_oi_heatmap_data(symbol)
            
            # Generate heatmap visualization
            heatmap_base64 = self.chart_generator.generate_oi_heatmap(heatmap_data)
            
            # Create temporary file for heatmap
            if heatmap_base64:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(base64.b64decode(heatmap_base64))
                    heatmap_path = temp_file.name
                
                # Send heatmap with caption
                await update.message.reply_photo(
                    photo=open(heatmap_path, 'rb'),
                    caption=f"🔥 *{symbol} - Open Interest & Volume Heatmap* 🔥\n\n"
                            f"This heatmap shows the distribution of open interest and volume across different strike prices.\n\n"
                            f"_Updated: {heatmap_data['timestamp']}_",
                    parse_mode='Markdown'
                )
                
                # Clean up
                os.unlink(heatmap_path)
            else:
                # Send text only if heatmap generation failed
                await update.message.reply_text(
                    f"Sorry, I couldn't generate the heatmap for {symbol} at this time. Please try again later."
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
            # Get trend analysis
            trend_analysis = self.rule_engine.analyze_market_trend(symbol)
            
            # Get option chain analysis
            option_analysis = self.rule_engine.analyze_option_chain(symbol)
            
            # Generate trade ideas
            trade_ideas = self.rule_engine.generate_trade_ideas(symbol, 3)
            
            # Format daily summary
            summary = self.report_formatter.format_daily_summary(
                symbol, trend_analysis, option_analysis, trade_ideas
            )
            
            # Send summary
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
            self._store_user_interaction(user_id, f"Requested daily summary for {symbol}")
            
        except Exception as e:
            logger.error(f"Error in summary command: {e}")
            await update.message.reply_text(
                f"Sorry, I encountered an error while generating the summary for {symbol}. Please try again later."
            )
    
    async def invite_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /invite command to generate invite links."""
        user_id = update.effective_user.id
        
        # Check if user is an admin
        if user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to generate invite links."
            )
            return
        
        # Generate a new invite link
        invite_token = generate_invite_link()
        
        # Set expiry time (24 hours)
        expiry_time = datetime.now() + timedelta(hours=24)
        
        # Store the invite link
        self.invite_links[invite_token] = expiry_time
        
        # Create the full invite link
        bot_username = context.bot.username
        invite_link = f"https://t.me/{bot_username}?start={invite_token}"
        
        await update.message.reply_text(
            f"Here is your invite link:\n\n{invite_link}\n\n"
            f"This link will expire on {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}."
        )
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /admin command for admin functions."""
        user_id = update.effective_user.id
        
        # Check if user is an admin
        if user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(
                "You are not authorized to access admin functions."
            )
            return
        
        # Create admin menu
        keyboard = [
            [
                InlineKeyboardButton("Generate Invite", callback_data="admin_invite"),
                InlineKeyboardButton("User Stats", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("System Status", callback_data="admin_status"),
                InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Admin Panel - Select an option:",
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
        
        # Answer the callback query to stop the loading animation
        await query.answer()
        
        # Handle different callback data
        if query.data == "back_to_menu":
            # Send main menu
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
            
            await query.edit_message_text(
                "Please select an option:",
                reply_markup=reply_markup
            )
        
        elif query.data == "menu_trend":
            # Prompt for symbol
            keyboard = [
                [
                    InlineKeyboardButton("NIFTY", callback_data="trend_NIFTY"),
                    InlineKeyboardButton("BANKNIFTY", callback_data="trend_BANKNIFTY")
                ],
                [
                    InlineKeyboardButton("FINNIFTY", callback_data="trend_FINNIFTY"),
                    InlineKeyboardButton("SENSEX", callback_data="trend_SENSEX")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Select a symbol for trend analysis:",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("trend_"):
            # Extract symbol
            symbol = query.data.split("_")[1]
            
            # Send typing action
            await query.message.chat.send_action("typing")
            
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
                    await query.message.reply_photo(
                        photo=open(chart_path, 'rb'),
                        caption=report,
                        parse_mode='Markdown'
                    )
                    
                    # Clean up
                    os.unlink(chart_path)
                else:
                    # Send text only if chart generation failed
                    await query.message.reply_text(
                        report,
                        parse_mode='Markdown'
                    )
                
                # Add back to menu button
                keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    "What would you like to do next?",
                    reply_markup=reply_markup
                )
                
                # Store interaction
                self._store_user_interaction(user_id, f"Requested trend analysis for {symbol}")
                
            except Exception as e:
                logger.error(f"Error in trend callback: {e}")
                await query.message.reply_text(
                    f"Sorry, I encountered an error while analyzing {symbol}. Please try again later."
                )
        
        elif query.data == "menu_options":
            # Prompt for symbol
            keyboard = [
                [
                    InlineKeyboardButton("NIFTY", callback_data="options_NIFTY"),
                    InlineKeyboardButton("BANKNIFTY", callback_data="options_BANKNIFTY")
                ],
                [
                    InlineKeyboardButton("FINNIFTY", callback_data="options_FINNIFTY"),
                    InlineKeyboardButton("SENSEX", callback_data="options_SENSEX")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Select a symbol for option chain analysis:",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("options_"):
            # Extract symbol
            symbol = query.data.split("_")[1]
            
            # Send typing action
            await query.message.chat.send_action("typing")
            
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
                    await query.message.reply_photo(
                        photo=open(chart_path, 'rb'),
                        caption=summary,
                        parse_mode='Markdown'
                    )
                    
                    # Clean up
                    os.unlink(chart_path)
                else:
                    # Send text only if chart generation failed
                    await query.message.reply_text(
                        summary,
                        parse_mode='Markdown'
                    )
                
                # Add back to menu button
                keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    "What would you like to do next?",
                    reply_markup=reply_markup
                )
                
                # Store interaction
                self._store_user_interaction(user_id, f"Requested option chain analysis for {symbol}")
                
            except Exception as e:
                logger.error(f"Error in options callback: {e}")
                await query.message.reply_text(
                    f"Sorry, I encountered an error while analyzing {symbol} options. Please try again later."
                )
        
        elif query.data == "menu_ideas":
            # Prompt for symbol
            keyboard = [
                [
                    InlineKeyboardButton("NIFTY", callback_data="ideas_NIFTY"),
                    InlineKeyboardButton("BANKNIFTY", callback_data="ideas_BANKNIFTY")
                ],
                [
                    InlineKeyboardButton("FINNIFTY", callback_data="ideas_FINNIFTY"),
                    InlineKeyboardButton("SENSEX", callback_data="ideas_SENSEX")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Select a symbol for trade ideas:",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("ideas_"):
            # Extract symbol
            symbol = query.data.split("_")[1]
            
            # Send typing action
            await query.message.chat.send_action("typing")
            
            try:
                # Generate trade ideas
                ideas = self.rule_engine.generate_trade_ideas(symbol, 3)
                
                # Enhance with ML if enabled
                if config.ENABLE_ML_ENGINE:
                    ideas = self.ml_engine.enhance_trade_ideas(ideas)
                
                if not ideas:
                    await query.message.reply_text(
                        f"Sorry, I couldn't generate any trade ideas for {symbol} at this time. Please try again later."
                    )
                    return
                
                # Send each idea as a separate message
                for idea in ideas:
                    formatted_idea = self.report_formatter.format_trade_idea(idea)
                    
                    # Add view chart button
                    keyboard = [
                        [
                            InlineKeyboardButton("View Chart", callback_data=f"chart_{symbol}_{idea['strike']}_{idea['option_type']}")
                        ],
                        [
                            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.message.reply_text(
                        formatted_idea,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                
                # Store interaction
                self._store_user_interaction(user_id, f"Requested trade ideas for {symbol}")
                
            except Exception as e:
                logger.error(f"Error in ideas callback: {e}")
                await query.message.reply_text(
                    f"Sorry, I encountered an error while generating trade ideas for {symbol}. Please try again later."
                )
        
        elif query.data == "menu_heatmap":
            # Prompt for symbol
            keyboard = [
                [
                    InlineKeyboardButton("NIFTY", callback_data="heatmap_NIFTY"),
                    InlineKeyboardButton("BANKNIFTY", callback_data="heatmap_BANKNIFTY")
                ],
                [
                    InlineKeyboardButton("FINNIFTY", callback_data="heatmap_FINNIFTY"),
                    InlineKeyboardButton("SENSEX", callback_data="heatmap_SENSEX")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Select a symbol for OI heatmap:",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("heatmap_"):
            # Extract symbol
            symbol = query.data.split("_")[1]
            
            # Send typing action
            await query.message.chat.send_action("typing")
            
            try:
                # Generate heatmap data
                heatmap_data = self.rule_engine.generate_oi_heatmap_data(symbol)
                
                # Generate heatmap visualization
                heatmap_base64 = self.chart_generator.generate_oi_heatmap(heatmap_data)
                
                # Create temporary file for heatmap
                if heatmap_base64:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        temp_file.write(base64.b64decode(heatmap_base64))
                        heatmap_path = temp_file.name
                    
                    # Send heatmap with caption
                    await query.message.reply_photo(
                        photo=open(heatmap_path, 'rb'),
                        caption=f"🔥 *{symbol} - Open Interest & Volume Heatmap* 🔥\n\n"
                                f"This heatmap shows the distribution of open interest and volume across different strike prices.\n\n"
                                f"_Updated: {heatmap_data['timestamp']}_",
                        parse_mode='Markdown'
                    )
                    
                    # Clean up
                    os.unlink(heatmap_path)
                else:
                    # Send text only if heatmap generation failed
                    await query.message.reply_text(
                        f"Sorry, I couldn't generate the heatmap for {symbol} at this time. Please try again later."
                    )
                
                # Add back to menu button
                keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    "What would you like to do next?",
                    reply_markup=reply_markup
                )
                
                # Store interaction
                self._store_user_interaction(user_id, f"Requested OI heatmap for {symbol}")
                
            except Exception as e:
                logger.error(f"Error in heatmap callback: {e}")
                await query.message.reply_text(
                    f"Sorry, I encountered an error while generating the heatmap for {symbol}. Please try again later."
                )
        
        elif query.data == "menu_summary":
            # Prompt for symbol
            keyboard = [
                [
                    InlineKeyboardButton("NIFTY", callback_data="summary_NIFTY"),
                    InlineKeyboardButton("BANKNIFTY", callback_data="summary_BANKNIFTY")
                ],
                [
                    InlineKeyboardButton("FINNIFTY", callback_data="summary_FINNIFTY"),
                    InlineKeyboardButton("SENSEX", callback_data="summary_SENSEX")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Select a symbol for daily summary:",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("summary_"):
            # Extract symbol
            symbol = query.data.split("_")[1]
            
            # Send typing action
            await query.message.chat.send_action("typing")
            
            try:
                # Get trend analysis
                trend_analysis = self.rule_engine.analyze_market_trend(symbol)
                
                # Get option chain analysis
                option_analysis = self.rule_engine.analyze_option_chain(symbol)
                
                # Generate trade ideas
                trade_ideas = self.rule_engine.generate_trade_ideas(symbol, 3)
                
                # Format daily summary
                summary = self.report_formatter.format_daily_summary(
                    symbol, trend_analysis, option_analysis, trade_ideas
                )
                
                # Send summary
                await query.message.reply_text(
                    summary,
                    parse_mode='Markdown'
                )
                
                # Add back to menu button
                keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    "What would you like to do next?",
                    reply_markup=reply_markup
                )
                
                # Store interaction
                self._store_user_interaction(user_id, f"Requested daily summary for {symbol}")
                
            except Exception as e:
                logger.error(f"Error in summary callback: {e}")
                await query.message.reply_text(
                    f"Sorry, I encountered an error while generating the summary for {symbol}. Please try again later."
                )
        
        elif query.data == "menu_help":
            # Show help message
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
            
            await query.edit_message_text(
                help_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]])
            )
        
        elif query.data.startswith("chart_"):
            # Extract chart details
            parts = query.data.split("_")
            symbol = parts[1]
            strike = float(parts[2])
            option_type = parts[3]
            
            # Send typing action
            await query.message.chat.send_action("typing")
            
            try:
                # Get trend data
                trend_data = self.market_data.get_market_trend(symbol)
                
                # Create a simple chart for the option
                fig = go.Figure()
                
                # Generate simulated price data
                days = 30
                dates = pd.date_range(end=pd.Timestamp.now(), periods=days)
                
                # Create price trend based on option type
                if option_type.upper() == "CE":
                    # Call option - price increases if underlying increases
                    if trend_data['trend'] == 'bullish':
                        # Upward trend with some noise
                        change_factor = np.linspace(0.8, 1.0, days) + np.random.normal(0, 0.02, days)
                    else:
                        # Downward trend with some noise
                        change_factor = np.linspace(1.2, 1.0, days) + np.random.normal(0, 0.02, days)
                else:
                    # Put option - price increases if underlying decreases
                    if trend_data['trend'] == 'bearish':
                        # Upward trend with some noise
                        change_factor = np.linspace(0.8, 1.0, days) + np.random.normal(0, 0.02, days)
                    else:
                        # Downward trend with some noise
                        change_factor = np.linspace(1.2, 1.0, days) + np.random.normal(0, 0.02, days)
                
                # Get option data from option chain
                option_chain = self.market_data.get_option_chain(symbol)
                option_row = option_chain[option_chain['strike'] == strike].iloc[0]
                
                if option_type.upper() == "CE":
                    current_premium = option_row['call_premium']
                else:
                    current_premium = option_row['put_premium']
                
                # Calculate prices
                prices = current_premium / np.cumprod(change_factor)
                
                # Create DataFrame
                df = pd.DataFrame({
                    'Date': dates,
                    'Price': prices
                })
                
                # Add trace
                fig.add_trace(go.Scatter(
                    x=df['Date'],
                    y=df['Price'],
                    mode='lines',
                    name=f"{symbol} {strike} {option_type}"
                ))
                
                # Add current price marker
                fig.add_trace(go.Scatter(
                    x=[df['Date'].iloc[-1]],
                    y=[current_premium],
                    mode='markers',
                    marker=dict(size=10, color='red'),
                    name='Current Premium'
                ))
                
                # Update layout
                fig.update_layout(
                    title=f"{symbol} {strike} {option_type} - Premium History",
                    height=600,
                    width=1000,
                    template="plotly_white",
                    xaxis_title="Date",
                    yaxis_title="Premium"
                )
                
                # Create temporary file for chart
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    fig.write_image(temp_file.name)
                    chart_path = temp_file.name
                
                # Send chart
                await query.message.reply_photo(
                    photo=open(chart_path, 'rb'),
                    caption=f"📊 *{symbol} {strike} {option_type} - Premium Chart*\n\n"
                            f"Current Premium: {current_premium:.2f}\n"
                            f"IV: {option_row['call_iv' if option_type.upper() == 'CE' else 'put_iv']:.2%}\n"
                            f"Delta: {option_row['call_delta' if option_type.upper() == 'CE' else 'put_delta']:.2f}\n\n"
                            f"_Note: This is a simulated chart for demonstration purposes._",
                    parse_mode='Markdown'
                )
                
                # Clean up
                os.unlink(chart_path)
                
                # Store interaction
                self._store_user_interaction(user_id, f"Viewed chart for {symbol} {strike} {option_type}")
                
            except Exception as e:
                logger.error(f"Error in chart callback: {e}")
                await query.message.reply_text(
                    f"Sorry, I encountered an error while generating the chart. Please try again later."
                )
        
        elif query.data == "admin_invite":
            # Check if user is an admin
            if user_id not in config.ADMIN_USER_IDS:
                await query.message.reply_text(
                    "You are not authorized to generate invite links."
                )
                return
            
            # Generate a new invite link
            invite_token = generate_invite_link()
            
            # Set expiry time (24 hours)
            expiry_time = datetime.now() + timedelta(hours=24)
            
            # Store the invite link
            self.invite_links[invite_token] = expiry_time
            
            # Create the full invite link
            bot_username = context.bot.username
            invite_link = f"https://t.me/{bot_username}?start={invite_token}"
            
            await query.message.reply_text(
                f"Here is your invite link:\n\n{invite_link}\n\n"
                f"This link will expire on {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}."
            )
        
        elif query.data == "admin_stats":
            # Check if user is an admin
            if user_id not in config.ADMIN_USER_IDS:
                await query.message.reply_text(
                    "You are not authorized to view user statistics."
                )
                return
            
            # Generate user statistics
            user_count = len(config.ALLOWED_USERS)
            active_users = sum(1 for user_id, expiry in config.ALLOWED_USERS.items() if expiry > datetime.now())
            
            stats = (
                "📊 *User Statistics* 📊\n\n"
                f"Total Users: {user_count}\n"
                f"Active Users: {active_users}\n"
                f"Expired Users: {user_count - active_users}\n\n"
                f"Active Invite Links: {len(self.invite_links)}\n\n"
                f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            )
            
            await query.message.reply_text(
                stats,
                parse_mode='Markdown'
            )
        
        elif query.data == "admin_status":
            # Check if user is an admin
            if user_id not in config.ADMIN_USER_IDS:
                await query.message.reply_text(
                    "You are not authorized to view system status."
                )
                return
            
            # Generate system status
            status = (
                "🖥️ *System Status* 🖥️\n\n"
                f"Rule Engine: {'Enabled' if config.ENABLE_RULE_ENGINE else 'Disabled'}\n"
                f"ML Engine: {'Enabled' if config.ENABLE_ML_ENGINE else 'Disabled'}\n"
                f"Real-time Alerts: {'Enabled' if config.ENABLE_REAL_TIME_ALERTS else 'Disabled'}\n\n"
                f"External AI: {'Enabled' if config.USE_EXTERNAL_AI else 'Disabled'}\n"
                f"Cache: {'Redis' if config.USE_REDIS else 'SQLite'}\n\n"
                f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            )
            
            await query.message.reply_text(
                status,
                parse_mode='Markdown'
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages."""
        # Check if this is an invite token
        message_text = update.message.text.strip()
        
        if message_text in self.invite_links:
            user_id = update.effective_user.id
            
            if datetime.now() < self.invite_links[message_text]:
                # Valid invite, add user to allowed users
                expiry = add_authorized_user(user_id, config.ALLOWED_USERS)
                
                # Remove the used invite link
                del self.invite_links[message_text]
                
                await update.message.reply_text(
                    f"Welcome {update.effective_user.first_name}! You have been granted access to the Options Trading Bot. "
                    f"Your access will expire on {expiry.strftime('%Y-%m-%d')}.\n\n"
                    f"Type /help to see available commands."
                )
                
                # Send welcome menu
                await self._send_welcome_menu(update)
            else:
                # Expired invite
                del self.invite_links[message_text]
                await update.message.reply_text(
                    "This invite token has expired. Please request a new one."
                )
        else:
            # For other messages, suggest using commands
            await update.message.reply_text(
                "I can help you with options trading insights. Please use commands like /help, /trend, or /ideas."
            )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the dispatcher."""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Send error message to user if possible
        if update and hasattr(update, 'effective_message'):
            await update.effective_message.reply_text(
                "Sorry, an error occurred while processing your request. Please try again later."
            )
    
    def _store_user_interaction(self, user_id: int, interaction: str):
        """Store user interaction for tracking."""
        if user_id not in self.user_interactions:
            self.user_interactions[user_id] = []
        
        # Add new interaction
        self.user_interactions[user_id].append({
            'timestamp': datetime.now(),
            'interaction': interaction
        })
        
        # Keep only the last N interactions
        if len(self.user_interactions[user_id]) > config.MAX_INTERACTIONS_STORED:
            self.user_interactions[user_id] = self.user_interactions[user_id][-config.MAX_INTERACTIONS_STORED:]
    
    def run(self):
        """Run the bot."""
        logger.info("Starting Options Trading Bot")
        self.application.run_polling()


def main():
    """Main function to run the bot."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Create models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
    
    # Initialize and run the bot
    bot = OptionsTradingBot()
    bot.run()


if __name__ == "__main__":
    main()
