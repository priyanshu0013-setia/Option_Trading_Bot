"""
Utility functions for the AI Options Trading Bot.
"""
import logging
import os
from datetime import datetime, timedelta
import uuid

# Set up logging
def setup_logging(log_file, log_level):
    """Set up logging configuration."""
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('options_bot')

# Access control functions
def generate_invite_link():
    """Generate a unique, single-use invite link."""
    return str(uuid.uuid4())

def is_user_authorized(user_id, allowed_users):
    """Check if a user is authorized to use the bot."""
    if user_id in allowed_users:
        expiry_time = allowed_users[user_id]
        if expiry_time > datetime.now():
            return True
        else:
            # Expired access
            return False
    return False

def add_authorized_user(user_id, allowed_users, days_valid=30):
    """Add a user to the authorized users list."""
    expiry_time = datetime.now() + timedelta(days=days_valid)
    allowed_users[user_id] = expiry_time
    return expiry_time

# Rate limiting
class RateLimiter:
    """Simple rate limiter to prevent abuse."""
    def __init__(self, max_calls, time_frame):
        self.max_calls = max_calls  # Maximum number of calls allowed
        self.time_frame = time_frame  # Time frame in seconds
        self.calls = {}  # user_id -> list of timestamps
    
    def is_allowed(self, user_id):
        """Check if the user is allowed to make another call."""
        now = datetime.now()
        if user_id not in self.calls:
            self.calls[user_id] = []
        
        # Remove timestamps older than the time frame
        self.calls[user_id] = [ts for ts in self.calls[user_id] 
                              if now - ts < timedelta(seconds=self.time_frame)]
        
        # Check if the user has made too many calls
        if len(self.calls[user_id]) >= self.max_calls:
            return False
        
        # Add the current timestamp
        self.calls[user_id].append(now)
        return True

# Formatting helpers
def format_currency(value):
    """Format a value as currency."""
    return f"₹{value:,.2f}"

def format_percentage(value):
    """Format a value as percentage."""
    return f"{value:.2f}%"

def format_trade_idea(symbol, option_type, strike, entry, target, stop_loss, delta=None, oi_change=None):
    """Format a trade idea message."""
    trend = "Bullish" if option_type.upper() == "CE" else "Bearish"
    
    message = f"📍 {symbol} {strike} {option_type} – {trend} Trend\n"
    message += f"🔹 Entry: {format_currency(entry)} | Target: {format_currency(target)} | SL: {format_currency(stop_loss)}\n"
    
    if delta is not None or oi_change is not None:
        message += "📈 "
        if delta is not None:
            message += f"Delta: {delta:.2f}"
            if oi_change is not None:
                message += " | "
        if oi_change is not None:
            direction = "↑" if oi_change > 0 else "↓"
            message += f"OI Spike: {direction}{abs(oi_change):.0f}%"
    
    return message
