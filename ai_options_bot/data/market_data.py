"""
Data fetching and processing module for the AI Options Trading Bot.
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, List, Optional, Tuple, Union

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
    
    def get_option_chain(self, symbol: str) -> pd.DataFrame:
        """
        Fetch option chain data for a given symbol.
        
        Args:
            symbol: Stock/index symbol (e.g., 'NIFTY', 'BANKNIFTY')
            
        Returns:
            DataFrame containing option chain data
        """
        if self.use_sample_data:
            return self._get_sample_option_chain(symbol)
        
        try:
            # In a real implementation, this would make API calls to NSE or Zerodha
            # For now, we'll just return sample data
            logger.info(f"Fetching option chain for {symbol}")
            return self._get_sample_option_chain(symbol)
        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {e}")
            # Fallback to sample data in case of error
            return self._get_sample_option_chain(symbol)
    
    def get_market_trend(self, symbol: str, timeframe: str = "1d") -> Dict:
        """
        Get market trend data for a symbol.
        
        Args:
            symbol: Stock/index symbol
            timeframe: Time frame for the data (e.g., '1d', '1h', '15m')
            
        Returns:
            Dictionary with trend information
        """
        if self.use_sample_data:
            return self._get_sample_market_trend(symbol, timeframe)
        
        try:
            # In a real implementation, this would make API calls
            logger.info(f"Fetching market trend for {symbol} on {timeframe} timeframe")
            return self._get_sample_market_trend(symbol, timeframe)
        except Exception as e:
            logger.error(f"Error fetching market trend for {symbol}: {e}")
            return self._get_sample_market_trend(symbol, timeframe)
    
    def get_oi_data(self, symbol: str) -> pd.DataFrame:
        """
        Get open interest data for a symbol.
        
        Args:
            symbol: Stock/index symbol
            
        Returns:
            DataFrame with OI data
        """
        if self.use_sample_data:
            return self._get_sample_oi_data(symbol)
        
        try:
            # In a real implementation, this would make API calls
            logger.info(f"Fetching OI data for {symbol}")
            return self._get_sample_oi_data(symbol)
        except Exception as e:
            logger.error(f"Error fetching OI data for {symbol}: {e}")
            return self._get_sample_oi_data(symbol)
    
    def _get_sample_option_chain(self, symbol: str) -> pd.DataFrame:
        """Generate sample option chain data for development/testing."""
        # Current price for the underlying
        if symbol.upper() == "NIFTY":
            spot_price = 17500
            step = 50
        elif symbol.upper() == "BANKNIFTY":
            spot_price = 42000
            step = 100
        else:
            spot_price = 1000
            step = 20
        
        # Generate strikes around the spot price
        strikes = [spot_price + (i - 10) * step for i in range(21)]
        
        # Create sample data
        data = []
        for strike in strikes:
            # Call option
            call_premium = max(0, spot_price - strike) + np.random.randint(50, 200)
            call_oi = np.random.randint(1000, 10000) * 100
            call_volume = np.random.randint(100, 1000) * 10
            call_oi_change = np.random.uniform(-0.2, 0.3)
            call_iv = np.random.uniform(0.1, 0.4)
            call_delta = max(0, min(1, 1 - (strike - spot_price) / (spot_price * 0.1)))
            
            # Put option
            put_premium = max(0, strike - spot_price) + np.random.randint(50, 200)
            put_oi = np.random.randint(1000, 10000) * 100
            put_volume = np.random.randint(100, 1000) * 10
            put_oi_change = np.random.uniform(-0.2, 0.3)
            put_iv = np.random.uniform(0.1, 0.4)
            put_delta = max(0, min(1, (strike - spot_price) / (spot_price * 0.1)))
            
            data.append({
                'strike': strike,
                'call_premium': call_premium,
                'call_oi': call_oi,
                'call_volume': call_volume,
                'call_oi_change': call_oi_change,
                'call_iv': call_iv,
                'call_delta': call_delta,
                'put_premium': put_premium,
                'put_oi': put_oi,
                'put_volume': put_volume,
                'put_oi_change': put_oi_change,
                'put_iv': put_iv,
                'put_delta': put_delta
            })
        
        return pd.DataFrame(data)
    
    def _get_sample_market_trend(self, symbol: str, timeframe: str) -> Dict:
        """Generate sample market trend data for development/testing."""
        if symbol.upper() == "NIFTY":
            current_price = 17500
        elif symbol.upper() == "BANKNIFTY":
            current_price = 42000
        else:
            current_price = 1000
        
        # Generate random trend
        trend_direction = np.random.choice(['bullish', 'bearish', 'neutral'], p=[0.4, 0.4, 0.2])
        
        # Generate sample price movement
        if trend_direction == 'bullish':
            change_pct = np.random.uniform(0.2, 1.5)
            rsi = np.random.uniform(60, 80)
            macd = np.random.uniform(10, 30)
        elif trend_direction == 'bearish':
            change_pct = np.random.uniform(-1.5, -0.2)
            rsi = np.random.uniform(20, 40)
            macd = np.random.uniform(-30, -10)
        else:
            change_pct = np.random.uniform(-0.2, 0.2)
            rsi = np.random.uniform(40, 60)
            macd = np.random.uniform(-10, 10)
        
        change_value = current_price * change_pct / 100
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'current_price': current_price,
            'change_value': change_value,
            'change_percentage': change_pct,
            'trend': trend_direction,
            'rsi': rsi,
            'macd': macd,
            'volume': np.random.randint(1000000, 10000000),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _get_sample_oi_data(self, symbol: str) -> pd.DataFrame:
        """Generate sample OI data for development/testing."""
        if symbol.upper() == "NIFTY":
            spot_price = 17500
            step = 50
        elif symbol.upper() == "BANKNIFTY":
            spot_price = 42000
            step = 100
        else:
            spot_price = 1000
            step = 20
        
        # Generate strikes around the spot price
        strikes = [spot_price + (i - 10) * step for i in range(21)]
        
        # Create sample data
        data = []
        for strike in strikes:
            call_oi = np.random.randint(1000, 10000) * 100
            call_oi_change = np.random.uniform(-0.2, 0.3)
            put_oi = np.random.randint(1000, 10000) * 100
            put_oi_change = np.random.uniform(-0.2, 0.3)
            
            data.append({
                'strike': strike,
                'call_oi': call_oi,
                'call_oi_change': call_oi_change,
                'put_oi': put_oi,
                'put_oi_change': put_oi_change
            })
        
        return pd.DataFrame(data)


class DataProcessor:
    """Process market data for analysis."""
    
    @staticmethod
    def calculate_pcr(option_chain: pd.DataFrame) -> float:
        """
        Calculate Put-Call Ratio from option chain data.
        
        Args:
            option_chain: DataFrame with option chain data
            
        Returns:
            Put-Call Ratio value
        """
        total_put_oi = option_chain['put_oi'].sum()
        total_call_oi = option_chain['call_oi'].sum()
        
        if total_call_oi == 0:
            return 0
        
        return total_put_oi / total_call_oi
    
    @staticmethod
    def find_max_pain(option_chain: pd.DataFrame) -> float:
        """
        Calculate max pain point from option chain.
        
        Args:
            option_chain: DataFrame with option chain data
            
        Returns:
            Max pain strike price
        """
        strikes = option_chain['strike'].unique()
        
        pain_values = []
        for strike in strikes:
            # Calculate pain for this strike
            pain = 0
            
            # Add call pain (loss to call writers)
            for _, row in option_chain.iterrows():
                if row['strike'] < strike:
                    # In-the-money calls
                    pain += row['call_oi'] * (strike - row['strike'])
                
                if row['strike'] > strike:
                    # In-the-money puts
                    pain += row['put_oi'] * (row['strike'] - strike)
            
            pain_values.append((strike, pain))
        
        # Find strike with minimum pain
        min_pain_strike = min(pain_values, key=lambda x: x[1])[0]
        return min_pain_strike
    
    @staticmethod
    def identify_support_resistance(option_chain: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """
        Identify support and resistance levels from option chain.
        
        Args:
            option_chain: DataFrame with option chain data
            
        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        # Sort by OI
        high_call_oi = option_chain.sort_values('call_oi', ascending=False)['strike'].iloc[:3].tolist()
        high_put_oi = option_chain.sort_values('put_oi', ascending=False)['strike'].iloc[:3].tolist()
        
        # Resistance levels are where there's high call OI
        resistance_levels = high_call_oi
        
        # Support levels are where there's high put OI
        support_levels = high_put_oi
        
        return support_levels, resistance_levels
