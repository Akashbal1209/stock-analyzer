import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# Import configuration
try:
    from config import (
        # Fundamental
        PE_UNDERVALUED, PE_FAIR_VALUE, PE_EXPENSIVE,
        PB_BELOW_BOOK, PB_REASONABLE, PB_PREMIUM,
        ROE_EXCELLENT, ROE_GOOD, ROE_AVERAGE,
        DE_LOW, DE_MODERATE, DE_HIGH,
        DIVIDEND_GOOD, DIVIDEND_MODERATE,
        MARGIN_HIGH, MARGIN_DECENT,
        GROWTH_HIGH, GROWTH_GOOD,
        # Fundamental Scores
        SCORE_PE_UNDERVALUED, SCORE_PE_FAIR, SCORE_PE_EXPENSIVE, SCORE_PE_OVERVALUED,
        SCORE_PB_BELOW_BOOK, SCORE_PB_REASONABLE, SCORE_PB_PREMIUM, SCORE_PB_EXPENSIVE,
        SCORE_ROE_EXCELLENT, SCORE_ROE_GOOD, SCORE_ROE_LOW,
        SCORE_DE_LOW, SCORE_DE_MODERATE, SCORE_DE_HIGH, SCORE_DE_VERY_HIGH,
        SCORE_DIVIDEND_GOOD, SCORE_DIVIDEND_MODERATE,
        SCORE_MARGIN_HIGH, SCORE_MARGIN_DECENT, SCORE_MARGIN_LOSS,
        SCORE_GROWTH_HIGH, SCORE_GROWTH_GOOD, SCORE_GROWTH_DECLINING,
        # Technical
        RSI_OVERSOLD, RSI_APPROACHING_OVERSOLD, RSI_NEUTRAL_HIGH, RSI_APPROACHING_OVERBOUGHT, RSI_OVERBOUGHT,
        STOCH_OVERSOLD, STOCH_OVERBOUGHT, ADX_TRENDING, BB_OVERSOLD, BB_OVERBOUGHT,
        VOLUME_HIGH, VOLUME_LOW,
        # Technical Scores
        SCORE_RSI_OVERSOLD, SCORE_RSI_APPROACHING_OVERSOLD, SCORE_RSI_APPROACHING_OVERBOUGHT, SCORE_RSI_OVERBOUGHT,
        SCORE_MACD_BULLISH, SCORE_MACD_BEARISH,
        SCORE_MA_BULLISH, SCORE_MA_BEARISH,
        SCORE_BB_OVERSOLD, SCORE_BB_OVERBOUGHT,
        SCORE_STOCH_OVERSOLD, SCORE_STOCH_OVERBOUGHT,
        SCORE_ADX_UPTREND, SCORE_ADX_DOWNTREND,
        # Historical
        POSITION_NEAR_LOW, POSITION_LOWER_HALF, POSITION_UPPER_HALF, POSITION_NEAR_HIGH,
        RETURN_STRONG, RETURN_GOOD, VOLATILITY_LOW, VOLATILITY_MODERATE,
        SUPPORT_VERY_CLOSE, SUPPORT_NEAR,
        # Historical Scores
        SCORE_POSITION_NEAR_LOW, SCORE_POSITION_LOWER_HALF, SCORE_POSITION_NEAR_HIGH, SCORE_POSITION_AT_HIGH,
        SCORE_TREND_BULLISH, SCORE_TREND_BEARISH,
        SCORE_RETURN_STRONG, SCORE_RETURN_GOOD, SCORE_RETURN_NEGATIVE,
        SCORE_VOLATILITY_LOW, SCORE_VOLATILITY_HIGH,
        SCORE_SUPPORT_VERY_CLOSE, SCORE_SUPPORT_NEAR,
        # Analyzer settings
        ANALYZER_WEIGHTS, BUY_SIGNAL_THRESHOLD, STRONG_BUY_THRESHOLD,
        SELL_SIGNAL_THRESHOLD, STRONG_SELL_THRESHOLD,
        FUNDAMENTAL_WEIGHT, HISTORICAL_WEIGHT, TECHNICAL_WEIGHT,
        # Trading Plan
        BEST_ENTRY_TOLERANCE, GOOD_ENTRY_TOLERANCE, AGGRESSIVE_ENTRY_TOLERANCE,
        TARGET_1_ATR_MULTIPLIER, TARGET_2_ATR_MULTIPLIER, STOP_LOSS_ATR_MULTIPLIER, SUPPORT_STOP_MARGIN
    )
    CONFIG_LOADED = True
except ImportError:
    CONFIG_LOADED = False
    # Fallback defaults
    PE_UNDERVALUED, PE_FAIR_VALUE, PE_EXPENSIVE = 15, 25, 40
    PB_BELOW_BOOK, PB_REASONABLE, PB_PREMIUM = 1, 3, 5
    ROE_EXCELLENT, ROE_GOOD, ROE_AVERAGE = 20, 15, 10
    DE_LOW, DE_MODERATE, DE_HIGH = 50, 100, 150
    DIVIDEND_GOOD, DIVIDEND_MODERATE = 3, 1
    MARGIN_HIGH, MARGIN_DECENT = 20, 10
    GROWTH_HIGH, GROWTH_GOOD = 20, 10
    SCORE_PE_UNDERVALUED, SCORE_PE_FAIR, SCORE_PE_EXPENSIVE, SCORE_PE_OVERVALUED = 10, 5, -5, -10
    SCORE_PB_BELOW_BOOK, SCORE_PB_REASONABLE, SCORE_PB_PREMIUM, SCORE_PB_EXPENSIVE = 10, 5, -5, -10
    SCORE_ROE_EXCELLENT, SCORE_ROE_GOOD, SCORE_ROE_LOW = 10, 5, -5
    SCORE_DE_LOW, SCORE_DE_MODERATE, SCORE_DE_HIGH, SCORE_DE_VERY_HIGH = 10, 5, -5, -10
    SCORE_DIVIDEND_GOOD, SCORE_DIVIDEND_MODERATE = 5, 2
    SCORE_MARGIN_HIGH, SCORE_MARGIN_DECENT, SCORE_MARGIN_LOSS = 5, 2, -10
    SCORE_GROWTH_HIGH, SCORE_GROWTH_GOOD, SCORE_GROWTH_DECLINING = 5, 2, -5
    RSI_OVERSOLD, RSI_APPROACHING_OVERSOLD, RSI_NEUTRAL_HIGH = 30, 45, 55
    RSI_APPROACHING_OVERBOUGHT, RSI_OVERBOUGHT = 70, 70
    STOCH_OVERSOLD, STOCH_OVERBOUGHT = 20, 80
    ADX_TRENDING = 25
    BB_OVERSOLD, BB_OVERBOUGHT = 0.2, 0.8
    VOLUME_HIGH, VOLUME_LOW = 1.5, 0.5
    SCORE_RSI_OVERSOLD, SCORE_RSI_APPROACHING_OVERSOLD = 15, 5
    SCORE_RSI_APPROACHING_OVERBOUGHT, SCORE_RSI_OVERBOUGHT = -5, -15
    SCORE_MACD_BULLISH, SCORE_MACD_BEARISH = 10, -10
    SCORE_MA_BULLISH, SCORE_MA_BEARISH = 10, -10
    SCORE_BB_OVERSOLD, SCORE_BB_OVERBOUGHT = 10, -10
    SCORE_STOCH_OVERSOLD, SCORE_STOCH_OVERBOUGHT = 10, -10
    SCORE_ADX_UPTREND, SCORE_ADX_DOWNTREND = 5, -5
    POSITION_NEAR_LOW, POSITION_LOWER_HALF, POSITION_UPPER_HALF, POSITION_NEAR_HIGH = 30, 50, 70, 90
    RETURN_STRONG, RETURN_GOOD = 30, 10
    VOLATILITY_LOW, VOLATILITY_MODERATE = 20, 35
    SUPPORT_VERY_CLOSE, SUPPORT_NEAR = 3, 7
    SCORE_POSITION_NEAR_LOW, SCORE_POSITION_LOWER_HALF = 15, 10
    SCORE_POSITION_NEAR_HIGH, SCORE_POSITION_AT_HIGH = -5, -10
    SCORE_TREND_BULLISH, SCORE_TREND_BEARISH = 10, -10
    SCORE_RETURN_STRONG, SCORE_RETURN_GOOD, SCORE_RETURN_NEGATIVE = 5, 2, -5
    SCORE_VOLATILITY_LOW, SCORE_VOLATILITY_HIGH = 5, -5
    SCORE_SUPPORT_VERY_CLOSE, SCORE_SUPPORT_NEAR = 10, 5
    ANALYZER_WEIGHTS = {'rsi': 0.12, 'macd': 0.12, 'ma_trend': 0.12, 'bollinger': 0.10,
                        'stochastic': 0.10, 'volume': 0.10, 'momentum': 0.10,
                        'atr_position': 0.08, 'adx': 0.08, 'historical': 0.08}
    BUY_SIGNAL_THRESHOLD, STRONG_BUY_THRESHOLD = 65, 75
    SELL_SIGNAL_THRESHOLD, STRONG_SELL_THRESHOLD = 35, 25
    FUNDAMENTAL_WEIGHT, HISTORICAL_WEIGHT, TECHNICAL_WEIGHT = 0.30, 0.25, 0.45
    BEST_ENTRY_TOLERANCE, GOOD_ENTRY_TOLERANCE, AGGRESSIVE_ENTRY_TOLERANCE = 0.01, 0.02, 0.01
    TARGET_1_ATR_MULTIPLIER, TARGET_2_ATR_MULTIPLIER = 2.0, 3.5
    STOP_LOSS_ATR_MULTIPLIER, SUPPORT_STOP_MARGIN = 1.5, 0.03


class ComprehensiveAnalyzer:
    """Complete Stock Analysis Engine - All thresholds from config.py"""

    def __init__(self):
        self.weights = ANALYZER_WEIGHTS.copy()

    # ==================== FUNDAMENTAL ANALYSIS ====================
    
    def get_fundamental_data(self, symbol):
        """Fetch fundamental data from Yahoo Finance"""
        try:
            for suffix in ['.NS', '.BO']:
                ticker = yf.Ticker(f"{symbol}{suffix}")
                info = ticker.info
                
                if info and ('regularMarketPrice' in info or 'currentPrice' in info):
                    return {
                        'company_name': info.get('longName', info.get('shortName', symbol)),
                        'sector': info.get('sector', 'N/A'),
                        'industry': info.get('industry', 'N/A'),
                        'market_cap': info.get('marketCap', 0),
                        'market_cap_formatted': self._format_market_cap(info.get('marketCap', 0)),
                        'pe_ratio': info.get('trailingPE', info.get('forwardPE', None)),
                        'pb_ratio': info.get('priceToBook', None),
                        'ps_ratio': info.get('priceToSalesTrailing12Months', None),
                        'peg_ratio': info.get('pegRatio', None),
                        'eps': info.get('trailingEps', None),
                        'book_value': info.get('bookValue', None),
                        'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                        'dividend_rate': info.get('dividendRate', 0),
                        'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else None,
                        'roa': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else None,
                        'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else None,
                        'operating_margin': info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else None,
                        'debt_to_equity': info.get('debtToEquity', None),
                        'current_ratio': info.get('currentRatio', None),
                        'quick_ratio': info.get('quickRatio', None),
                        'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else None,
                        'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else None,
                        'current_price': info.get('regularMarketPrice', info.get('currentPrice', None)),
                        'previous_close': info.get('previousClose', None),
                        'day_high': info.get('dayHigh', None),
                        'day_low': info.get('dayLow', None),
                        'fifty_two_week_high': info.get('fiftyTwoWeekHigh', None),
                        'fifty_two_week_low': info.get('fiftyTwoWeekLow', None),
                        'fifty_day_avg': info.get('fiftyDayAverage', None),
                        'two_hundred_day_avg': info.get('twoHundredDayAverage', None),
                        'avg_volume': info.get('averageVolume', None),
                        'avg_volume_10d': info.get('averageVolume10days', None),
                    }
            return None
        except Exception as e:
            print(f"   ⚠️ Could not fetch fundamentals: {str(e)[:50]}")
            return None

    def _format_market_cap(self, market_cap):
        """Format market cap in Cr"""
        if not market_cap:
            return 'N/A'
        cr = market_cap / 10000000
        if cr >= 100000:
            return f"₹{cr/100000:.2f} Lakh Cr"
        elif cr >= 1000:
            return f"₹{cr/1000:.2f}K Cr"
        else:
            return f"₹{cr:.0f} Cr"

    def calculate_fundamental_score(self, fundamentals):
        """Calculate fundamental score (0-100) using config thresholds"""
        if not fundamentals:
            return None, []
        
        score = 50
        factors = []
        
        # PE Ratio
        pe = fundamentals.get('pe_ratio')
        if pe:
            if pe < PE_UNDERVALUED:
                score += SCORE_PE_UNDERVALUED
                factors.append(('PE Ratio', pe, 'Undervalued', '✅'))
            elif pe < PE_FAIR_VALUE:
                score += SCORE_PE_FAIR
                factors.append(('PE Ratio', pe, 'Fair value', '✅'))
            elif pe < PE_EXPENSIVE:
                score += SCORE_PE_EXPENSIVE
                factors.append(('PE Ratio', pe, 'Slightly expensive', '⚠️'))
            else:
                score += SCORE_PE_OVERVALUED
                factors.append(('PE Ratio', pe, 'Overvalued', '❌'))
        
        # PB Ratio
        pb = fundamentals.get('pb_ratio')
        if pb:
            if pb < PB_BELOW_BOOK:
                score += SCORE_PB_BELOW_BOOK
                factors.append(('PB Ratio', pb, 'Below book value', '✅'))
            elif pb < PB_REASONABLE:
                score += SCORE_PB_REASONABLE
                factors.append(('PB Ratio', pb, 'Reasonable', '✅'))
            elif pb < PB_PREMIUM:
                score += SCORE_PB_PREMIUM
                factors.append(('PB Ratio', pb, 'Premium valuation', '⚠️'))
            else:
                score += SCORE_PB_EXPENSIVE
                factors.append(('PB Ratio', pb, 'Very expensive', '❌'))
        
        # ROE
        roe = fundamentals.get('roe')
        if roe:
            if roe > ROE_EXCELLENT:
                score += SCORE_ROE_EXCELLENT
                factors.append(('ROE', f"{roe:.1f}%", 'Excellent', '✅'))
            elif roe > ROE_GOOD:
                score += SCORE_ROE_GOOD
                factors.append(('ROE', f"{roe:.1f}%", 'Good', '✅'))
            elif roe > ROE_AVERAGE:
                factors.append(('ROE', f"{roe:.1f}%", 'Average', '⚠️'))
            else:
                score += SCORE_ROE_LOW
                factors.append(('ROE', f"{roe:.1f}%", 'Low', '❌'))
        
        # Debt to Equity
        de = fundamentals.get('debt_to_equity')
        if de is not None:
            if de < DE_LOW:
                score += SCORE_DE_LOW
                factors.append(('Debt/Equity', f"{de:.1f}%", 'Low debt', '✅'))
            elif de < DE_MODERATE:
                score += SCORE_DE_MODERATE
                factors.append(('Debt/Equity', f"{de:.1f}%", 'Moderate', '✅'))
            elif de < DE_HIGH:
                score += SCORE_DE_HIGH
                factors.append(('Debt/Equity', f"{de:.1f}%", 'High debt', '⚠️'))
            else:
                score += SCORE_DE_VERY_HIGH
                factors.append(('Debt/Equity', f"{de:.1f}%", 'Very high', '❌'))
        
        # Dividend Yield
        div = fundamentals.get('dividend_yield', 0)
        if div > DIVIDEND_GOOD:
            score += SCORE_DIVIDEND_GOOD
            factors.append(('Dividend', f"{div:.1f}%", 'Good', '✅'))
        elif div > DIVIDEND_MODERATE:
            score += SCORE_DIVIDEND_MODERATE
            factors.append(('Dividend', f"{div:.1f}%", 'Moderate', '✅'))
        
        # Profit Margin
        margin = fundamentals.get('profit_margin')
        if margin:
            if margin > MARGIN_HIGH:
                score += SCORE_MARGIN_HIGH
                factors.append(('Margin', f"{margin:.1f}%", 'High', '✅'))
            elif margin > MARGIN_DECENT:
                score += SCORE_MARGIN_DECENT
                factors.append(('Margin', f"{margin:.1f}%", 'Decent', '✅'))
            elif margin > 0:
                factors.append(('Margin', f"{margin:.1f}%", 'Low', '⚠️'))
            else:
                score += SCORE_MARGIN_LOSS
                factors.append(('Margin', f"{margin:.1f}%", 'Loss', '❌'))
        
        # Revenue Growth
        rev_growth = fundamentals.get('revenue_growth')
        if rev_growth:
            if rev_growth > GROWTH_HIGH:
                score += SCORE_GROWTH_HIGH
                factors.append(('Growth', f"{rev_growth:.1f}%", 'High', '✅'))
            elif rev_growth > GROWTH_GOOD:
                score += SCORE_GROWTH_GOOD
                factors.append(('Growth', f"{rev_growth:.1f}%", 'Good', '✅'))
            elif rev_growth > 0:
                factors.append(('Growth', f"{rev_growth:.1f}%", 'Slow', '⚠️'))
            else:
                score += SCORE_GROWTH_DECLINING
                factors.append(('Growth', f"{rev_growth:.1f}%", 'Declining', '❌'))
        
        return max(0, min(100, score)), factors

    # ==================== HISTORICAL ANALYSIS ====================
    
    def calculate_historical_levels(self, df):
        """Calculate support, resistance, and historical levels"""
        if df is None or len(df) < 50:
            return None
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        current_price = close.iloc[-1]
        
        week_52_high = high.max()
        week_52_low = low.min()
        
        # Swing highs/lows
        swing_highs, swing_lows = [], []
        window = 10
        for i in range(window, len(df) - window):
            if high.iloc[i] == high.iloc[i-window:i+window+1].max():
                swing_highs.append(high.iloc[i])
            if low.iloc[i] == low.iloc[i-window:i+window+1].min():
                swing_lows.append(low.iloc[i])
        
        supports = sorted([s for s in swing_lows if s < current_price], reverse=True)
        resistances = sorted([r for r in swing_highs if r > current_price])
        
        supports = self._cluster_levels(supports, current_price * 0.02)
        resistances = self._cluster_levels(resistances, current_price * 0.02)
        
        sma_20 = close.rolling(20).mean().iloc[-1]
        sma_50 = close.rolling(50).mean().iloc[-1]
        sma_200 = close.rolling(200).mean().iloc[-1] if len(df) >= 200 else None
        
        price_position = (current_price - week_52_low) / (week_52_high - week_52_low) * 100
        
        returns_1m = ((current_price / close.iloc[-22]) - 1) * 100 if len(df) >= 22 else None
        returns_3m = ((current_price / close.iloc[-66]) - 1) * 100 if len(df) >= 66 else None
        returns_6m = ((current_price / close.iloc[-132]) - 1) * 100 if len(df) >= 132 else None
        returns_1y = ((current_price / close.iloc[0]) - 1) * 100
        
        volatility = close.pct_change().dropna().std() * np.sqrt(252) * 100
        
        # Trend detection
        if sma_200:
            if current_price > sma_200 and sma_50 > sma_200:
                trend = 'BULLISH'
            elif current_price < sma_200 and sma_50 < sma_200:
                trend = 'BEARISH'
            else:
                trend = 'SIDEWAYS'
        else:
            trend = 'BULLISH' if current_price > sma_50 else 'BEARISH' if current_price < sma_50 else 'SIDEWAYS'
        
        return {
            'current_price': round(current_price, 2),
            'week_52_high': round(week_52_high, 2),
            'week_52_low': round(week_52_low, 2),
            'pct_from_52w_high': round((current_price - week_52_high) / week_52_high * 100, 1),
            'pct_from_52w_low': round((current_price - week_52_low) / week_52_low * 100, 1),
            'price_position': round(price_position, 1),
            'supports': [round(s, 2) for s in supports[:3]],
            'resistances': [round(r, 2) for r in resistances[:3]],
            'sma_20': round(sma_20, 2) if not pd.isna(sma_20) else None,
            'sma_50': round(sma_50, 2) if not pd.isna(sma_50) else None,
            'sma_200': round(sma_200, 2) if sma_200 and not pd.isna(sma_200) else None,
            'returns_1m': round(returns_1m, 1) if returns_1m else None,
            'returns_3m': round(returns_3m, 1) if returns_3m else None,
            'returns_6m': round(returns_6m, 1) if returns_6m else None,
            'returns_1y': round(returns_1y, 1),
            'volatility': round(volatility, 1),
            'trend': trend
        }

    def _cluster_levels(self, levels, threshold):
        """Cluster nearby price levels"""
        if not levels:
            return []
        clustered = []
        current_cluster = [levels[0]]
        for level in levels[1:]:
            if abs(level - current_cluster[0]) <= threshold:
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        clustered.append(np.mean(current_cluster))
        return clustered

    def calculate_historical_score(self, historical):
        """Calculate historical score using config thresholds"""
        if not historical:
            return None, []
        
        score = 50
        factors = []
        
        # 52-week position
        pos = historical['price_position']
        if pos < POSITION_NEAR_LOW:
            score += SCORE_POSITION_NEAR_LOW
            factors.append(('52W Position', f"{pos:.0f}%", 'Near low', '✅'))
        elif pos < POSITION_LOWER_HALF:
            score += SCORE_POSITION_LOWER_HALF
            factors.append(('52W Position', f"{pos:.0f}%", 'Lower half', '✅'))
        elif pos < POSITION_UPPER_HALF:
            factors.append(('52W Position', f"{pos:.0f}%", 'Middle', '⚠️'))
        elif pos < POSITION_NEAR_HIGH:
            score += SCORE_POSITION_NEAR_HIGH
            factors.append(('52W Position', f"{pos:.0f}%", 'Near high', '⚠️'))
        else:
            score += SCORE_POSITION_AT_HIGH
            factors.append(('52W Position', f"{pos:.0f}%", 'At high', '❌'))
        
        # Trend
        trend = historical['trend']
        if trend == 'BULLISH':
            score += SCORE_TREND_BULLISH
            factors.append(('Trend', trend, 'Uptrend', '✅'))
        elif trend == 'BEARISH':
            score += SCORE_TREND_BEARISH
            factors.append(('Trend', trend, 'Downtrend', '❌'))
        else:
            factors.append(('Trend', trend, 'Sideways', '⚠️'))
        
        # 1Y Return
        ret_1y = historical.get('returns_1y', 0)
        if ret_1y > RETURN_STRONG:
            score += SCORE_RETURN_STRONG
            factors.append(('1Y Return', f"{ret_1y:+.1f}%", 'Strong', '✅'))
        elif ret_1y > RETURN_GOOD:
            score += SCORE_RETURN_GOOD
            factors.append(('1Y Return', f"{ret_1y:+.1f}%", 'Good', '✅'))
        elif ret_1y > 0:
            factors.append(('1Y Return', f"{ret_1y:+.1f}%", 'Positive', '⚠️'))
        else:
            score += SCORE_RETURN_NEGATIVE
            factors.append(('1Y Return', f"{ret_1y:+.1f}%", 'Negative', '❌'))
        
        # Volatility
        vol = historical.get('volatility', 30)
        if vol < VOLATILITY_LOW:
            score += SCORE_VOLATILITY_LOW
            factors.append(('Volatility', f"{vol:.0f}%", 'Low', '✅'))
        elif vol < VOLATILITY_MODERATE:
            factors.append(('Volatility', f"{vol:.0f}%", 'Moderate', '⚠️'))
        else:
            score += SCORE_VOLATILITY_HIGH
            factors.append(('Volatility', f"{vol:.0f}%", 'High', '❌'))
        
        # Support proximity
        price = historical['current_price']
        supports = historical['supports']
        if supports:
            nearest = supports[0]
            dist = (price - nearest) / price * 100
            if dist < SUPPORT_VERY_CLOSE:
                score += SCORE_SUPPORT_VERY_CLOSE
                factors.append(('Support', f"₹{nearest}", f'{dist:.1f}% away', '✅'))
            elif dist < SUPPORT_NEAR:
                score += SCORE_SUPPORT_NEAR
                factors.append(('Support', f"₹{nearest}", f'{dist:.1f}% away', '✅'))
        
        return max(0, min(100, score)), factors

    # ==================== TECHNICAL ANALYSIS ====================
    
    def calculate_technical_indicators(self, df):
        """Calculate all technical indicators"""
        if df is None or len(df) < 50:
            return None
        
        close, high, low, volume = df['Close'], df['High'], df['Low'], df['Volume']
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9).mean()
        macd_hist = macd_line - signal_line
        
        # MAs
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        sma_200 = close.rolling(200).mean() if len(df) >= 200 else pd.Series([np.nan] * len(df))
        
        # Bollinger
        bb_middle = sma_20
        bb_std = close.rolling(20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        # Stochastic
        lowest_low = low.rolling(14).min()
        highest_high = high.rolling(14).max()
        stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
        stoch_d = stoch_k.rolling(3).mean()
        
        # ATR
        tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        
        # ADX
        plus_dm = high.diff().where((high.diff() > -low.diff()) & (high.diff() > 0), 0)
        minus_dm = (-low.diff()).where((-low.diff() > high.diff()) & (-low.diff() > 0), 0)
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr.replace(0, np.nan))
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr.replace(0, np.nan))
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(14).mean()
        
        # Volume
        vol_ratio = volume / volume.rolling(20).mean()
        
        idx = -1
        return {
            'rsi': round(rsi.iloc[idx], 2) if not pd.isna(rsi.iloc[idx]) else None,
            'macd_line': round(macd_line.iloc[idx], 4) if not pd.isna(macd_line.iloc[idx]) else None,
            'macd_signal': round(signal_line.iloc[idx], 4) if not pd.isna(signal_line.iloc[idx]) else None,
            'macd_hist': round(macd_hist.iloc[idx], 4) if not pd.isna(macd_hist.iloc[idx]) else None,
            'sma_20': round(sma_20.iloc[idx], 2) if not pd.isna(sma_20.iloc[idx]) else None,
            'sma_50': round(sma_50.iloc[idx], 2) if not pd.isna(sma_50.iloc[idx]) else None,
            'sma_200': round(sma_200.iloc[idx], 2) if not pd.isna(sma_200.iloc[idx]) else None,
            'bb_upper': round(bb_upper.iloc[idx], 2) if not pd.isna(bb_upper.iloc[idx]) else None,
            'bb_middle': round(bb_middle.iloc[idx], 2) if not pd.isna(bb_middle.iloc[idx]) else None,
            'bb_lower': round(bb_lower.iloc[idx], 2) if not pd.isna(bb_lower.iloc[idx]) else None,
            'stoch_k': round(stoch_k.iloc[idx], 2) if not pd.isna(stoch_k.iloc[idx]) else None,
            'stoch_d': round(stoch_d.iloc[idx], 2) if not pd.isna(stoch_d.iloc[idx]) else None,
            'atr': round(atr.iloc[idx], 2) if not pd.isna(atr.iloc[idx]) else None,
            'adx': round(adx.iloc[idx], 2) if not pd.isna(adx.iloc[idx]) else None,
            'plus_di': round(plus_di.iloc[idx], 2) if not pd.isna(plus_di.iloc[idx]) else None,
            'minus_di': round(minus_di.iloc[idx], 2) if not pd.isna(minus_di.iloc[idx]) else None,
            'volume_ratio': round(vol_ratio.iloc[idx], 2) if not pd.isna(vol_ratio.iloc[idx]) else None,
            'current_price': round(close.iloc[idx], 2),
        }

    def calculate_technical_score(self, tech):
        """Calculate technical score using config thresholds"""
        if not tech:
            return None, []
        
        score = 50
        factors = []
        price = tech['current_price']
        
        # RSI
        rsi = tech.get('rsi')
        if rsi:
            if rsi < RSI_OVERSOLD:
                score += SCORE_RSI_OVERSOLD
                factors.append(('RSI', rsi, 'Oversold', '✅'))
            elif rsi < RSI_APPROACHING_OVERSOLD:
                score += SCORE_RSI_APPROACHING_OVERSOLD
                factors.append(('RSI', rsi, 'Approaching oversold', '✅'))
            elif rsi < RSI_NEUTRAL_HIGH:
                factors.append(('RSI', rsi, 'Neutral', '⚠️'))
            elif rsi < RSI_OVERBOUGHT:
                score += SCORE_RSI_APPROACHING_OVERBOUGHT
                factors.append(('RSI', rsi, 'Approaching overbought', '⚠️'))
            else:
                score += SCORE_RSI_OVERBOUGHT
                factors.append(('RSI', rsi, 'Overbought', '❌'))
        
        # MACD
        macd_hist = tech.get('macd_hist')
        macd_line = tech.get('macd_line')
        macd_signal = tech.get('macd_signal')
        if macd_hist is not None and macd_line is not None:
            if macd_line > macd_signal and macd_hist > 0:
                score += SCORE_MACD_BULLISH
                factors.append(('MACD', 'Bullish', 'Above signal', '✅'))
            elif macd_line < macd_signal and macd_hist < 0:
                score += SCORE_MACD_BEARISH
                factors.append(('MACD', 'Bearish', 'Below signal', '❌'))
            else:
                factors.append(('MACD', 'Neutral', 'Consolidating', '⚠️'))
        
        # Moving Averages
        sma_20, sma_50, sma_200 = tech.get('sma_20'), tech.get('sma_50'), tech.get('sma_200')
        ma_bullish = sum([1 for ma in [sma_20, sma_50, sma_200] if ma and price > ma])
        ma_bearish = sum([1 for ma in [sma_20, sma_50, sma_200] if ma and price < ma])
        if ma_bullish >= 2:
            score += SCORE_MA_BULLISH
            factors.append(('MAs', f'{ma_bullish}/3 bullish', 'Above MAs', '✅'))
        elif ma_bearish >= 2:
            score += SCORE_MA_BEARISH
            factors.append(('MAs', f'{ma_bearish}/3 bearish', 'Below MAs', '❌'))
        
        # Bollinger
        bb_upper, bb_lower = tech.get('bb_upper'), tech.get('bb_lower')
        if bb_upper and bb_lower:
            bb_pos = (price - bb_lower) / (bb_upper - bb_lower)
            if bb_pos < BB_OVERSOLD:
                score += SCORE_BB_OVERSOLD
                factors.append(('BB', f'{bb_pos:.0%}', 'Oversold', '✅'))
            elif bb_pos > BB_OVERBOUGHT:
                score += SCORE_BB_OVERBOUGHT
                factors.append(('BB', f'{bb_pos:.0%}', 'Overbought', '❌'))
        
        # Stochastic
        stoch_k = tech.get('stoch_k')
        if stoch_k:
            if stoch_k < STOCH_OVERSOLD:
                score += SCORE_STOCH_OVERSOLD
                factors.append(('Stoch', stoch_k, 'Oversold', '✅'))
            elif stoch_k > STOCH_OVERBOUGHT:
                score += SCORE_STOCH_OVERBOUGHT
                factors.append(('Stoch', stoch_k, 'Overbought', '❌'))
        
        # ADX
        adx, plus_di, minus_di = tech.get('adx'), tech.get('plus_di'), tech.get('minus_di')
        if adx and plus_di and minus_di:
            if adx > ADX_TRENDING:
                if plus_di > minus_di:
                    score += SCORE_ADX_UPTREND
                    factors.append(('ADX', adx, 'Strong uptrend', '✅'))
                else:
                    score += SCORE_ADX_DOWNTREND
                    factors.append(('ADX', adx, 'Strong downtrend', '❌'))
        
        # Volume
        vol_ratio = tech.get('volume_ratio')
        if vol_ratio:
            if vol_ratio > VOLUME_HIGH:
                factors.append(('Volume', f'{vol_ratio:.1f}x', 'High', '✅'))
            elif vol_ratio < VOLUME_LOW:
                factors.append(('Volume', f'{vol_ratio:.1f}x', 'Low', '⚠️'))
        
        return max(0, min(100, score)), factors

    # ==================== TRADING PLAN ====================
    
    def generate_trading_plan(self, tech, historical, fundamentals):
        """Generate buy/sell zones using config"""
        if not tech or not historical:
            return None
        
        price = tech['current_price']
        atr = tech.get('atr', price * 0.02)
        supports = historical.get('supports', [])
        resistances = historical.get('resistances', [])
        bb_lower = tech.get('bb_lower')
        bb_upper = tech.get('bb_upper')
        sma_20 = tech.get('sma_20')
        rsi = tech.get('rsi', 50)
        
        # Buy zones
        buy_zones = []
        if supports:
            buy_zones.append({
                'zone': 'Best Entry',
                'price_low': round(supports[0] * (1 - BEST_ENTRY_TOLERANCE), 2),
                'price_high': round(supports[0] * (1 + BEST_ENTRY_TOLERANCE), 2),
                'reason': 'Strong support'
            })
        if bb_lower and bb_lower < price:
            buy_zones.append({
                'zone': 'Good Entry',
                'price_low': round(bb_lower * (1 - GOOD_ENTRY_TOLERANCE/2), 2),
                'price_high': round(bb_lower * (1 + GOOD_ENTRY_TOLERANCE), 2),
                'reason': 'Lower Bollinger'
            })
        buy_zones.append({
            'zone': 'Aggressive',
            'price_low': round(price * (1 - AGGRESSIVE_ENTRY_TOLERANCE), 2),
            'price_high': round(price * (1 + AGGRESSIVE_ENTRY_TOLERANCE), 2),
            'reason': 'Current price'
        })
        
        # Buy triggers
        buy_triggers = [f"RSI below 40 (Now: {rsi:.0f})"]
        if bb_lower:
            buy_triggers.append(f"Price at ₹{bb_lower:.0f}")
        if supports:
            buy_triggers.append(f"Price at ₹{supports[0]:.0f}")
        
        # Targets & Stop Loss
        buy_target_1 = round(price + (atr * TARGET_1_ATR_MULTIPLIER), 2)
        buy_target_2 = round(price + (atr * TARGET_2_ATR_MULTIPLIER), 2)
        if resistances:
            buy_target_1 = min(buy_target_1, resistances[0])
            if len(resistances) > 1:
                buy_target_2 = min(buy_target_2, resistances[1])
        
        buy_stop_loss = round(price - (atr * STOP_LOSS_ATR_MULTIPLIER), 2)
        if supports:
            buy_stop_loss = min(buy_stop_loss, supports[0] * (1 - SUPPORT_STOP_MARGIN))
        
        # ── SHORT SELL targets (market goes DOWN = profit) ──
        # Target: supports BELOW current price (cover position here)
        sell_target_1 = round(price - (atr * TARGET_1_ATR_MULTIPLIER), 2)
        sell_target_2 = round(price - (atr * TARGET_2_ATR_MULTIPLIER), 2)
        if supports:
            # Use nearest support as T1 if it's below price
            s1 = supports[0]
            if s1 < price:
                sell_target_1 = round(max(sell_target_1, s1 * 0.99), 2)
            if len(supports) > 1 and supports[1] < price:
                sell_target_2 = round(max(sell_target_2, supports[1] * 0.99), 2)

        # Stop Loss: ABOVE current price (exit if market goes against short)
        sell_stop_loss = round(price + (atr * STOP_LOSS_ATR_MULTIPLIER), 2)
        if resistances and resistances[0] > price:
            sell_stop_loss = round(max(sell_stop_loss, resistances[0] * (1 + SUPPORT_STOP_MARGIN)), 2)

        # Short entry zones (enter short near current price or resistance bounce)
        sell_zones = []
        sell_zones.append({
            'zone': 'Best Entry (Short)',
            'price_low': round(price * (1 - BEST_ENTRY_TOLERANCE), 2),
            'price_high': round(price * (1 + BEST_ENTRY_TOLERANCE), 2),
            'reason': 'Current market price'
        })
        if resistances and resistances[0] > price:
            sell_zones.append({
                'zone': 'Aggressive Entry',
                'price_low': round(resistances[0] * 0.99, 2),
                'price_high': round(resistances[0] * 1.01, 2),
                'reason': 'Resistance bounce – better risk/reward'
            })
        sell_zones.append({
            'zone': 'Stop Loss (Exit Short)',
            'price_low': sell_stop_loss,
            'price_high': sell_stop_loss,
            'reason': 'Exit if market rises above this'
        })

        # Sell triggers
        sell_triggers = [f"RSI below 30 – oversold caution (Now: {rsi:.0f})"]
        if resistances:
            sell_triggers.append(f"Bounce from resistance ₹{resistances[0]:.0f}")
        if sma_20:
            sell_triggers.append(f"Price below SMA20 ₹{sma_20:.0f}")

        # Exit conditions
        exit_conditions = ["Strong bullish reversal candle", "RSI divergence upward"]
        if resistances:
            exit_conditions.insert(0, f"Close above resistance ₹{resistances[0]:.0f} – danger zone")

        # Risk/Reward for BUY side
        risk = price - buy_stop_loss
        reward = buy_target_1 - price
        risk_reward = round(reward / risk, 2) if risk > 0 else 0

        # Risk/Reward for SELL side
        sell_risk = sell_stop_loss - price
        sell_reward = price - sell_target_1
        sell_risk_reward = round(sell_reward / sell_risk, 2) if sell_risk > 0 else 0

        return {
            'buy_zones': buy_zones,
            'buy_triggers': buy_triggers,
            'buy_target_1': buy_target_1,
            'buy_target_2': buy_target_2,
            'buy_stop_loss': round(buy_stop_loss, 2),
            'sell_zones': sell_zones,
            'sell_triggers': sell_triggers,
            'sell_target_1': sell_target_1,
            'sell_target_2': sell_target_2,
            'sell_stop_loss': sell_stop_loss,
            'sell_risk_reward': sell_risk_reward,
            'exit_conditions': exit_conditions,
            'risk_reward': risk_reward,
            'risk_amount': round(risk, 2),
            'reward_amount': round(reward, 2)
        }

    # ==================== MAIN ANALYSIS ====================
    
    def analyze(self, symbol, df):
        """Complete stock analysis"""
        print(f"   📊 Analyzing {symbol}...")
        
        # 1. Fundamental
        print(f"   📈 Fetching fundamentals...")
        fundamentals = self.get_fundamental_data(symbol)
        fundamental_score, fundamental_factors = self.calculate_fundamental_score(fundamentals)
        
        # 2. Historical
        print(f"   📜 Calculating historical...")
        historical = self.calculate_historical_levels(df)
        historical_score, historical_factors = self.calculate_historical_score(historical)
        
        # 3. Technical
        print(f"   🔧 Calculating technical...")
        technical = self.calculate_technical_indicators(df)
        technical_score, technical_factors = self.calculate_technical_score(technical)
        
        # 4. Trading Plan
        print(f"   🎯 Generating trading plan...")
        trading_plan = self.generate_trading_plan(technical, historical, fundamentals)
        
        # 5. Overall Score
        scores = []
        if fundamental_score:
            scores.append(('Fundamental', fundamental_score, FUNDAMENTAL_WEIGHT))
        if historical_score:
            scores.append(('Historical', historical_score, HISTORICAL_WEIGHT))
        if technical_score:
            scores.append(('Technical', technical_score, TECHNICAL_WEIGHT))
        
        if scores:
            total_weight = sum(s[2] for s in scores)
            overall_score = sum(s[1] * s[2] for s in scores) / total_weight
        else:
            overall_score = 50
        
        # ==================== SMART SIGNAL LOGIC ====================
        # Uses Technical as primary indicator with Fundamental/Historical confirmation
        
        tech_score = technical_score if technical_score else 50
        fund_score = fundamental_score if fundamental_score else 50
        hist_score = historical_score if historical_score else 50
        
        signal = 'HOLD'
        signal_strength = 'WAIT'
        
        # ===== BUY CONDITIONS =====
        # Strong BUY: Technical very strong (>=65) + at least one confirmation
        if tech_score >= 65 and (fund_score >= 50 or hist_score >= 55):
            signal = 'BUY'
            signal_strength = 'STRONG'
        
        # Moderate BUY: Technical good (>=58) + both confirmations
        elif tech_score >= 58 and fund_score >= 48 and hist_score >= 48:
            signal = 'BUY'
            signal_strength = 'MODERATE'
        
        # BUY: Overall positive (>=55) + Technical confirms (>=55)
        elif overall_score >= 55 and tech_score >= 55:
            signal = 'BUY'
            signal_strength = 'MODERATE'
        
        # BUY: Technical strong (>=60) + not negative fundamentals
        elif tech_score >= 60 and fund_score >= 45:
            signal = 'BUY'
            signal_strength = 'MODERATE'
        
        # ===== SELL CONDITIONS =====
        # Strong SELL: Technical very weak (<=35) + at least one confirmation
        elif tech_score <= 35 and (fund_score <= 50 or hist_score <= 45):
            signal = 'SELL'
            signal_strength = 'STRONG'
        
        # Moderate SELL: Technical weak (<=42) + both confirmations
        elif tech_score <= 42 and fund_score <= 52 and hist_score <= 52:
            signal = 'SELL'
            signal_strength = 'MODERATE'
        
        # SELL: Overall negative (<=45) + Technical confirms (<=45)
        elif overall_score <= 45 and tech_score <= 45:
            signal = 'SELL'
            signal_strength = 'MODERATE'
        
        # SELL: Technical weak (<=40) + not strong fundamentals
        elif tech_score <= 40 and fund_score <= 55:
            signal = 'SELL'
            signal_strength = 'MODERATE'
        
        # ===== EDGE CASES FOR MORE SIGNALS =====
        # Mild BUY: Technical slightly positive + Historical support
        elif tech_score >= 52 and hist_score >= 58 and overall_score >= 52:
            signal = 'BUY'
            signal_strength = 'WEAK'
        
        # Mild SELL: Technical slightly negative + Historical resistance
        elif tech_score <= 48 and hist_score <= 42 and overall_score <= 48:
            signal = 'SELL'
            signal_strength = 'WEAK'
        
        # ===== HOLD: Only when genuinely mixed =====
        # (Signal remains 'HOLD' if none of above conditions met)
        
        return {
            'symbol': symbol,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'current_price': technical['current_price'] if technical else None,
            'overall_score': round(overall_score, 1),
            'signal': signal,
            'signal_strength': signal_strength,
            'fundamentals': fundamentals,
            'fundamental_score': fundamental_score,
            'fundamental_factors': fundamental_factors,
            'historical': historical,
            'historical_score': historical_score,
            'historical_factors': historical_factors,
            'technical': technical,
            'technical_score': technical_score,
            'technical_factors': technical_factors,
            'trading_plan': trading_plan
        }

    def display_analysis(self, result):
        """Display comprehensive analysis"""
        symbol = result['symbol']
        price = result['current_price']
        signal = result['signal']
        strength = result['signal_strength']
        score = result['overall_score']
        
        signal_icon = '🟢' if signal == 'BUY' else '🔴' if signal == 'SELL' else '🟡'
        
        print("\n" + "═" * 70)
        print(f"   📊 {symbol} - COMPLETE ANALYSIS")
        print("═" * 70)
        print(f"\n   💰 Price: ₹{price} | {signal_icon} {signal} ({strength}) | Score: {score}/100")
        
        # Scores summary
        print("\n   ┌" + "─" * 50 + "┐")
        if result['fundamental_score']:
            print(f"   │ Fundamental: {result['fundamental_score']}/100" + " " * 30 + "│")
        if result['historical_score']:
            print(f"   │ Historical:  {result['historical_score']}/100" + " " * 30 + "│")
        if result['technical_score']:
            print(f"   │ Technical:   {result['technical_score']}/100" + " " * 30 + "│")
        print("   └" + "─" * 50 + "┘")
        
        # Trading Plan
        plan = result['trading_plan']
        if plan:
            print(f"\n   🎯 TRADING PLAN:")
            print(f"      Target 1: ₹{plan['buy_target_1']} | Target 2: ₹{plan['buy_target_2']}")
            print(f"      Stop Loss: ₹{plan['buy_stop_loss']} | R:R = 1:{plan['risk_reward']}")
        
        print("\n" + "═" * 70)

    def get_report_text(self, result):
        """Generate formatted report text"""
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()
        try:
            self.display_analysis(result)
            return buffer.getvalue()
        finally:
            sys.stdout = old_stdout


if __name__ == "__main__":
    analyzer = ComprehensiveAnalyzer()
    print("Comprehensive Analyzer loaded successfully!")
