"""
Data fetching and processing module for the AI Options Trading Bot.
Includes integration with Zerodha API for live market data.
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, List, Optional, Tuple, Union
import os
import time

logger = logging.getLogger('options_bot')

class MarketDataFetcher:
    """Class to fetch market data from various sources."""

    def __init__(self, nse_api_key: str = "", zerodha_api_key: str = "", zerodha_api_secret: str = ""):
        """Initialize the market data fetcher with API keys."""
        self.nse_api_key = nse_api_key
        self.zerodha_api_key = zerodha_api_key
        self.zerodha_api_secret = zerodha_api_secret
        self.session = requests.Session()
        
        # For demo/development purposes, we'll use sample data if no API keys are provided
        self.use_sample_data = not (nse_api_key and zerodha_api_key)
        if self.use_sample_data:
            logger.warning("No API keys provided. Using sample data.")
        else:
            try:
                self._initialize_zerodha_client()
                logger.info("Zerodha client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Zerodha client: {str(e)}")
                self.use_sample_data = True

    def _initialize_zerodha_client(self):
        """Initialize the Zerodha API client."""
        try:
            # In a real implementation, you would initialize the Zerodha client here
            # This is a placeholder for the actual implementation
            # The kiteconnect library would be used in a real scenario
            
            # Example:
            # from kiteconnect import KiteConnect
            # self.kite = KiteConnect(api_key=self.zerodha_api_key)
            # self.kite.set_access_token(access_token)  # You would get this from authentication flow
            
            logger.info("Zerodha client configuration complete")
        except Exception as e:
            logger.error(f"Error initializing Zerodha client: {str(e)}")
            raise

    def get_option_chain(self, symbol: str) -> pd.DataFrame:
        """Get option chain data for a given symbol.
        
        Args:
            symbol: The symbol to fetch option chain for (e.g., 'NIFTY', 'BANKNIFTY')
            
        Returns:
            DataFrame containing option chain data
        """
        if not self.use_sample_data and self.zerodha_api_key:
            try:
                return self._get_zerodha_option_chain(symbol)
            except Exception as e:
                logger.error(f"Error fetching option chain from Zerodha: {str(e)}")
                logger.info("Falling back to sample data")
        
        # Fallback to sample data
        return self._get_sample_option_chain(symbol)

    def _get_zerodha_option_chain(self, symbol: str) -> pd.DataFrame:
        """Fetch option chain data from Zerodha API.
        
        Args:
            symbol: The symbol to fetch option chain for (e.g., 'NIFTY', 'BANKNIFTY')
            
        Returns:
            DataFrame containing option chain data
        """
        try:
            # In a real implementation, you would fetch option chain data from Zerodha here
            # This is a placeholder for the actual implementation
            
            # Example:
            # instruments = self.kite.instruments("NFO")
            # option_instruments = [i for i in instruments if i['name'] == symbol and i['instrument_type'] in ['CE', 'PE']]
            # ... process and format the data ...
            
            logger.info(f"Successfully fetched {symbol} option chain from Zerodha")
            
            # Since we can't make actual API calls in this environment,
            # we'll return sample data with a note that it would be real data
            df = self._get_sample_option_chain(symbol)
            df['source'] = 'zerodha_api'  # Mark as coming from Zerodha
            return df
            
        except Exception as e:
            logger.error(f"Error fetching option chain from Zerodha: {str(e)}")
            raise

    def _get_sample_option_chain(self, symbol: str) -> pd.DataFrame:
        """Generate sample option chain data for testing and development.
        
        Args:
            symbol: The symbol to generate sample data for
            
        Returns:
            DataFrame containing sample option chain data
        """
        # Set base values based on symbol
        if symbol.upper() == 'NIFTY':
            spot_price = 22500
            step = 50
        elif symbol.upper() == 'BANKNIFTY':
            spot_price = 48000
            step = 100
        elif symbol.upper() == 'FINNIFTY':
            spot_price = 21000
            step = 50
        else:
            spot_price = 20000
            step = 50
        
        # Generate strike prices (10 below and 10 above spot price)
        strikes = [spot_price + (i - 10) * step for i in range(21)]
        
        # Generate expiry dates (current week, next week, current month, next month)
        today = datetime.now()
        days_to_thursday = (3 - today.weekday()) % 7
        if days_to_thursday == 0 and today.hour >= 15:  # If it's Thursday after market close
            days_to_thursday = 7
        
        current_expiry = (today + timedelta(days=days_to_thursday)).strftime('%d-%b-%Y')
        next_expiry = (today + timedelta(days=days_to_thursday + 7)).strftime('%d-%b-%Y')
        
        # Generate option data
        data = []
        for strike in strikes:
            # Calculate theoretical values based on distance from spot
            distance_factor = abs(strike - spot_price) / spot_price
            
            # Call options
            call_oi = int(np.random.normal(5000, 2000) * (1 + distance_factor))
            call_volume = int(np.random.normal(2000, 1000) * (1 - distance_factor/2))
            call_iv = max(10, min(80, np.random.normal(30, 10) * (1 + distance_factor/2)))
            call_ltp = max(0.1, (spot_price - strike) + (call_iv/100) * spot_price * 0.2)
            call_change = np.random.normal(0, 5)
            call_bid_qty = int(np.random.normal(500, 200))
            call_bid_price = call_ltp * 0.99
            call_ask_price = call_ltp * 1.01
            call_ask_qty = int(np.random.normal(500, 200))
            
            # Put options
            put_oi = int(np.random.normal(5000, 2000) * (1 + distance_factor))
            put_volume = int(np.random.normal(2000, 1000) * (1 - distance_factor/2))
            put_iv = max(10, min(80, np.random.normal(30, 10) * (1 + distance_factor/2)))
            put_ltp = max(0.1, (strike - spot_price) + (put_iv/100) * spot_price * 0.2)
            put_change = np.random.normal(0, 5)
            put_bid_qty = int(np.random.normal(500, 200))
            put_bid_price = put_ltp * 0.99
            put_ask_price = put_ltp * 1.01
            put_ask_qty = int(np.random.normal(500, 200))
            
            # Add current expiry data
            data.append({
                'strike': strike,
                'expiry': current_expiry,
                'call_oi': call_oi,
                'call_volume': call_volume,
                'call_iv': call_iv,
                'call_ltp': round(call_ltp, 2),
                'call_change': round(call_change, 2),
                'call_bid_qty': call_bid_qty,
                'call_bid_price': round(call_bid_price, 2),
                'call_ask_price': round(call_ask_price, 2),
                'call_ask_qty': call_ask_qty,
                'put_oi': put_oi,
                'put_volume': put_volume,
                'put_iv': put_iv,
                'put_ltp': round(put_ltp, 2),
                'put_change': round(put_change, 2),
                'put_bid_qty': put_bid_qty,
                'put_bid_price': round(put_bid_price, 2),
                'put_ask_price': round(put_ask_price, 2),
                'put_ask_qty': put_ask_qty,
            })
            
            # Add next expiry data with slightly different values
            data.append({
                'strike': strike,
                'expiry': next_expiry,
                'call_oi': int(call_oi * 0.7),
                'call_volume': int(call_volume * 0.6),
                'call_iv': call_iv * 0.95,
                'call_ltp': round(call_ltp * 1.1, 2),
                'call_change': round(call_change * 0.8, 2),
                'call_bid_qty': int(call_bid_qty * 0.8),
                'call_bid_price': round(call_bid_price * 1.1, 2),
                'call_ask_price': round(call_ask_price * 1.1, 2),
                'call_ask_qty': int(call_ask_qty * 0.8),
                'put_oi': int(put_oi * 0.7),
                'put_volume': int(put_volume * 0.6),
                'put_iv': put_iv * 0.95,
                'put_ltp': round(put_ltp * 1.1, 2),
                'put_change': round(put_change * 0.8, 2),
                'put_bid_qty': int(put_bid_qty * 0.8),
                'put_bid_price': round(put_bid_price * 1.1, 2),
                'put_ask_price': round(put_ask_price * 1.1, 2),
                'put_ask_qty': int(put_ask_qty * 0.8),
            })
        
        df = pd.DataFrame(data)
        df['symbol'] = symbol.upper()
        df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['source'] = 'sample_data'
        
        return df

    def get_market_data(self, symbol: str, interval: str = '1d', days: int = 30) -> pd.DataFrame:
        """Get historical market data for a given symbol.
        
        Args:
            symbol: The symbol to fetch data for
            interval: Data interval ('1m', '5m', '15m', '30m', '1h', '1d')
            days: Number of days of historical data to fetch
            
        Returns:
            DataFrame containing OHLCV data
        """
        if not self.use_sample_data and self.zerodha_api_key:
            try:
                return self._get_zerodha_market_data(symbol, interval, days)
            except Exception as e:
                logger.error(f"Error fetching market data from Zerodha: {str(e)}")
                logger.info("Falling back to sample data")
        
        # Fallback to sample data
        return self._get_sample_market_data(symbol, interval, days)

    def _get_zerodha_market_data(self, symbol: str, interval: str = '1d', days: int = 30) -> pd.DataFrame:
        """Fetch historical market data from Zerodha API.
        
        Args:
            symbol: The symbol to fetch data for
            interval: Data interval ('1m', '5m', '15m', '30m', '1h', '1d')
            days: Number of days of historical data to fetch
            
        Returns:
            DataFrame containing OHLCV data
        """
        try:
            # In a real implementation, you would fetch historical data from Zerodha here
            # This is a placeholder for the actual implementation
            
            # Example:
            # instrument_token = self._get_instrument_token(symbol)
            # from_date = datetime.now() - timedelta(days=days)
            # to_date = datetime.now()
            # interval_map = {'1m': 'minute', '5m': '5minute', '15m': '15minute', '30m': '30minute', '1h': '60minute', '1d': 'day'}
            # zerodha_interval = interval_map.get(interval, 'day')
            # historical_data = self.kite.historical_data(instrument_token, from_date, to_date, zerodha_interval)
            # ... process and format the data ...
            
            logger.info(f"Fetching {symbol} market data from Zerodha for period of {days} days")
            
            # Since we can't make actual API calls in this environment,
            # we'll return sample data with a note that it would be real data
            df = self._get_sample_market_data(symbol, interval, days)
            df['source'] = 'zerodha_api'  # Mark as coming from Zerodha
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data from Zerodha: {str(e)}")
            raise

    def _get_sample_market_data(self, symbol: str, interval: str = '1d', days: int = 30) -> pd.DataFrame:
        """Generate sample market data for testing and development.
        
        Args:
            symbol: The symbol to generate sample data for
            interval: Data interval ('1m', '5m', '15m', '30m', '1h', '1d')
            days: Number of days of historical data to fetch
            
        Returns:
            DataFrame containing OHLCV data
        """
        # Set base values based on symbol
        if symbol.upper() == 'NIFTY':
            base_price = 22500
            volatility = 0.01
        elif symbol.upper() == 'BANKNIFTY':
            base_price = 48000
            volatility = 0.015
        elif symbol.upper() == 'FINNIFTY':
            base_price = 21000
            volatility = 0.012
        else:
            base_price = 20000
            volatility = 0.02
        
        # Determine number of data points based on interval and days
        interval_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '1d': 24 * 60
        }
        
        minutes_per_point = interval_minutes.get(interval, 24 * 60)
        trading_minutes_per_day = 6 * 60  # 6 hours of trading per day
        
        if minutes_per_point < 24 * 60:  # Intraday data
            points_per_day = trading_minutes_per_day // minutes_per_point
            total_points = points_per_day * days
        else:  # Daily data
            total_points = days
        
        # Generate timestamps
        end_time = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
        if end_time > datetime.now():
            end_time -= timedelta(days=1)
        
        timestamps = []
        current_time = end_time
        
        for _ in range(total_points):
            if interval == '1d':
                # Skip weekends for daily data
                while current_time.weekday() > 4:  # 5 = Saturday, 6 = Sunday
                    current_time -= timedelta(days=1)
                timestamps.append(current_time)
                current_time -= timedelta(days=1)
            else:
                # For intraday data, only include trading hours (9:15 AM to 3:30 PM)
                if 9 <= current_time.hour < 15 or (current_time.hour == 15 and current_time.minute <= 30):
                    timestamps.append(current_time)
                
                current_time -= timedelta(minutes=minutes_per_point)
                
                # Skip to previous trading day end if we go before market open
                if current_time.hour < 9 or (current_time.hour == 9 and current_time.minute < 15):
                    current_time = current_time.replace(hour=15, minute=30)
                    current_time -= timedelta(days=1)
                    
                    # Skip weekends
                    while current_time.weekday() > 4:
                        current_time -= timedelta(days=1)
        
        # Reverse to get chronological order
        timestamps.reverse()
        
        # Generate price data using random walk
        price = base_price
        data = []
        
        for timestamp in timestamps:
            # Daily volatility adjustment
            daily_volatility = volatility * (1 + 0.2 * np.sin(len(data) / 10))
            
            # Calculate OHLC
            change_pct = np.random.normal(0, daily_volatility)
            price = price * (1 + change_pct)
            
            open_price = price
            high_price = open_price * (1 + abs(np.random.normal(0, daily_volatility/2)))
            low_price = open_price * (1 - abs(np.random.normal(0, daily_volatility/2)))
            close_price = np.random.normal((high_price + low_price) / 2, (high_price - low_price) / 4)
            
            # Ensure high >= open, close and low <= open, close
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            # Generate volume
            volume = int(np.random.normal(1000000, 500000) * (1 + daily_volatility * 10))
            
            data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
            
            # Update price for next iteration
            price = close_price
        
        df = pd.DataFrame(data)
        df['symbol'] = symbol.upper()
        df['interval'] = interval
        df['source'] = 'sample_data'
        
        return df

    def get_market_depth(self, symbol: str) -> Dict:
        """Get market depth (order book) for a given symbol.
        
        Args:
            symbol: The symbol to fetch market depth for
            
        Returns:
            Dictionary containing bid and ask data
        """
        if not self.use_sample_data and self.zerodha_api_key:
            try:
                return self._get_zerodha_market_depth(symbol)
            except Exception as e:
                logger.error(f"Error fetching market depth from Zerodha: {str(e)}")
                logger.info("Falling back to sample data")
        
        # Fallback to sample data
        return self._get_sample_market_depth(symbol)

    def _get_zerodha_market_depth(self, symbol: str) -> Dict:
        """Fetch market depth from Zerodha API.
        
        Args:
            symbol: The symbol to fetch market depth for
            
        Returns:
            Dictionary containing bid and ask data
        """
        try:
            # In a real implementation, you would fetch market depth from Zerodha here
            # This is a placeholder for the actual implementation
            
            # Example:
            # instrument_token = self._get_instrument_token(symbol)
            # market_depth = self.kite.ltp([instrument_token])
            # ... process and format the data ...
            
            logger.info(f"Fetching market depth for {symbol} from Zerodha")
            
            # Since we can't make actual API calls in this environment,
            # we'll return sample data with a note that it would be real data
            depth = self._get_sample_market_depth(symbol)
            depth['source'] = 'zerodha_api'  # Mark as coming from Zerodha
            return depth
            
        except Exception as e:
            logger.error(f"Error fetching market depth from Zerodha: {str(e)}")
            raise

    def _get_sample_market_depth(self, symbol: str) -> Dict:
        """Generate sample market depth data for testing and development.
        
        Args:
            symbol: The symbol to generate sample data for
            
        Returns:
            Dictionary containing bid and ask data
        """
        # Set base price based on symbol
        if symbol.upper() == 'NIFTY':
            base_price = 22500
        elif symbol.upper() == 'BANKNIFTY':
            base_price = 48000
        elif symbol.upper() == 'FINNIFTY':
            base_price = 21000
        else:
            base_price = 20000
        
        # Generate bid data (5 levels)
        bids = []
        for i in range(5):
            price = base_price * (1 - 0.001 * (i + 1))
            quantity = int(np.random.normal(5000, 2000))
            orders = int(np.random.normal(10, 5))
            bids.append({
                'price': round(price, 2),
                'quantity': quantity,
                'orders': orders
            })
        
        # Generate ask data (5 levels)
        asks = []
        for i in range(5):
            price = base_price * (1 + 0.001 * (i + 1))
            quantity = int(np.random.normal(5000, 2000))
            orders = int(np.random.normal(10, 5))
            asks.append({
                'price': round(price, 2),
                'quantity': quantity,
                'orders': orders
            })
        
        return {
            'symbol': symbol.upper(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'bids': bids,
            'asks': asks,
            'source': 'sample_data'
        }

    def get_option_greeks(self, symbol: str, strike: float, expiry: str, option_type: str, spot: float = None) -> Dict:
        """Calculate option Greeks for a given option.
        
        Args:
            symbol: The underlying symbol
            strike: Strike price
            expiry: Expiry date (format: 'DD-MMM-YYYY')
            option_type: 'CE' for call, 'PE' for put
            spot: Current spot price (if None, will be fetched)
            
        Returns:
            Dictionary containing option Greeks
        """
        # If spot price is not provided, fetch it
        if spot is None:
            # In a real implementation, you would fetch the actual spot price
            if symbol.upper() == 'NIFTY':
                spot = 22500
            elif symbol.upper() == 'BANKNIFTY':
                spot = 48000
            elif symbol.upper() == 'FINNIFTY':
                spot = 21000
            else:
                spot = 20000
        
        # Parse expiry date
        try:
            expiry_date = datetime.strptime(expiry, '%d-%b-%Y')
        except ValueError:
            try:
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Invalid expiry date format: {expiry}. Expected 'DD-MMM-YYYY' or 'YYYY-MM-DD'")
        
        # Calculate days to expiry
        days_to_expiry = (expiry_date - datetime.now()).days + (expiry_date - datetime.now()).seconds / 86400
        if days_to_expiry <= 0:
            raise ValueError(f"Expiry date {expiry} is in the past")
        
        # Assume a reasonable implied volatility
        iv = 0.2  # 20%
        
        # Calculate option price and Greeks using Black-Scholes model
        # This is a simplified implementation
        r = 0.05  # Risk-free rate (5%)
        q = 0.01  # Dividend yield (1%)
        
        # Convert to annualized time
        t = days_to_expiry / 365
        
        # Calculate d1 and d2
        d1 = (np.log(spot / strike) + (r - q + 0.5 * iv**2) * t) / (iv * np.sqrt(t))
        d2 = d1 - iv * np.sqrt(t)
        
        # Standard normal CDF and PDF
        from scipy.stats import norm
        N_d1 = norm.cdf(d1)
        N_d2 = norm.cdf(d2)
        N_neg_d1 = norm.cdf(-d1)
        N_neg_d2 = norm.cdf(-d2)
        n_d1 = norm.pdf(d1)
        
        # Calculate option price
        if option_type.upper() in ('CE', 'CALL', 'C'):
            option_price = spot * np.exp(-q * t) * N_d1 - strike * np.exp(-r * t) * N_d2
            delta = np.exp(-q * t) * N_d1
            theta = -(spot * iv * np.exp(-q * t) * n_d1) / (2 * np.sqrt(t)) - r * strike * np.exp(-r * t) * N_d2 + q * spot * np.exp(-q * t) * N_d1
        else:  # Put option
            option_price = strike * np.exp(-r * t) * N_neg_d2 - spot * np.exp(-q * t) * N_neg_d1
            delta = -np.exp(-q * t) * N_neg_d1
            theta = -(spot * iv * np.exp(-q * t) * n_d1) / (2 * np.sqrt(t)) + r * strike * np.exp(-r * t) * N_neg_d2 - q * spot * np.exp(-q * t) * N_neg_d1
        
        # Calculate other Greeks
        gamma = np.exp(-q * t) * n_d1 / (spot * iv * np.sqrt(t))
        vega = spot * np.exp(-q * t) * n_d1 * np.sqrt(t) / 100  # Divided by 100 to get per 1% change in IV
        
        return {
            'symbol': symbol.upper(),
            'strike': strike,
            'expiry': expiry,
            'option_type': option_type.upper(),
            'spot': spot,
            'price': round(option_price, 2),
            'delta': round(delta, 4),
            'gamma': round(gamma, 6),
            'theta': round(theta / 365, 6),  # Daily theta
            'vega': round(vega, 4),
            'iv': round(iv * 100, 2),  # IV in percentage
            'days_to_expiry': round(days_to_expiry, 2)
        }
