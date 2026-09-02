"""
Simple Backtester Module
Provides easy-to-understand backtest results for stock signals

Features:
- Takes a date and shows what signal was generated
- Shows entry price, targets, and stop loss
- Shows whether the signal was successful or not
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from signal_engine import SignalEngine


class SimpleBacktester:
    """
    Simple Backtester - Easy to understand results
    
    Input: Select a date
    Output: Signal for that date + Result (success or failure)
    """
    
    def __init__(self):
        self.engine = SignalEngine()
    
    def run_backtest(self, df, backtest_date, symbol=''):
        """
        Simple backtest for a single date
        
        Parameters:
        - df: DataFrame with OHLCV data
        - backtest_date: Date to backtest (string 'YYYY-MM-DD' or datetime)
        - symbol: Stock symbol for display
        
        Returns:
        - Dictionary with signal details and outcome
        """
        
        # Validate inputs
        if df is None or len(df) < 50:
            return {'error': 'Insufficient data - minimum 50 days required'}
        
        # Convert date
        if isinstance(backtest_date, str):
            backtest_date = pd.to_datetime(backtest_date)
        
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Get data up to backtest date (for signal generation)
        df_past = df[df['Date'] <= backtest_date].copy()
        
        if len(df_past) < 50:
            return {'error': f'Insufficient data before {backtest_date.strftime("%d-%m-%Y")} - need 50 days minimum'}
        
        # Get actual analysis date (last available date before/on backtest_date)
        actual_date = df_past['Date'].iloc[-1]
        
        # Generate signal for that date
        signal_result = self.engine.analyze(df_past)
        
        if 'error' in signal_result:
            return signal_result
        
        # Extract signal info
        signal = signal_result['signal']
        confidence = signal_result['confidence']
        entry_price = signal_result['entry_price']
        target_1 = signal_result['target_price']
        stop_loss = signal_result['stop_loss']
        signal_strength = signal_result.get('signal_strength', 'N/A')
        
        # Calculate Target 2 (1.5x of Target 1 distance from entry)
        if target_1 and signal == 'BUY':
            target_2 = round(entry_price + (target_1 - entry_price) * 1.5, 2)
        elif target_1 and signal == 'SELL':
            target_2 = round(entry_price - (entry_price - target_1) * 1.5, 2)
        else:
            target_2 = None
        
        # Get future data (after signal date)
        df_future = df[df['Date'] > actual_date].copy()
        
        if len(df_future) == 0:
            return {
                'status': 'PENDING',
                'message': 'No future data available - signal is still active',
                'symbol': symbol,
                'signal_date': actual_date.strftime('%d-%m-%Y'),
                'signal': signal,
                'signal_strength': signal_strength,
                'confidence': confidence,
                'entry_price': entry_price,
                'target_1': target_1,
                'target_2': target_2,
                'stop_loss': stop_loss,
            }
        
        # ============ CHECK RESULTS ============
        
        if signal == 'HOLD':
            # HOLD signal - no trade
            return {
                'status': 'NO_TRADE',
                'message': 'HOLD signal - no trade was executed',
                'symbol': symbol,
                'signal_date': actual_date.strftime('%d-%m-%Y'),
                'signal': 'HOLD',
                'signal_strength': 'NEUTRAL',
                'confidence': confidence,
                'entry_price': entry_price,
                'target_1': None,
                'target_2': None,
                'stop_loss': None,
                'result': 'N/A',
                'verdict': 'HOLD - No Action Required'
            }
        
        # Check what happened after signal
        result = self._check_outcome(df_future, signal, entry_price, target_1, target_2, stop_loss)
        
        # Calculate P&L based on result
        if result['target_1_hit']:
            if signal == 'BUY':
                pnl_t1 = round(((target_1 - entry_price) / entry_price) * 100, 2)
            else:
                pnl_t1 = round(((entry_price - target_1) / entry_price) * 100, 2)
        else:
            pnl_t1 = None
            
        if result['target_2_hit']:
            if signal == 'BUY':
                pnl_t2 = round(((target_2 - entry_price) / entry_price) * 100, 2)
            else:
                pnl_t2 = round(((entry_price - target_2) / entry_price) * 100, 2)
        else:
            pnl_t2 = None
            
        if result['stop_hit']:
            if signal == 'BUY':
                pnl_sl = round(((stop_loss - entry_price) / entry_price) * 100, 2)
            else:
                pnl_sl = round(((entry_price - stop_loss) / entry_price) * 100, 2)
        else:
            pnl_sl = None
        
        # Determine verdict
        if result['stop_hit'] and not result['target_1_hit']:
            verdict = 'SIGNAL FAILED - Stop Loss Hit'
            status = 'LOSS'
        elif result['target_1_hit'] and result['target_2_hit']:
            verdict = 'SIGNAL SUCCESSFUL - Both Targets Hit'
            status = 'BIG_WIN'
        elif result['target_1_hit']:
            verdict = 'SIGNAL SUCCESSFUL - Target 1 Hit'
            status = 'WIN'
        elif result['stop_hit'] and result['target_1_hit']:
            verdict = 'PARTIAL - T1 Hit, then SL Hit'
            status = 'PARTIAL'
        else:
            verdict = 'PENDING - Still in trade'
            status = 'OPEN'
        
        return {
            'status': status,
            'symbol': symbol,
            'signal_date': actual_date.strftime('%d-%m-%Y'),
            'signal': signal,
            'signal_strength': signal_strength,
            'confidence': confidence,
            'entry_price': entry_price,
            'target_1': target_1,
            'target_2': target_2,
            'stop_loss': stop_loss,
            
            # Results
            'target_1_hit': result['target_1_hit'],
            'target_1_date': result['target_1_date'],
            'target_1_days': result['target_1_days'],
            'pnl_target_1': pnl_t1,
            
            'target_2_hit': result['target_2_hit'],
            'target_2_date': result['target_2_date'],
            'target_2_days': result['target_2_days'],
            'pnl_target_2': pnl_t2,
            
            'stop_hit': result['stop_hit'],
            'stop_date': result['stop_date'],
            'stop_days': result['stop_days'],
            'pnl_stop': pnl_sl,
            
            'current_price': result['current_price'],
            'current_pnl': result['current_pnl'],
            
            'verdict': verdict,
            
            # Extra info
            'days_since_signal': len(df_future),
            'indicators': signal_result['indicators'],
            'scores': signal_result['scores']
        }
    
    def _check_outcome(self, df_future, signal, entry, t1, t2, sl):
        """Check what happened after signal was generated"""
        
        result = {
            'target_1_hit': False,
            'target_1_date': None,
            'target_1_days': None,
            
            'target_2_hit': False,
            'target_2_date': None,
            'target_2_days': None,
            
            'stop_hit': False,
            'stop_date': None,
            'stop_days': None,
            
            'current_price': df_future['Close'].iloc[-1],
            'current_pnl': 0
        }
        
        # Calculate current P&L
        if signal == 'BUY':
            result['current_pnl'] = round(((result['current_price'] - entry) / entry) * 100, 2)
        else:
            result['current_pnl'] = round(((entry - result['current_price']) / entry) * 100, 2)
        
        # Check each day after signal
        for day_num, (idx, row) in enumerate(df_future.iterrows(), 1):
            
            if signal == 'BUY':
                # Check Target 1
                if t1 and not result['target_1_hit'] and row['High'] >= t1:
                    result['target_1_hit'] = True
                    result['target_1_date'] = row['Date'].strftime('%d-%m-%Y')
                    result['target_1_days'] = day_num
                
                # Check Target 2
                if t2 and not result['target_2_hit'] and row['High'] >= t2:
                    result['target_2_hit'] = True
                    result['target_2_date'] = row['Date'].strftime('%d-%m-%Y')
                    result['target_2_days'] = day_num
                
                # Check Stop Loss
                if sl and not result['stop_hit'] and row['Low'] <= sl:
                    result['stop_hit'] = True
                    result['stop_date'] = row['Date'].strftime('%d-%m-%Y')
                    result['stop_days'] = day_num
                    
            elif signal == 'SELL':
                # Check Target 1
                if t1 and not result['target_1_hit'] and row['Low'] <= t1:
                    result['target_1_hit'] = True
                    result['target_1_date'] = row['Date'].strftime('%d-%m-%Y')
                    result['target_1_days'] = day_num
                
                # Check Target 2
                if t2 and not result['target_2_hit'] and row['Low'] <= t2:
                    result['target_2_hit'] = True
                    result['target_2_date'] = row['Date'].strftime('%d-%m-%Y')
                    result['target_2_days'] = day_num
                
                # Check Stop Loss
                if sl and not result['stop_hit'] and row['High'] >= sl:
                    result['stop_hit'] = True
                    result['stop_date'] = row['Date'].strftime('%d-%m-%Y')
                    result['stop_days'] = day_num
        
        return result
    
    def display_result(self, r):
        """Display result in console format"""
        
        if 'error' in r:
            print(f"\n[ERROR] {r['error']}")
            return
        
        signal_icon = '[BUY]' if r['signal'] == 'BUY' else '[SELL]' if r['signal'] == 'SELL' else '[HOLD]'
        
        print("\n" + "=" * 60)
        print(f"   BACKTEST RESULT: {r.get('symbol', 'STOCK')}")
        print("=" * 60)
        
        print(f"\n   Signal Date: {r['signal_date']}")
        print(f"   {signal_icon} Signal: {r['signal']} ({r['signal_strength']})")
        print(f"   Confidence: {r['confidence']}%")
        
        print(f"\n   Entry Price: {r['entry_price']}")
        if r['target_1']:
            print(f"   Target 1: {r['target_1']}")
        if r['target_2']:
            print(f"   Target 2: {r['target_2']}")
        if r['stop_loss']:
            print(f"   Stop Loss: {r['stop_loss']}")
        
        print("\n   " + "-" * 56)
        print("   RESULT:")
        
        if r['signal'] != 'HOLD':
            # Target 1
            if r.get('target_1_hit'):
                print(f"   [OK] Target 1: HIT on {r['target_1_date']} ({r['target_1_days']} days) | P&L: +{r['pnl_target_1']}%")
            else:
                print(f"   [--] Target 1: Not hit yet")
            
            # Target 2
            if r.get('target_2_hit'):
                print(f"   [OK] Target 2: HIT on {r['target_2_date']} ({r['target_2_days']} days) | P&L: +{r['pnl_target_2']}%")
            elif r.get('target_1_hit'):
                print(f"   [--] Target 2: Not hit yet")
            
            # Stop Loss
            if r.get('stop_hit'):
                print(f"   [XX] Stop Loss: HIT on {r['stop_date']} ({r['stop_days']} days) | P&L: {r['pnl_stop']}%")
            else:
                print(f"   [OK] Stop Loss: Safe")
            
            # Current status
            if r.get('current_price'):
                pnl_status = 'PROFIT' if r['current_pnl'] > 0 else 'LOSS' if r['current_pnl'] < 0 else 'NEUTRAL'
                print(f"\n   Current Price: {round(r['current_price'], 2)} | {pnl_status}: {r['current_pnl']}%")
        
        print("\n   " + "-" * 56)
        print(f"   VERDICT: {r['verdict']}")
        print("=" * 60)


# ============ TEST ============
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   TESTING SIMPLE BACKTESTER")
    print("=" * 60)
    
    # Create test data
    dates = pd.date_range(start='2024-01-01', periods=300, freq='D')
    np.random.seed(42)
    prices = 1000 * np.cumprod(1 + np.random.randn(300) * 0.02)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices * (1 + np.random.randn(300) * 0.005),
        'High': prices * (1 + abs(np.random.randn(300) * 0.015)),
        'Low': prices * (1 - abs(np.random.randn(300) * 0.015)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 300)
    })
    
    bt = SimpleBacktester()
    
    # Test backtest
    result = bt.run_backtest(df, '2024-06-01', 'TEST')
    bt.display_result(result)
    
    print("\n[OK] Test completed!")
