"""
Visualization module for the AI Options Trading Bot.
"""
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import base64
from typing import Dict, List, Optional, Tuple, Union
import logging

logger = logging.getLogger('options_bot')

class ChartGenerator:
    """Generate charts and visualizations for the bot."""
    
    @staticmethod
    def generate_oi_heatmap(heatmap_data: Dict) -> str:
        """
        Generate OI heatmap visualization.
        
        Args:
            heatmap_data: Dictionary with heatmap data
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Extract data
            strikes = heatmap_data['strikes']
            call_oi = heatmap_data['call_oi']
            put_oi = heatmap_data['put_oi']
            call_oi_change = heatmap_data['call_oi_change']
            put_oi_change = heatmap_data['put_oi_change']
            symbol = heatmap_data['symbol']
            
            # Create figure with subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("Call OI", "Put OI", "Call OI Change %", "Put OI Change %"),
                shared_xaxes=True
            )
            
            # Add traces
            fig.add_trace(go.Bar(x=strikes, y=call_oi, name="Call OI", marker_color='green'), row=1, col=1)
            fig.add_trace(go.Bar(x=strikes, y=put_oi, name="Put OI", marker_color='red'), row=1, col=2)
            
            # Add OI change traces with color based on positive/negative
            call_colors = ['green' if x >= 0 else 'red' for x in call_oi_change]
            put_colors = ['green' if x >= 0 else 'red' for x in put_oi_change]
            
            fig.add_trace(go.Bar(x=strikes, y=call_oi_change, name="Call OI Change %", marker_color=call_colors), row=2, col=1)
            fig.add_trace(go.Bar(x=strikes, y=put_oi_change, name="Put OI Change %", marker_color=put_colors), row=2, col=2)
            
            # Update layout
            fig.update_layout(
                title=f"{symbol} - Open Interest Analysis",
                height=800,
                width=1000,
                showlegend=False,
                template="plotly_white"
            )
            
            # Convert to base64 image
            img_bytes = io.BytesIO()
            fig.write_image(img_bytes, format='png')
            img_bytes.seek(0)
            img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Error generating OI heatmap: {e}")
            return ""
    
    @staticmethod
    def generate_trend_chart(trend_data: Dict) -> str:
        """
        Generate trend chart visualization.
        
        Args:
            trend_data: Dictionary with trend data
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            # For a real implementation, this would use historical price data
            # For demo purposes, we'll create a simulated price chart
            
            symbol = trend_data['symbol']
            current_price = trend_data['current_price']
            trend = trend_data['trend']
            
            # Generate simulated price data
            days = 30
            dates = pd.date_range(end=pd.Timestamp.now(), periods=days)
            
            # Create price trend based on current trend
            if trend == 'bullish':
                # Upward trend with some noise
                change_factor = np.linspace(0.9, 1.0, days) + np.random.normal(0, 0.01, days)
            elif trend == 'bearish':
                # Downward trend with some noise
                change_factor = np.linspace(1.1, 1.0, days) + np.random.normal(0, 0.01, days)
            else:
                # Sideways trend with some noise
                change_factor = np.ones(days) + np.random.normal(0, 0.01, days)
            
            # Calculate prices
            prices = current_price / np.cumprod(change_factor)
            
            # Create DataFrame
            df = pd.DataFrame({
                'Date': dates,
                'Price': prices
            })
            
            # Create figure
            fig = px.line(df, x='Date', y='Price', title=f"{symbol} - Price Trend")
            
            # Add current price marker
            fig.add_trace(go.Scatter(
                x=[df['Date'].iloc[-1]],
                y=[current_price],
                mode='markers',
                marker=dict(size=10, color='red'),
                name='Current Price'
            ))
            
            # Update layout
            fig.update_layout(
                height=600,
                width=1000,
                template="plotly_white",
                xaxis_title="Date",
                yaxis_title="Price"
            )
            
            # Convert to base64 image
            img_bytes = io.BytesIO()
            fig.write_image(img_bytes, format='png')
            img_bytes.seek(0)
            img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Error generating trend chart: {e}")
            return ""
    
    @staticmethod
    def generate_option_chain_summary(analysis: Dict) -> str:
        """
        Generate option chain summary visualization.
        
        Args:
            analysis: Dictionary with option chain analysis
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Extract data
            symbol = analysis['symbol']
            current_price = analysis['current_price']
            pcr = analysis['pcr']
            max_pain = analysis['max_pain']
            support_levels = analysis['support_levels']
            resistance_levels = analysis['resistance_levels']
            
            # Create figure with subplots
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Key Levels", "Put-Call Ratio"),
                row_heights=[0.7, 0.3]
            )
            
            # Add price levels
            price_range = max(abs(current_price - min(support_levels)), 
                             abs(current_price - max(resistance_levels))) * 1.2
            
            price_min = current_price - price_range
            price_max = current_price + price_range
            
            # Add current price line
            fig.add_shape(
                type="line",
                x0=0, x1=1,
                y0=current_price, y1=current_price,
                line=dict(color="black", width=2, dash="solid"),
                row=1, col=1
            )
            
            # Add max pain line
            fig.add_shape(
                type="line",
                x0=0, x1=1,
                y0=max_pain, y1=max_pain,
                line=dict(color="purple", width=2, dash="dash"),
                row=1, col=1
            )
            
            # Add support levels
            for level in support_levels:
                fig.add_shape(
                    type="line",
                    x0=0, x1=1,
                    y0=level, y1=level,
                    line=dict(color="green", width=1.5, dash="dot"),
                    row=1, col=1
                )
            
            # Add resistance levels
            for level in resistance_levels:
                fig.add_shape(
                    type="line",
                    x0=0, x1=1,
                    y0=level, y1=level,
                    line=dict(color="red", width=1.5, dash="dot"),
                    row=1, col=1
                )
            
            # Add annotations
            fig.add_annotation(
                x=0.5, y=current_price,
                text=f"Current: {current_price}",
                showarrow=True,
                arrowhead=1,
                row=1, col=1
            )
            
            fig.add_annotation(
                x=0.5, y=max_pain,
                text=f"Max Pain: {max_pain}",
                showarrow=True,
                arrowhead=1,
                row=1, col=1
            )
            
            # Add PCR bar
            fig.add_trace(
                go.Bar(
                    x=['PCR'],
                    y=[pcr],
                    marker_color='blue' if pcr > 1 else 'orange',
                    text=[f"{pcr:.2f}"],
                    textposition='auto'
                ),
                row=2, col=1
            )
            
            # Add PCR reference line at 1.0
            fig.add_shape(
                type="line",
                x0=-0.5, x1=0.5,
                y0=1, y1=1,
                line=dict(color="black", width=1, dash="dot"),
                row=2, col=1
            )
            
            # Update layout
            fig.update_layout(
                title=f"{symbol} - Option Chain Summary",
                height=800,
                width=1000,
                showlegend=False,
                template="plotly_white"
            )
            
            # Update y-axis range for price levels
            fig.update_yaxes(range=[price_min, price_max], row=1, col=1)
            
            # Update y-axis range for PCR
            fig.update_yaxes(range=[0, max(2, pcr * 1.2)], row=2, col=1)
            
            # Convert to base64 image
            img_bytes = io.BytesIO()
            fig.write_image(img_bytes, format='png')
            img_bytes.seek(0)
            img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Error generating option chain summary: {e}")
            return ""


class ReportFormatter:
    """Format reports and summaries for the bot."""
    
    @staticmethod
    def format_market_trend_report(trend_analysis: Dict) -> str:
        """
        Format market trend report.
        
        Args:
            trend_analysis: Dictionary with trend analysis
            
        Returns:
            Formatted report text
        """
        symbol = trend_analysis['symbol']
        current_price = trend_analysis['current_price']
        change_value = trend_analysis['change_value']
        change_percentage = trend_analysis['change_percentage']
        trend = trend_analysis['trend']
        trend_strength = trend_analysis.get('trend_strength', '')
        recommendation = trend_analysis.get('recommendation', '')
        
        # Format change with appropriate sign
        change_sign = '+' if change_value >= 0 else ''
        change_str = f"{change_sign}{change_value:.2f} ({change_sign}{change_percentage:.2f}%)"
        
        # Emoji based on trend
        if trend == 'bullish':
            trend_emoji = '📈'
        elif trend == 'bearish':
            trend_emoji = '📉'
        else:
            trend_emoji = '➡️'
        
        # Format report
        report = f"🔍 *{symbol} Market Trend Report* 🔍\n\n"
        report += f"*Current Price:* {current_price:.2f}\n"
        report += f"*Change:* {change_str}\n"
        report += f"*Trend:* {trend_emoji} {trend.capitalize()}"
        
        if trend_strength:
            report += f" ({trend_strength.capitalize()})"
        
        report += "\n\n"
        
        # Add technical indicators
        report += "*Technical Indicators:*\n"
        report += f"• RSI: {trend_analysis['rsi']:.2f}\n"
        report += f"• MACD: {trend_analysis['macd']:.2f}\n"
        
        # Add volume
        report += f"• Volume: {trend_analysis['volume']:,}\n\n"
        
        # Add recommendation
        if recommendation:
            report += f"*Recommendation:* {recommendation}\n\n"
        
        # Add timestamp
        report += f"_Updated: {trend_analysis['timestamp']}_"
        
        return report
    
    @staticmethod
    def format_option_chain_summary(analysis: Dict) -> str:
        """
        Format option chain summary.
        
        Args:
            analysis: Dictionary with option chain analysis
            
        Returns:
            Formatted summary text
        """
        symbol = analysis['symbol']
        current_price = analysis['current_price']
        pcr = analysis['pcr']
        max_pain = analysis['max_pain']
        sentiment = analysis['sentiment']
        max_pain_analysis = analysis['max_pain_analysis']
        
        # Format support and resistance levels
        support_str = ', '.join([f"{level:.2f}" for level in analysis['support_levels']])
        resistance_str = ', '.join([f"{level:.2f}" for level in analysis['resistance_levels']])
        
        # Emoji based on sentiment
        if 'Bullish' in sentiment:
            sentiment_emoji = '🐂'
        elif 'Bearish' in sentiment:
            sentiment_emoji = '🐻'
        else:
            sentiment_emoji = '⚖️'
        
        # Format summary
        summary = f"📊 *{symbol} Option Chain Summary* 📊\n\n"
        summary += f"*Current Price:* {current_price:.2f}\n"
        summary += f"*Put-Call Ratio:* {pcr:.2f}\n"
        summary += f"*Max Pain Point:* {max_pain:.2f}\n"
        summary += f"*Market Sentiment:* {sentiment_emoji} {sentiment}\n\n"
        
        summary += "*Key Levels:*\n"
        summary += f"• Support: {support_str}\n"
        summary += f"• Resistance: {resistance_str}\n\n"
        
        summary += f"*Analysis:* {max_pain_analysis}\n\n"
        
        # Add timestamp
        summary += f"_Updated: {analysis['timestamp']}_"
        
        return summary
    
    @staticmethod
    def format_trade_idea(trade_idea: Dict) -> str:
        """
        Format a trade idea.
        
        Args:
            trade_idea: Dictionary with trade idea
            
        Returns:
            Formatted trade idea text
        """
        symbol = trade_idea['symbol']
        option_type = trade_idea['option_type']
        strike = trade_idea['strike']
        entry = trade_idea['entry']
        target = trade_idea['target']
        stop_loss = trade_idea['stop_loss']
        
        # Optional fields
        delta = trade_idea.get('delta')
        oi_change = trade_idea.get('oi_change')
        rationale = trade_idea.get('rationale')
        confidence = trade_idea.get('confidence')
        risk_reward = trade_idea.get('risk_reward_ratio')
        ml_commentary = trade_idea.get('ml_commentary')
        
        # Determine trend direction
        trend = "Bullish" if option_type.upper() == "CE" else "Bearish"
        
        # Format trade idea
        idea = f"📍 *{symbol} {strike} {option_type} – {trend} Trend*\n\n"
        idea += f"🔹 *Entry:* {entry:.2f} | *Target:* {target:.2f} | *SL:* {stop_loss:.2f}\n"
        
        # Add optional metrics
        metrics = []
        if delta is not None:
            metrics.append(f"Delta: {delta:.2f}")
        
        if oi_change is not None:
            direction = "↑" if oi_change > 0 else "↓"
            metrics.append(f"OI Change: {direction}{abs(oi_change):.0f}%")
        
        if confidence is not None:
            metrics.append(f"Confidence: {confidence:.0%}")
        
        if risk_reward is not None:
            metrics.append(f"Risk-Reward: 1:{risk_reward:.1f}")
        
        if metrics:
            idea += "📈 " + " | ".join(metrics) + "\n\n"
        
        # Add rationale
        if rationale:
            idea += f"*Rationale:* {rationale}\n\n"
        
        # Add ML commentary
        if ml_commentary:
            idea += f"*ML Insight:* {ml_commentary}\n\n"
        
        return idea
    
    @staticmethod
    def format_daily_summary(symbol: str, trend_analysis: Dict, option_analysis: Dict, trade_ideas: List[Dict]) -> str:
        """
        Format daily market summary.
        
        Args:
            symbol: Stock/index symbol
            trend_analysis: Dictionary with trend analysis
            option_analysis: Dictionary with option chain analysis
            trade_ideas: List of trade ideas
            
        Returns:
            Formatted summary text
        """
        # Get current date
        current_date = datetime.now().strftime('%d %b %Y')
        
        # Format summary
        summary = f"📅 *{symbol} Daily Summary - {current_date}* 📅\n\n"
        
        # Market overview
        summary += "*Market Overview:*\n"
        summary += f"• Price: {trend_analysis['current_price']:.2f}\n"
        
        change_sign = '+' if trend_analysis['change_value'] >= 0 else ''
        change_str = f"{change_sign}{trend_analysis['change_value']:.2f} ({change_sign}{trend_analysis['change_percentage']:.2f}%)"
        summary += f"• Change: {change_str}\n"
        
        summary += f"• Trend: {trend_analysis['trend'].capitalize()}\n"
        summary += f"• PCR: {option_analysis['pcr']:.2f}\n"
        summary += f"• Sentiment: {option_analysis['sentiment']}\n\n"
        
        # Key levels
        summary += "*Key Price Levels:*\n"
        summary += f"• Max Pain: {option_analysis['max_pain']:.2f}\n"
        
        support_str = ', '.join([f"{level:.2f}" for level in option_analysis['support_levels'][:2]])
        resistance_str = ', '.join([f"{level:.2f}" for level in option_analysis['resistance_levels'][:2]])
        
        summary += f"• Support: {support_str}\n"
        summary += f"• Resistance: {resistance_str}\n\n"
        
        # Top trade idea
        if trade_ideas:
            top_idea = trade_ideas[0]
            trend = "Bullish" if top_idea['option_type'].upper() == "CE" else "Bearish"
            
            summary += "*Top Trade Idea:*\n"
            summary += f"• {top_idea['symbol']} {top_idea['strike']} {top_idea['option_type']} ({trend})\n"
            summary += f"• Entry: {top_idea['entry']:.2f} | Target: {top_idea['target']:.2f} | SL: {top_idea['stop_loss']:.2f}\n\n"
        
        # Market outlook
        if trend_analysis.get('recommendation'):
            summary += f"*Market Outlook:* {trend_analysis['recommendation']}\n\n"
        
        # Add timestamp
        summary += f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        return summary
