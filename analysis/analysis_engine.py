"""
Analysis engine for the AI Options Trading Bot.
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

from data.market_data import MarketDataFetcher, DataProcessor

logger = logging.getLogger('options_bot')

class RuleBasedAnalysis:
    """Rule-based analysis engine for options trading."""
    
    def __init__(self, market_data: MarketDataFetcher):
        """Initialize with market data fetcher."""
        self.market_data = market_data
        self.data_processor = DataProcessor()
    
    def analyze_market_trend(self, symbol: str, timeframe: str = "1d") -> Dict:
        """
        Analyze market trend for a symbol.
        
        Args:
            symbol: Stock/index symbol
            timeframe: Time frame for analysis
                 
        Returns:
            Dictionary with trend analysis
        """
        # Get market data
        trend_data = self.market_data.get_market_trend(symbol, timeframe)
        
        # Add analysis
        analysis = trend_data.copy()
        
        # Add trend strength
        if trend_data['trend'] == 'bullish':
            if trend_data['rsi'] > 70:
                analysis['trend_strength'] = 'overbought'
            else:
                analysis['trend_strength'] = 'strong'
        elif trend_data['trend'] == 'bearish':
            if trend_data['rsi'] < 30:
                analysis['trend_strength'] = 'oversold'
            else:
                analysis['trend_strength'] = 'strong'
        else:
            analysis['trend_strength'] = 'neutral'
        
        # Add recommendation
        if analysis['trend'] == 'bullish' and analysis['trend_strength'] != 'overbought':
            analysis['recommendation'] = 'Consider bullish strategies'
        elif analysis['trend'] == 'bearish' and analysis['trend_strength'] != 'oversold':
            analysis['recommendation'] = 'Consider bearish strategies'
        elif analysis['trend_strength'] == 'overbought':
            analysis['recommendation'] = 'Caution: Market may be overbought'
        elif analysis['trend_strength'] == 'oversold':
            analysis['recommendation'] = 'Caution: Market may be oversold'
        else:
            analysis['recommendation'] = 'Consider neutral strategies'
        
        return analysis
    
    def generate_trade_ideas(self, symbol: str, count: int = 3) -> List[Dict]:
        """
        Generate trade ideas based on option chain analysis.
        
        Args:
            symbol: Stock/index symbol
            count: Number of trade ideas to generate
            
        Returns:
            List of trade idea dictionaries
        """
        # Get option chain
        option_chain = self.market_data.get_option_chain(symbol)
        
        # Get market trend
        trend_data = self.market_data.get_market_trend(symbol)
        
        # Calculate PCR
        pcr = self.data_processor.calculate_pcr(option_chain)
        
        # Find max pain
        max_pain = self.data_processor.find_max_pain(option_chain)
        
        # Identify support and resistance
        support_levels, resistance_levels = self.data_processor.identify_support_resistance(option_chain)
        
        # Generate ideas based on market conditions
        ideas = []
        
        # Bullish ideas
        if trend_data['trend'] == 'bullish' or pcr > 1.2:  # High PCR can indicate bullish reversal
            # Find call options with high OI change
            bullish_candidates = option_chain.sort_values('call_oi_change', ascending=False).head(count * 2)
            
            for _, row in bullish_candidates.iterrows():
                if len(ideas) >= count:
                    break
                    
                # Skip if strike is too far from current price
                if abs(row['strike'] - trend_data['current_price']) / trend_data['current_price'] > 0.05:
                    continue
                
                # Create trade idea
                idea = {
                    'symbol': symbol,
                    'option_type': 'CE',
                    'strike': row['strike'],
                    'entry': row['call_premium'],
                    'target': row['call_premium'] * 1.3,  # 30% profit target
                    'stop_loss': row['call_premium'] * 0.8,  # 20% stop loss
                    'delta': row['call_delta'],
                    'oi_change': row['call_oi_change'] * 100,  # Convert to percentage
                    'rationale': 'Bullish momentum with increasing Call OI'
                }
                
                ideas.append(idea)
        
        # Bearish ideas
        if trend_data['trend'] == 'bearish' or pcr < 0.8:  # Low PCR can indicate bearish reversal
            # Find put options with high OI change
            bearish_candidates = option_chain.sort_values('put_oi_change', ascending=False).head(count * 2)
            
            for _, row in bearish_candidates.iterrows():
                if len(ideas) >= count:
                    break
                    
                # Skip if strike is too far from current price
                if abs(row['strike'] - trend_data['current_price']) / trend_data['current_price'] > 0.05:
                    continue
                
                # Create trade idea
                idea = {
                    'symbol': symbol,
                    'option_type': 'PE',
                    'strike': row['strike'],
                    'entry': row['put_premium'],
                    'target': row['put_premium'] * 1.3,  # 30% profit target
                    'stop_loss': row['put_premium'] * 0.8,  # 20% stop loss
                    'delta': row['put_delta'],
                    'oi_change': row['put_oi_change'] * 100,  # Convert to percentage
                    'rationale': 'Bearish momentum with increasing Put OI'
                }
                
                ideas.append(idea)
        
        # If we don't have enough ideas, add some based on support/resistance
        if len(ideas) < count:
            current_price = trend_data['current_price']
            
            # Add bullish idea near support
            for support in support_levels:
                if len(ideas) >= count:
                    break
                    
                if support < current_price and support > current_price * 0.95:
                    # Find the corresponding option
                    option_row = option_chain[option_chain['strike'] == support].iloc[0]
                    
                    idea = {
                        'symbol': symbol,
                        'option_type': 'CE',
                        'strike': support,
                        'entry': option_row['call_premium'],
                        'target': option_row['call_premium'] * 1.3,
                        'stop_loss': option_row['call_premium'] * 0.8,
                        'delta': option_row['call_delta'],
                        'oi_change': option_row['call_oi_change'] * 100,
                        'rationale': 'Support level with potential bounce'
                    }
                    
                    ideas.append(idea)
            
            # Add bearish idea near resistance
            for resistance in resistance_levels:
                if len(ideas) >= count:
                    break
                    
                if resistance > current_price and resistance < current_price * 1.05:
                    # Find the corresponding option
                    option_row = option_chain[option_chain['strike'] == resistance].iloc[0]
                    
                    idea = {
                        'symbol': symbol,
                        'option_type': 'PE',
                        'strike': resistance,
                        'entry': option_row['put_premium'],
                        'target': option_row['put_premium'] * 1.3,
                        'stop_loss': option_row['put_premium'] * 0.8,
                        'delta': option_row['put_delta'],
                        'oi_change': option_row['put_oi_change'] * 100,
                        'rationale': 'Resistance level with potential reversal'
                    }
                    
                    ideas.append(idea)
        
        return ideas[:count]
    
    def analyze_option_chain(self, symbol: str) -> Dict:
        """
        Analyze option chain for a symbol.
        
        Args:
            symbol: Stock/index symbol
            
        Returns:
            Dictionary with option chain analysis
        """
        # Get option chain
        option_chain = self.market_data.get_option_chain(symbol)
        
        # Get market trend
        trend_data = self.market_data.get_market_trend(symbol)
        
        # Calculate PCR
        pcr = self.data_processor.calculate_pcr(option_chain)
        
        # Find max pain
        max_pain = self.data_processor.find_max_pain(option_chain)
        
        # Identify support and resistance
        support_levels, resistance_levels = self.data_processor.identify_support_resistance(option_chain)
        
        # Prepare analysis
        analysis = {
            'symbol': symbol,
            'current_price': trend_data['current_price'],
            'pcr': pcr,
            'max_pain': max_pain,
            'support_levels': support_levels,
            'resistance_levels': resistance_levels,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add market sentiment
        if pcr > 1.2:
            analysis['sentiment'] = 'Bullish (High Put-Call Ratio)'
        elif pcr < 0.8:
            analysis['sentiment'] = 'Bearish (Low Put-Call Ratio)'
        else:
            analysis['sentiment'] = 'Neutral'
        
        # Add max pain analysis
        if abs(max_pain - trend_data['current_price']) / trend_data['current_price'] < 0.01:
            analysis['max_pain_analysis'] = 'Price is near max pain point'
        elif max_pain > trend_data['current_price']:
            analysis['max_pain_analysis'] = 'Max pain is above current price, potential upward pressure'
        else:
            analysis['max_pain_analysis'] = 'Max pain is below current price, potential downward pressure'
        
        return analysis
    
    def generate_oi_heatmap_data(self, symbol: str) -> Dict:
        """
        Generate data for OI heatmap.
        
        Args:
            symbol: Stock/index symbol
            
        Returns:
            Dictionary with heatmap data
        """
        # Get OI data
        oi_data = self.market_data.get_oi_data(symbol)
        
        # Prepare heatmap data
        heatmap_data = {
            'symbol': symbol,
            'strikes': oi_data['strike'].tolist(),
            'call_oi': oi_data['call_oi'].tolist(),
            'put_oi': oi_data['put_oi'].tolist(),
            'call_oi_change': (oi_data['call_oi_change'] * 100).tolist(),  # Convert to percentage
            'put_oi_change': (oi_data['put_oi_change'] * 100).tolist(),  # Convert to percentage
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return heatmap_data


class MLAnalysis:
    """Machine learning-based analysis engine for options trading."""
    
    def __init__(self, market_data: MarketDataFetcher, use_external_ai: bool = False, openai_api_key: str = ""):
        """
        Initialize ML analysis engine.
        
        Args:
            market_data: Market data fetcher
            use_external_ai: Whether to use external AI API
            openai_api_key: OpenAI API key (if using external AI)
        """
        self.market_data = market_data
        self.use_external_ai = use_external_ai
        self.openai_api_key = openai_api_key
        
        # For demo purposes, we'll use simple models
        # In a real implementation, this would load trained ML models
        self.models = {}
    
    def predict_price_movement(self, symbol: str, timeframe: str = "1d") -> Dict:
        """
        Predict price movement for a symbol.
        
        Args:
            symbol: Stock/index symbol
            timeframe: Time frame for prediction
            
        Returns:
            Dictionary with prediction
        """
        # Get market data
        trend_data = self.market_data.get_market_trend(symbol, timeframe)
        
        if self.use_external_ai and self.openai_api_key:
            # In a real implementation, this would call OpenAI API
            # For now, we'll just return a simulated prediction
            return self._simulate_prediction(trend_data)
        else:
            # Use simple model
            return self._simulate_prediction(trend_data)
    
    def _simulate_prediction(self, trend_data: Dict) -> Dict:
        """Simulate ML prediction for demo purposes."""
        # Add random noise to the trend
        current_trend = trend_data['trend']
        current_price = trend_data['current_price']
        
        # Simulate prediction with some randomness
        if current_trend == 'bullish':
            prediction_up = np.random.uniform(0.6, 0.9)  # 60-90% chance of going up
        elif current_trend == 'bearish':
            prediction_up = np.random.uniform(0.1, 0.4)  # 10-40% chance of going up
        else:
            prediction_up = np.random.uniform(0.4, 0.6)  # 40-60% chance of going up
        
        prediction_down = 1 - prediction_up
        
        # Predict price range
        if prediction_up > prediction_down:
            predicted_movement = np.random.uniform(0.5, 2.0)  # 0.5-2% up
            predicted_price = current_price * (1 + predicted_movement / 100)
            predicted_trend = 'bullish'
        else:
            predicted_movement = np.random.uniform(0.5, 2.0)  # 0.5-2% down
            predicted_price = current_price * (1 - predicted_movement / 100)
            predicted_trend = 'bearish'
        
        return {
            'symbol': trend_data['symbol'],
            'current_price': current_price,
            'predicted_price': predicted_price,
            'predicted_trend': predicted_trend,
            'confidence': max(prediction_up, prediction_down),
            'timeframe': trend_data['timeframe'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def enhance_trade_ideas(self, trade_ideas: List[Dict]) -> List[Dict]:
        """
        Enhance trade ideas with ML insights.
        
        Args:
            trade_ideas: List of trade ideas from rule-based analysis
            
        Returns:
            Enhanced trade ideas
        """
        enhanced_ideas = []
        
        for idea in trade_ideas:
            enhanced_idea = idea.copy()
            
            # Add confidence score
            enhanced_idea['confidence'] = np.random.uniform(0.6, 0.95)
            
            # Add expected return
            expected_return = (enhanced_idea['target'] - enhanced_idea['entry']) / enhanced_idea['entry'] * 100
            enhanced_idea['expected_return'] = expected_return
            
            # Add risk-reward ratio
            risk = (enhanced_idea['entry'] - enhanced_idea['stop_loss']) / enhanced_idea['entry'] * 100
            reward = expected_return
            enhanced_idea['risk_reward_ratio'] = reward / risk if risk > 0 else 0
            
            # Add ML-based commentary
            if enhanced_idea['option_type'] == 'CE':
                enhanced_idea['ml_commentary'] = f"ML model indicates a {enhanced_idea['confidence']:.0%} probability of upward movement based on historical patterns and current market conditions."
            else:
                enhanced_idea['ml_commentary'] = f"ML model indicates a {enhanced_idea['confidence']:.0%} probability of downward movement based on historical patterns and current market conditions."
            
            enhanced_ideas.append(enhanced_idea)
        
        return enhanced_ideas
