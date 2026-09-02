
import pandas as pd
import numpy as np
from datetime import datetime

# Import configuration
try:
    from config import (
        SIGNAL_WEIGHTS, STRONG_SIGNAL_THRESHOLD, MODERATE_SIGNAL_THRESHOLD,
        STRONG_SIGNAL_MIN_INDICATORS, MODERATE_SIGNAL_MIN_INDICATORS,
        TARGET_MULTIPLIER_STRONG, TARGET_MULTIPLIER_MODERATE,
        STOP_MULTIPLIER_STRONG, STOP_MULTIPLIER_MODERATE
    )
except ImportError:
    # Fallback defaults if config not found
    SIGNAL_WEIGHTS = {
        'rsi': 0.15, 'macd': 0.15, 'ma_trend': 0.15, 'bollinger': 0.10,
        'stochastic': 0.10, 'volume': 0.10, 'momentum': 0.10,
        'atr_position': 0.05, 'adx': 0.10,
    }
    STRONG_SIGNAL_THRESHOLD = 0.15
    MODERATE_SIGNAL_THRESHOLD = 0.08
    STRONG_SIGNAL_MIN_INDICATORS = 4
    MODERATE_SIGNAL_MIN_INDICATORS = 3
    TARGET_MULTIPLIER_STRONG = 2.5
    TARGET_MULTIPLIER_MODERATE = 2.0
    STOP_MULTIPLIER_STRONG = 1.5
    STOP_MULTIPLIER_MODERATE = 1.2


class SignalEngine:
    """
    Dynamic Signal Generator
    - Each indicator produces a CONTINUOUS SCORE (-1 to +1)
    - Scores are WEIGHTED and combined
    - All thresholds loaded from config.py
    """

    def __init__(self):
        # Load from config
        self.weights = SIGNAL_WEIGHTS.copy()
        self.strong_threshold = STRONG_SIGNAL_THRESHOLD
        self.moderate_threshold = MODERATE_SIGNAL_THRESHOLD
        self.strong_min_indicators = STRONG_SIGNAL_MIN_INDICATORS
        self.moderate_min_indicators = MODERATE_SIGNAL_MIN_INDICATORS
        self.target_mult_strong = TARGET_MULTIPLIER_STRONG
        self.target_mult_moderate = TARGET_MULTIPLIER_MODERATE
        self.stop_mult_strong = STOP_MULTIPLIER_STRONG
        self.stop_mult_moderate = STOP_MULTIPLIER_MODERATE

    # ==================== INDICATOR CALCULATIONS ====================

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def calculate_sma(self, prices, period):
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()

    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()

    def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower

    def calculate_stochastic(self, high, low, close, k_period=14, d_period=3):
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
        d = k.rolling(window=d_period).mean()
        return k, d

    def calculate_atr(self, high, low, close, period=14):
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def calculate_adx(self, high, low, close, period=14):
        """Calculate ADX (Average Directional Index)"""
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        atr = self.calculate_atr(high, low, close, period)
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr.replace(0, np.nan))
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr.replace(0, np.nan))
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(window=period).mean()
        return adx, plus_di, minus_di

    def calculate_momentum(self, prices, period=10):
        """Calculate Price Momentum"""
        return prices.pct_change(periods=period) * 100

    # ==================== SCORING FUNCTIONS ====================

    def score_rsi(self, rsi_value):
        """RSI Score: -1 (overbought) to +1 (oversold)"""
        if pd.isna(rsi_value):
            return 0
        score = (50 - rsi_value) / 50
        return np.clip(score, -1, 1)

    def score_macd(self, histogram, histogram_series):
        """MACD Score: Normalized based on recent histogram range"""
        if pd.isna(histogram):
            return 0
        hist_std = histogram_series.std()
        if hist_std == 0 or pd.isna(hist_std):
            return 0
        score = histogram / (2 * hist_std)
        return np.clip(score, -1, 1)

    def score_ma_trend(self, price, sma_20, sma_50, sma_200, atr):
        """Moving Average Trend Score"""
        if pd.isna(price) or pd.isna(atr) or atr == 0:
            return 0
        scores = []
        if not pd.isna(sma_20):
            score_20 = (price - sma_20) / atr
            scores.append(np.clip(score_20 / 2, -1, 1))
        if not pd.isna(sma_50):
            score_50 = (price - sma_50) / atr
            scores.append(np.clip(score_50 / 3, -1, 1))
        if not pd.isna(sma_200):
            score_200 = (price - sma_200) / atr
            scores.append(np.clip(score_200 / 4, -1, 1))
        if not pd.isna(sma_20) and not pd.isna(sma_50) and not pd.isna(sma_200):
            if sma_20 > sma_50 > sma_200:
                scores.append(0.3)
            elif sma_20 < sma_50 < sma_200:
                scores.append(-0.3)
        return np.mean(scores) if scores else 0

    def score_bollinger(self, price, upper, middle, lower):
        """Bollinger Bands Score"""
        if pd.isna(price) or pd.isna(upper) or pd.isna(lower):
            return 0
        band_width = upper - lower
        if band_width == 0:
            return 0
        position = (middle - price) / (band_width / 2)
        return np.clip(position, -1, 1)

    def score_stochastic(self, k_value, d_value):
        """Stochastic Score"""
        if pd.isna(k_value) or pd.isna(d_value):
            return 0
        k_score = (50 - k_value) / 50
        crossover_score = (d_value - k_value) / 100
        combined = (k_score * 0.7) + (-crossover_score * 0.3)
        return np.clip(combined, -1, 1)

    def score_volume(self, current_volume, volume_series):
        """Volume Score"""
        if pd.isna(current_volume):
            return 0
        avg_volume = volume_series.mean()
        if avg_volume == 0 or pd.isna(avg_volume):
            return 0
        ratio = current_volume / avg_volume
        score = (ratio - 1) / 2
        return np.clip(score, -1, 1)

    def score_momentum(self, momentum_value, momentum_series):
        """Momentum Score"""
        if pd.isna(momentum_value):
            return 0
        mom_std = momentum_series.std()
        if mom_std == 0 or pd.isna(mom_std):
            return 0
        score = momentum_value / (2 * mom_std)
        return np.clip(score, -1, 1)

    def score_atr_position(self, price, sma_20, atr):
        """ATR-based Position Score"""
        if pd.isna(price) or pd.isna(sma_20) or pd.isna(atr) or atr == 0:
            return 0
        distance = (price - sma_20) / atr
        score = -distance / 2
        return np.clip(score, -1, 1)

    def score_adx(self, adx_value, plus_di, minus_di):
        """ADX Score"""
        if pd.isna(adx_value) or pd.isna(plus_di) or pd.isna(minus_di):
            return 0
        di_diff = plus_di - minus_di
        di_score = di_diff / 50
        strength_multiplier = min(adx_value / 25, 1)
        score = di_score * strength_multiplier
        return np.clip(score, -1, 1)

    # ==================== MAIN ANALYSIS ====================

    def analyze(self, df, analysis_date=None):
        """Main analysis function - Returns signal, indicators, scores"""
        if df is None or len(df) < 50:
            return {'error': 'Insufficient data (need at least 50 days)'}

        if analysis_date is not None:
            if isinstance(analysis_date, str):
                analysis_date = pd.to_datetime(analysis_date)
            df = df[df['Date'] <= analysis_date].copy()
            if len(df) < 50:
                return {'error': f'Insufficient data before {analysis_date}'}

        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']

        # Calculate all indicators
        rsi = self.calculate_rsi(close)
        macd_line, signal_line, macd_hist = self.calculate_macd(close)
        sma_20 = self.calculate_sma(close, 20)
        sma_50 = self.calculate_sma(close, 50)
        sma_200 = self.calculate_sma(close, 200)
        ema_9 = self.calculate_ema(close, 9)
        ema_21 = self.calculate_ema(close, 21)
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(close)
        stoch_k, stoch_d = self.calculate_stochastic(high, low, close)
        atr = self.calculate_atr(high, low, close)
        adx, plus_di, minus_di = self.calculate_adx(high, low, close)
        momentum = self.calculate_momentum(close)

        idx = -1
        current_price = close.iloc[idx]

        # Calculate all scores
        scores = {
            'rsi': self.score_rsi(rsi.iloc[idx]),
            'macd': self.score_macd(macd_hist.iloc[idx], macd_hist.iloc[-50:]),
            'ma_trend': self.score_ma_trend(
                current_price, sma_20.iloc[idx], sma_50.iloc[idx],
                sma_200.iloc[idx] if len(df) >= 200 else np.nan, atr.iloc[idx]
            ),
            'bollinger': self.score_bollinger(current_price, bb_upper.iloc[idx], bb_middle.iloc[idx], bb_lower.iloc[idx]),
            'stochastic': self.score_stochastic(stoch_k.iloc[idx], stoch_d.iloc[idx]),
            'volume': self.score_volume(volume.iloc[idx], volume.iloc[-20:]),
            'momentum': self.score_momentum(momentum.iloc[idx], momentum.iloc[-50:]),
            'atr_position': self.score_atr_position(current_price, sma_20.iloc[idx], atr.iloc[idx]),
            'adx': self.score_adx(adx.iloc[idx], plus_di.iloc[idx], minus_di.iloc[idx])
        }

        # Calculate weighted final score
        final_score = sum(scores[ind] * self.weights[ind] for ind in scores)

        # Count bullish vs bearish
        bullish_count = sum(1 for s in scores.values() if s > 0.1)
        bearish_count = sum(1 for s in scores.values() if s < -0.1)

        # Determine signal (using config thresholds)
        if final_score > self.strong_threshold and bullish_count >= self.strong_min_indicators:
            signal, signal_strength = 'BUY', 'STRONG'
        elif final_score > self.moderate_threshold and bullish_count >= self.moderate_min_indicators:
            signal, signal_strength = 'BUY', 'MODERATE'
        elif final_score < -self.strong_threshold and bearish_count >= self.strong_min_indicators:
            signal, signal_strength = 'SELL', 'STRONG'
        elif final_score < -self.moderate_threshold and bearish_count >= self.moderate_min_indicators:
            signal, signal_strength = 'SELL', 'MODERATE'
        else:
            signal, signal_strength = 'HOLD', 'NEUTRAL'

        # Confidence
        score_confidence = min(abs(final_score) * 200, 60)
        agreement_confidence = (max(bullish_count, bearish_count) / 9) * 40
        confidence = score_confidence + agreement_confidence

        # Target & Stop Loss
        current_atr = atr.iloc[idx]
        if signal == 'BUY':
            target_mult = self.target_mult_strong if signal_strength == 'STRONG' else self.target_mult_moderate
            stop_mult = self.stop_mult_strong if signal_strength == 'STRONG' else self.stop_mult_moderate
            target_price = current_price + (current_atr * target_mult)
            stop_loss = current_price - (current_atr * stop_mult)
        elif signal == 'SELL':
            target_mult = self.target_mult_strong if signal_strength == 'STRONG' else self.target_mult_moderate
            stop_mult = self.stop_mult_strong if signal_strength == 'STRONG' else self.stop_mult_moderate
            target_price = current_price - (current_atr * target_mult)
            stop_loss = current_price + (current_atr * stop_mult)
        else:
            target_price, stop_loss = None, None

        risk_reward = None
        if target_price and stop_loss and current_price != stop_loss:
            risk_reward = abs(target_price - current_price) / abs(current_price - stop_loss)

        return {
            'date': df['Date'].iloc[idx],
            'signal': signal,
            'signal_strength': signal_strength,
            'confidence': round(confidence, 1),
            'final_score': round(final_score, 4),
            'bullish_indicators': bullish_count,
            'bearish_indicators': bearish_count,
            'entry_price': round(current_price, 2),
            'target_price': round(target_price, 2) if target_price else None,
            'stop_loss': round(stop_loss, 2) if stop_loss else None,
            'risk_reward': round(risk_reward, 2) if risk_reward else None,
            'indicators': {
                'RSI': round(rsi.iloc[idx], 2) if not pd.isna(rsi.iloc[idx]) else None,
                'MACD_Histogram': round(macd_hist.iloc[idx], 4) if not pd.isna(macd_hist.iloc[idx]) else None,
                'MACD_Line': round(macd_line.iloc[idx], 4) if not pd.isna(macd_line.iloc[idx]) else None,
                'Signal_Line': round(signal_line.iloc[idx], 4) if not pd.isna(signal_line.iloc[idx]) else None,
                'SMA_20': round(sma_20.iloc[idx], 2) if not pd.isna(sma_20.iloc[idx]) else None,
                'SMA_50': round(sma_50.iloc[idx], 2) if not pd.isna(sma_50.iloc[idx]) else None,
                'SMA_200': round(sma_200.iloc[idx], 2) if len(df) >= 200 and not pd.isna(sma_200.iloc[idx]) else None,
                'EMA_9': round(ema_9.iloc[idx], 2) if not pd.isna(ema_9.iloc[idx]) else None,
                'EMA_21': round(ema_21.iloc[idx], 2) if not pd.isna(ema_21.iloc[idx]) else None,
                'BB_Upper': round(bb_upper.iloc[idx], 2) if not pd.isna(bb_upper.iloc[idx]) else None,
                'BB_Middle': round(bb_middle.iloc[idx], 2) if not pd.isna(bb_middle.iloc[idx]) else None,
                'BB_Lower': round(bb_lower.iloc[idx], 2) if not pd.isna(bb_lower.iloc[idx]) else None,
                'Stoch_K': round(stoch_k.iloc[idx], 2) if not pd.isna(stoch_k.iloc[idx]) else None,
                'Stoch_D': round(stoch_d.iloc[idx], 2) if not pd.isna(stoch_d.iloc[idx]) else None,
                'ATR': round(atr.iloc[idx], 2) if not pd.isna(atr.iloc[idx]) else None,
                'ADX': round(adx.iloc[idx], 2) if not pd.isna(adx.iloc[idx]) else None,
                '+DI': round(plus_di.iloc[idx], 2) if not pd.isna(plus_di.iloc[idx]) else None,
                '-DI': round(minus_di.iloc[idx], 2) if not pd.isna(minus_di.iloc[idx]) else None,
                'Momentum_10D': round(momentum.iloc[idx], 2) if not pd.isna(momentum.iloc[idx]) else None,
            },
            'scores': {k: round(v, 4) for k, v in scores.items()},
            'weights': self.weights.copy()
        }

    def display_result(self, result, symbol=''):
        """Display analysis result"""
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            return

        signal = result['signal']
        strength = result.get('signal_strength', '')
        
        if signal == 'BUY':
            signal_display = f"🟢 BUY ({strength})"
        elif signal == 'SELL':
            signal_display = f"🔴 SELL ({strength})"
        else:
            signal_display = "🟡 HOLD"

        print("\n" + "=" * 60)
        print(f"   ANALYSIS RESULT: {symbol}")
        print("=" * 60)
        print(f"\n   📅 Date: {result['date']}")
        print(f"\n   📊 SIGNAL: {signal_display}")
        print(f"   📈 Confidence: {result['confidence']}%")
        print(f"   🎯 Final Score: {result['final_score']}")
        print(f"   📊 Bullish: {result['bullish_indicators']}/9 | Bearish: {result['bearish_indicators']}/9")
        
        print(f"\n   💰 Entry: ₹{result['entry_price']}")
        if result['target_price']:
            print(f"   🎯 Target: ₹{result['target_price']} | 🛑 Stop: ₹{result['stop_loss']} | R:R = 1:{result['risk_reward']}")

        print("\n   " + "-" * 56)
        print("   INDICATORS:")
        for name, value in result['indicators'].items():
            if value is not None:
                print(f"   {name:<20}: {value}")
        print("=" * 60)

    def _score_bar(self, score):
        """Create visual bar for score"""
        mid = 10
        if score >= 0:
            filled = int(score * mid)
            bar = ' ' * mid + '|' + '█' * filled + ' ' * (mid - filled)
        else:
            filled = int(abs(score) * mid)
            bar = ' ' * (mid - filled) + '█' * filled + '|' + ' ' * mid
        return f"[{bar}]"


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   TESTING SIGNAL ENGINE")
    print("=" * 50 + "\n")
    
    dates = pd.date_range(start='2024-01-01', periods=250, freq='D')
    np.random.seed(42)
    prices = 1000 * np.cumprod(1 + np.random.randn(250) * 0.02)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices * (1 + np.random.randn(250) * 0.005),
        'High': prices * (1 + abs(np.random.randn(250) * 0.01)),
        'Low': prices * (1 - abs(np.random.randn(250) * 0.01)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 250)
    })

    engine = SignalEngine()
    result = engine.analyze(df)
    engine.display_result(result, 'TEST_STOCK')
