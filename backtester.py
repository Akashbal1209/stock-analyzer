import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

from signal_engine import SignalEngine

# Import configuration
try:
    from config import MIN_DATA_DAYS
except ImportError:
    MIN_DATA_DAYS = 50


class AdvancedBacktester:
    """Advanced Backtesting Engine with 12 features"""

    def __init__(self, commission_pct=0.1):
        """
        Initialize backtester
        commission_pct: Total commission % (buy + sell), default 0.1%
        """
        self.engine = SignalEngine()
        self.results = []
        self.portfolio_results = []
        self.min_data_days = MIN_DATA_DAYS
        self.commission_pct = commission_pct
        
        # Feature 1: Multiple timeframes (trading days)
        self.timeframes = {
            '1_day': 1,
            '3_days': 3,
            '7_days': 5,
            '14_days': 10,
            '30_days': 20,
            '60_days': 40,
        }
        
        # Feature 4: Signal strength buckets
        self.strength_buckets = {
            'HIGH': (75, 100),
            'MEDIUM': (50, 75),
            'LOW': (0, 50),
        }

    def backtest_single_date(self, df, backtest_date, symbol=''):
        """Complete backtest for a single date with all features"""
        if df is None or len(df) < self.min_data_days:
            return {'error': 'Insufficient data'}

        if isinstance(backtest_date, str):
            backtest_date = pd.to_datetime(backtest_date)

        df_full = df.copy()
        df_full['Date'] = pd.to_datetime(df_full['Date'])
        
        signal_result = self.engine.analyze(df_full, analysis_date=backtest_date)
        
        if 'error' in signal_result:
            return signal_result

        actual_date = signal_result['date']
        if isinstance(actual_date, str):
            actual_date = pd.to_datetime(actual_date)

        signal_price = signal_result['entry_price']
        signal = signal_result['signal']
        confidence = signal_result['confidence']
        target_1 = signal_result['target_price']
        stop_loss = signal_result['stop_loss']
        
        # Calculate Target 2 (1.5x of Target 1 distance)
        if target_1 and signal == 'BUY':
            target_2 = signal_price + (target_1 - signal_price) * 1.5
        elif target_1 and signal == 'SELL':
            target_2 = signal_price - (signal_price - target_1) * 1.5
        else:
            target_2 = None

        future_df = df_full[df_full['Date'] > actual_date].copy()
        
        if len(future_df) == 0:
            return {'error': 'No future data available', 'signal_result': signal_result}

        # All features
        outcomes = self._calc_timeframes(future_df, signal_price, signal)
        partial = self._calc_partial_profits(future_df, signal_price, signal, target_1, target_2, stop_loss)
        drawdown = self._calc_drawdown(future_df, signal_price, signal)
        strength = self._get_strength_bucket(confidence)
        mfe_mae = self._calc_mfe_mae(future_df, signal_price, signal)
        time_target = self._calc_time_to_target(future_df, signal_price, signal, target_1, target_2, stop_loss)
        trailing = self._simulate_trailing(future_df, signal_price, signal, stop_loss)
        benchmark = self._calc_benchmark(future_df, signal_price)
        commission_adj = self._apply_commission(outcomes)
        accuracy = self._determine_accuracy(signal, outcomes)

        backtest_result = {
            'symbol': symbol,
            'backtest_date': actual_date,
            'signal': signal,
            'signal_strength': signal_result.get('signal_strength', 'N/A'),
            'confidence': confidence,
            'strength_bucket': strength,
            'signal_price': signal_price,
            'target_1': target_1,
            'target_2': round(target_2, 2) if target_2 else None,
            'stop_loss': stop_loss,
            'outcomes': outcomes,
            'partial_profits': partial,
            'max_drawdown_pct': drawdown['max_drawdown_pct'],
            'max_drawdown_price': drawdown['max_drawdown_price'],
            'mfe_pct': mfe_mae['mfe_pct'],
            'mfe_price': mfe_mae['mfe_price'],
            'mae_pct': mfe_mae['mae_pct'],
            'mae_price': mfe_mae['mae_price'],
            'time_to_target_1': time_target['days_to_target_1'],
            'time_to_target_2': time_target['days_to_target_2'],
            'time_to_stop': time_target['days_to_stop'],
            'target_1_hit': time_target['target_1_hit'],
            'target_2_hit': time_target['target_2_hit'],
            'stop_hit': time_target['stop_hit'],
            'trailing_exit_price': trailing['exit_price'],
            'trailing_exit_date': trailing['exit_date'],
            'trailing_pnl_pct': trailing['pnl_pct'],
            'benchmark_30d_pct': benchmark.get('30_days', 0),
            'outcomes_after_commission': commission_adj,
            'accuracy': accuracy,
            'indicators': signal_result['indicators'],
            'scores': signal_result['scores']
        }

        self.results.append(backtest_result)
        return backtest_result

    # ==================== FEATURE 1: TIMEFRAMES ====================
    
    def _calc_timeframes(self, future_df, signal_price, signal):
        outcomes = {}
        for name, days in self.timeframes.items():
            if len(future_df) >= days:
                price = future_df.iloc[days - 1]['Close']
                change = ((price - signal_price) / signal_price) * 100
                pnl = change if signal == 'BUY' else -change if signal == 'SELL' else 0
                outcomes[name] = {
                    'date': future_df.iloc[days - 1]['Date'],
                    'price': round(price, 2),
                    'change_pct': round(change, 2),
                    'pnl_pct': round(pnl, 2)
                }
        return outcomes

    # ==================== FEATURE 2: PARTIAL PROFITS ====================
    
    def _calc_partial_profits(self, future_df, signal_price, signal, t1, t2, stop):
        result = {'t1_hit': False, 't1_date': None, 't1_pnl_pct': 0,
                  't2_hit': False, 't2_date': None, 't2_pnl_pct': 0,
                  'stop_hit': False, 'stop_date': None, 'total_pnl_pct': 0, 'status': 'OPEN'}
        
        if not t1 or not stop:
            return result
        
        half_exited = False
        
        for idx, row in future_df.iterrows():
            if signal == 'BUY':
                if row['Low'] <= stop and not half_exited:
                    result['stop_hit'], result['stop_date'] = True, row['Date']
                    result['total_pnl_pct'] = round(((stop - signal_price) / signal_price) * 100, 2)
                    result['status'] = 'STOPPED OUT'
                    break
                elif row['Low'] <= stop and half_exited:
                    pnl2 = ((stop - signal_price) / signal_price) * 100 * 0.5
                    result['total_pnl_pct'] = round(result['t1_pnl_pct'] + pnl2, 2)
                    result['status'] = 'PARTIAL WIN'
                    break
                elif row['High'] >= t1 and not half_exited:
                    result['t1_hit'], result['t1_date'] = True, row['Date']
                    result['t1_pnl_pct'] = round(((t1 - signal_price) / signal_price) * 100 * 0.5, 2)
                    half_exited = True
                elif t2 and row['High'] >= t2 and half_exited:
                    result['t2_hit'], result['t2_date'] = True, row['Date']
                    result['t2_pnl_pct'] = round(((t2 - signal_price) / signal_price) * 100 * 0.5, 2)
                    result['total_pnl_pct'] = round(result['t1_pnl_pct'] + result['t2_pnl_pct'], 2)
                    result['status'] = 'FULL TARGET'
                    break
                    
            elif signal == 'SELL':
                if row['High'] >= stop and not half_exited:
                    result['stop_hit'], result['stop_date'] = True, row['Date']
                    result['total_pnl_pct'] = round(((signal_price - stop) / signal_price) * 100, 2)
                    result['status'] = 'STOPPED OUT'
                    break
                elif row['High'] >= stop and half_exited:
                    pnl2 = ((signal_price - stop) / signal_price) * 100 * 0.5
                    result['total_pnl_pct'] = round(result['t1_pnl_pct'] + pnl2, 2)
                    result['status'] = 'PARTIAL WIN'
                    break
                elif row['Low'] <= t1 and not half_exited:
                    result['t1_hit'], result['t1_date'] = True, row['Date']
                    result['t1_pnl_pct'] = round(((signal_price - t1) / signal_price) * 100 * 0.5, 2)
                    half_exited = True
                elif t2 and row['Low'] <= t2 and half_exited:
                    result['t2_hit'], result['t2_date'] = True, row['Date']
                    result['t2_pnl_pct'] = round(((signal_price - t2) / signal_price) * 100 * 0.5, 2)
                    result['total_pnl_pct'] = round(result['t1_pnl_pct'] + result['t2_pnl_pct'], 2)
                    result['status'] = 'FULL TARGET'
                    break
        
        return result

    # ==================== FEATURE 3: DRAWDOWN ====================
    
    def _calc_drawdown(self, future_df, signal_price, signal):
        if signal == 'BUY':
            worst = future_df['Low'].min()
            dd = ((worst - signal_price) / signal_price) * 100
        elif signal == 'SELL':
            worst = future_df['High'].max()
            dd = ((signal_price - worst) / signal_price) * 100
        else:
            return {'max_drawdown_pct': 0, 'max_drawdown_price': signal_price}
        return {'max_drawdown_pct': round(min(dd, 0), 2), 'max_drawdown_price': round(worst, 2)}

    # ==================== FEATURE 4: STRENGTH BUCKET ====================
    
    def _get_strength_bucket(self, confidence):
        for bucket, (low, high) in self.strength_buckets.items():
            if low <= confidence < high:
                return bucket
        return 'HIGH' if confidence >= 75 else 'LOW'

    # ==================== FEATURE 5: MFE/MAE ====================
    
    def _calc_mfe_mae(self, future_df, signal_price, signal):
        if signal == 'BUY':
            best, worst = future_df['High'].max(), future_df['Low'].min()
            mfe = ((best - signal_price) / signal_price) * 100
            mae = ((worst - signal_price) / signal_price) * 100
        elif signal == 'SELL':
            best, worst = future_df['Low'].min(), future_df['High'].max()
            mfe = ((signal_price - best) / signal_price) * 100
            mae = ((signal_price - worst) / signal_price) * 100
        else:
            return {'mfe_pct': 0, 'mfe_price': signal_price, 'mae_pct': 0, 'mae_price': signal_price}
        return {'mfe_pct': round(mfe, 2), 'mfe_price': round(best, 2),
                'mae_pct': round(mae, 2), 'mae_price': round(worst, 2)}

    # ==================== FEATURE 6: TIME TO TARGET ====================
    
    def _calc_time_to_target(self, future_df, signal_price, signal, t1, t2, stop):
        result = {'days_to_target_1': None, 'days_to_target_2': None, 'days_to_stop': None,
                  'target_1_hit': False, 'target_2_hit': False, 'stop_hit': False}
        if not t1 or not stop:
            return result
        
        for day, (idx, row) in enumerate(future_df.iterrows(), 1):
            if signal == 'BUY':
                if row['High'] >= t1 and not result['target_1_hit']:
                    result['days_to_target_1'], result['target_1_hit'] = day, True
                if t2 and row['High'] >= t2 and not result['target_2_hit']:
                    result['days_to_target_2'], result['target_2_hit'] = day, True
                if row['Low'] <= stop and not result['stop_hit']:
                    result['days_to_stop'], result['stop_hit'] = day, True
            elif signal == 'SELL':
                if row['Low'] <= t1 and not result['target_1_hit']:
                    result['days_to_target_1'], result['target_1_hit'] = day, True
                if t2 and row['Low'] <= t2 and not result['target_2_hit']:
                    result['days_to_target_2'], result['target_2_hit'] = day, True
                if row['High'] >= stop and not result['stop_hit']:
                    result['days_to_stop'], result['stop_hit'] = day, True
        return result

    # ==================== FEATURE 7: TRAILING STOP ====================
    
    def _simulate_trailing(self, future_df, signal_price, signal, initial_stop, trail_pct=2.0):
        result = {'exit_price': None, 'exit_date': None, 'pnl_pct': 0}
        if signal == 'HOLD' or not initial_stop:
            return result
        
        current_stop, best = initial_stop, signal_price
        
        for idx, row in future_df.iterrows():
            if signal == 'BUY':
                if row['High'] > best:
                    best = row['High']
                    current_stop = max(current_stop, best * (1 - trail_pct / 100))
                if row['Low'] <= current_stop:
                    result['exit_price'] = round(current_stop, 2)
                    result['exit_date'] = row['Date']
                    result['pnl_pct'] = round(((current_stop - signal_price) / signal_price) * 100, 2)
                    return result
            elif signal == 'SELL':
                if row['Low'] < best:
                    best = row['Low']
                    current_stop = min(current_stop, best * (1 + trail_pct / 100))
                if row['High'] >= current_stop:
                    result['exit_price'] = round(current_stop, 2)
                    result['exit_date'] = row['Date']
                    result['pnl_pct'] = round(((signal_price - current_stop) / signal_price) * 100, 2)
                    return result
        
        last = future_df.iloc[-1]['Close']
        result['exit_price'] = round(last, 2)
        result['exit_date'] = future_df.iloc[-1]['Date']
        result['pnl_pct'] = round(((last - signal_price) / signal_price) * 100, 2) if signal == 'BUY' else round(((signal_price - last) / signal_price) * 100, 2)
        return result

    # ==================== FEATURE 8: PORTFOLIO ====================
    
    def backtest_portfolio(self, stocks_data, backtest_date, capital=100000):
        results = []
        per_stock = capital / len(stocks_data)
        
        for symbol, df in stocks_data.items():
            r = self.backtest_single_date(df, backtest_date, symbol)
            if 'error' not in r:
                r['allocated'] = per_stock
                pnl = r['outcomes'].get('30_days', {}).get('pnl_pct', 0)
                r['abs_pnl'] = round(per_stock * pnl / 100, 2)
                results.append(r)
        
        total_pnl = sum(r['abs_pnl'] for r in results)
        return {
            'date': backtest_date, 'stocks': len(results), 'capital': capital,
            'total_pnl': round(total_pnl, 2),
            'return_pct': round((total_pnl / capital) * 100, 2),
            'winners': sum(1 for r in results if r['abs_pnl'] > 0),
            'losers': sum(1 for r in results if r['abs_pnl'] < 0),
            'results': results
        }

    # ==================== FEATURE 9: BENCHMARK ====================
    
    def _calc_benchmark(self, future_df, signal_price):
        benchmark = {}
        for name, days in self.timeframes.items():
            if len(future_df) >= days:
                price = future_df.iloc[days - 1]['Close']
                benchmark[name] = round(((price - signal_price) / signal_price) * 100, 2)
        return benchmark

    # ==================== FEATURE 10: WIN RATE BY TYPE ====================
    
    def get_win_rate_by_signal_type(self):
        if not self.results:
            return None
        
        buy = [r for r in self.results if r['signal'] == 'BUY']
        sell = [r for r in self.results if r['signal'] == 'SELL']
        
        buy_correct = sum(1 for r in buy if 'CORRECT' in str(r.get('accuracy', '')))
        sell_correct = sum(1 for r in sell if 'CORRECT' in str(r.get('accuracy', '')))
        
        buy_pnl = [r['outcomes'].get('7_days', {}).get('pnl_pct', 0) for r in buy]
        sell_pnl = [r['outcomes'].get('7_days', {}).get('pnl_pct', 0) for r in sell]
        
        return {
            'buy': {'total': len(buy), 'correct': buy_correct,
                    'win_rate': round(buy_correct / len(buy) * 100, 1) if buy else 0,
                    'avg_pnl': round(sum(buy_pnl) / len(buy_pnl), 2) if buy_pnl else 0},
            'sell': {'total': len(sell), 'correct': sell_correct,
                     'win_rate': round(sell_correct / len(sell) * 100, 1) if sell else 0,
                     'avg_pnl': round(sum(sell_pnl) / len(sell_pnl), 2) if sell_pnl else 0}
        }

    def get_win_rate_by_strength(self):
        buckets = {'HIGH': [], 'MEDIUM': [], 'LOW': []}
        for r in self.results:
            b = r.get('strength_bucket', 'LOW')
            if b in buckets:
                buckets[b].append(r)
        
        result = {}
        for b, signals in buckets.items():
            if signals:
                correct = sum(1 for s in signals if 'CORRECT' in str(s.get('accuracy', '')))
                pnl = [s['outcomes'].get('7_days', {}).get('pnl_pct', 0) for s in signals]
                result[b] = {'total': len(signals), 'correct': correct,
                             'win_rate': round(correct / len(signals) * 100, 1),
                             'avg_pnl': round(sum(pnl) / len(pnl), 2)}
            else:
                result[b] = {'total': 0, 'correct': 0, 'win_rate': 0, 'avg_pnl': 0}
        return result

    # ==================== FEATURE 11: COMMISSION ====================
    
    def _apply_commission(self, outcomes):
        return {tf: {'price': d['price'], 'change_pct': d['change_pct'],
                     'pnl_pct': round(d['pnl_pct'] - self.commission_pct, 2)}
                for tf, d in outcomes.items()}

    def _determine_accuracy(self, signal, outcomes):
        if signal == 'HOLD':
            return 'N/A'
        if '7_days' in outcomes:
            c = outcomes['7_days']['change_pct']
            if (signal == 'BUY' and c > 0) or (signal == 'SELL' and c < 0):
                return '✅ CORRECT'
            elif c == 0:
                return '➖ NEUTRAL'
            else:
                return '❌ INCORRECT'
        return 'N/A'

    # ==================== FEATURE 12: EXPORT ====================
    
    def export_to_csv(self, filename=None):
        if not self.results:
            print("❌ No results")
            return None
        
        if not filename:
            filename = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        rows = []
        for r in self.results:
            row = {'Symbol': r['symbol'], 'Date': r['backtest_date'], 'Signal': r['signal'],
                   'Confidence': r['confidence'], 'Strength': r['strength_bucket'],
                   'Entry': r['signal_price'], 'T1': r['target_1'], 'T2': r['target_2'],
                   'Stop': r['stop_loss'], 'Drawdown': r['max_drawdown_pct'],
                   'MFE': r['mfe_pct'], 'MAE': r['mae_pct'],
                   'Days_T1': r['time_to_target_1'], 'T1_Hit': r['target_1_hit'],
                   'Trailing_PnL': r['trailing_pnl_pct'], 'Accuracy': r['accuracy']}
            for tf in self.timeframes:
                if tf in r['outcomes']:
                    row[f'PnL_{tf}'] = r['outcomes'][tf]['pnl_pct']
            rows.append(row)
        
        pd.DataFrame(rows).to_csv(filename, index=False)
        print(f"✅ CSV: {os.path.abspath(filename)}")
        return filename

    def export_to_html(self, filename=None):
        if not self.results:
            print("❌ No results")
            return None
        
        if not filename:
            filename = f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        summary = self.get_summary_stats()
        signal_stats = self.get_win_rate_by_signal_type()
        strength_stats = self.get_win_rate_by_strength()
        
        html = f"""<!DOCTYPE html>
<html><head><title>Backtest Report</title>
<style>
body{{font-family:Arial;margin:20px;background:#f5f5f5}}
.container{{max-width:1200px;margin:0 auto;background:white;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}}
h1{{color:#333;text-align:center}}h2{{color:#666;border-bottom:2px solid #667eea;padding-bottom:10px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin:20px 0}}
.card{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px;border-radius:10px;text-align:center}}
.val{{font-size:32px;font-weight:bold}}.lbl{{font-size:14px;opacity:0.9}}
table{{width:100%;border-collapse:collapse;margin:20px 0}}
th,td{{padding:12px;text-align:left;border-bottom:1px solid #ddd}}
th{{background:#667eea;color:white}}tr:hover{{background:#f5f5f5}}
.pos{{color:#22c55e;font-weight:bold}}.neg{{color:#ef4444;font-weight:bold}}
</style></head><body><div class="container">
<h1>📊 Backtest Report</h1>
<p style="text-align:center;color:#666">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<h2>📈 Summary</h2>
<div class="grid">
<div class="card"><div class="val">{summary['total_signals']}</div><div class="lbl">Total Signals</div></div>
<div class="card"><div class="val">{summary['accuracy_pct']}%</div><div class="lbl">Accuracy</div></div>
<div class="card"><div class="val">{summary['avg_pnl_7d']}%</div><div class="lbl">Avg P&L (7D)</div></div>
<div class="card"><div class="val">{summary['avg_mfe']}%</div><div class="lbl">Avg Max Profit</div></div>
</div>

<h2>🎯 Signal Type</h2>
<table><tr><th>Type</th><th>Total</th><th>Correct</th><th>Win Rate</th><th>Avg P&L</th></tr>
<tr><td>🟢 BUY</td><td>{signal_stats['buy']['total']}</td><td>{signal_stats['buy']['correct']}</td><td>{signal_stats['buy']['win_rate']}%</td><td class="{'pos' if signal_stats['buy']['avg_pnl']>0 else 'neg'}">{signal_stats['buy']['avg_pnl']}%</td></tr>
<tr><td>🔴 SELL</td><td>{signal_stats['sell']['total']}</td><td>{signal_stats['sell']['correct']}</td><td>{signal_stats['sell']['win_rate']}%</td><td class="{'pos' if signal_stats['sell']['avg_pnl']>0 else 'neg'}">{signal_stats['sell']['avg_pnl']}%</td></tr>
</table>

<h2>💪 Strength Analysis</h2>
<table><tr><th>Strength</th><th>Total</th><th>Win Rate</th><th>Avg P&L</th></tr>
<tr><td>🔥 HIGH</td><td>{strength_stats['HIGH']['total']}</td><td>{strength_stats['HIGH']['win_rate']}%</td><td class="{'pos' if strength_stats['HIGH']['avg_pnl']>0 else 'neg'}">{strength_stats['HIGH']['avg_pnl']}%</td></tr>
<tr><td>⚡ MEDIUM</td><td>{strength_stats['MEDIUM']['total']}</td><td>{strength_stats['MEDIUM']['win_rate']}%</td><td class="{'pos' if strength_stats['MEDIUM']['avg_pnl']>0 else 'neg'}">{strength_stats['MEDIUM']['avg_pnl']}%</td></tr>
<tr><td>💤 LOW</td><td>{strength_stats['LOW']['total']}</td><td>{strength_stats['LOW']['win_rate']}%</td><td class="{'pos' if strength_stats['LOW']['avg_pnl']>0 else 'neg'}">{strength_stats['LOW']['avg_pnl']}%</td></tr>
</table>

<h2>📋 All Trades</h2>
<table><tr><th>Symbol</th><th>Date</th><th>Signal</th><th>Entry</th><th>7D P&L</th><th>30D P&L</th><th>MFE</th><th>MAE</th><th>Result</th></tr>
"""
        for r in self.results:
            p7 = r['outcomes'].get('7_days', {}).get('pnl_pct', 0)
            p30 = r['outcomes'].get('30_days', {}).get('pnl_pct', 0)
            icon = '🟢' if r['signal']=='BUY' else '🔴' if r['signal']=='SELL' else '🟡'
            html += f"<tr><td>{r['symbol']}</td><td>{r['backtest_date']}</td><td>{icon} {r['signal']}</td><td>₹{r['signal_price']}</td>"
            html += f"<td class='{'pos' if p7>0 else 'neg'}'>{p7}%</td><td class='{'pos' if p30>0 else 'neg'}'>{p30}%</td>"
            html += f"<td class='pos'>+{r['mfe_pct']}%</td><td class='neg'>{r['mae_pct']}%</td><td>{r['accuracy']}</td></tr>\n"
        
        html += "</table></div></body></html>"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ HTML: {os.path.abspath(filename)}")
        return filename

    # ==================== SUMMARY ====================
    
    def get_summary_stats(self):
        if not self.results:
            return None
        
        total = len(self.results)
        buy = sum(1 for r in self.results if r['signal'] == 'BUY')
        sell = sum(1 for r in self.results if r['signal'] == 'SELL')
        hold = sum(1 for r in self.results if r['signal'] == 'HOLD')
        
        correct = sum(1 for r in self.results if 'CORRECT' in str(r.get('accuracy', '')))
        incorrect = sum(1 for r in self.results if 'INCORRECT' in str(r.get('accuracy', '')))
        
        pnl7 = [r['outcomes'].get('7_days', {}).get('pnl_pct', 0) for r in self.results if r['signal'] != 'HOLD']
        pnl30 = [r['outcomes'].get('30_days', {}).get('pnl_pct', 0) for r in self.results if r['signal'] != 'HOLD']
        mfe = [r['mfe_pct'] for r in self.results if r['signal'] != 'HOLD']
        mae = [r['mae_pct'] for r in self.results if r['signal'] != 'HOLD']
        dd = [r['max_drawdown_pct'] for r in self.results if r['signal'] != 'HOLD']
        
        t1_hits = sum(1 for r in self.results if r.get('target_1_hit'))
        t2_hits = sum(1 for r in self.results if r.get('target_2_hit'))
        stop_hits = sum(1 for r in self.results if r.get('stop_hit'))
        time_t1 = [r['time_to_target_1'] for r in self.results if r.get('time_to_target_1')]
        
        active = total - hold
        
        return {
            'total_signals': total, 'buy_signals': buy, 'sell_signals': sell, 'hold_signals': hold,
            'correct_signals': correct, 'incorrect_signals': incorrect,
            'accuracy_pct': round(correct / (correct + incorrect) * 100, 1) if (correct + incorrect) > 0 else 0,
            'avg_pnl_7d': round(sum(pnl7) / len(pnl7), 2) if pnl7 else 0,
            'avg_pnl_30d': round(sum(pnl30) / len(pnl30), 2) if pnl30 else 0,
            'avg_mfe': round(sum(mfe) / len(mfe), 2) if mfe else 0,
            'avg_mae': round(sum(mae) / len(mae), 2) if mae else 0,
            'avg_drawdown': round(sum(dd) / len(dd), 2) if dd else 0,
            'target_1_hit_rate': round(t1_hits / active * 100, 1) if active > 0 else 0,
            'target_2_hit_rate': round(t2_hits / active * 100, 1) if active > 0 else 0,
            'stop_hit_rate': round(stop_hits / active * 100, 1) if active > 0 else 0,
            'avg_days_to_t1': round(sum(time_t1) / len(time_t1), 1) if time_t1 else 0
        }

    # ==================== DISPLAY ====================
    
    def display_result(self, r):
        if 'error' in r:
            print(f"❌ {r['error']}")
            return
        
        icon = '🟢' if r['signal']=='BUY' else '🔴' if r['signal']=='SELL' else '🟡'
        
        print("\n" + "="*80)
        print(f"   BACKTEST: {r['symbol']}")
        print("="*80)
        print(f"   📅 {r['backtest_date']} | {icon} {r['signal']} ({r['signal_strength']})")
        print(f"   💪 {r['strength_bucket']} ({r['confidence']}%) | Entry: ₹{r['signal_price']}")
        print(f"   🎯 T1: ₹{r['target_1']} | T2: ₹{r['target_2']} | Stop: ₹{r['stop_loss']}")
        
        print("\n   📈 OUTCOMES:")
        for tf, d in r['outcomes'].items():
            i = '🟢' if d['pnl_pct']>0 else '🔴' if d['pnl_pct']<0 else '⚪'
            print(f"   {tf:<10}: ₹{d['price']:<8} {d['change_pct']:+.2f}% {i} P&L: {d['pnl_pct']:+.2f}%")
        
        print(f"\n   📊 MFE: +{r['mfe_pct']}% | MAE: {r['mae_pct']}% | DD: {r['max_drawdown_pct']}%")
        print(f"   ⏱️ Days to T1: {r['time_to_target_1']} | Trailing P&L: {r['trailing_pnl_pct']}%")
        print(f"   📋 {r['accuracy']}")
        print("="*80)

    def display_summary(self):
        s = self.get_summary_stats()
        if not s:
            print("❌ No results")
            return
        
        print("\n" + "="*80)
        print("   📊 BACKTEST SUMMARY")
        print("="*80)
        print(f"   Total: {s['total_signals']} | BUY: {s['buy_signals']} | SELL: {s['sell_signals']} | HOLD: {s['hold_signals']}")
        print(f"   ✅ Correct: {s['correct_signals']} | ❌ Wrong: {s['incorrect_signals']} | Accuracy: {s['accuracy_pct']}%")
        print(f"   💰 Avg P&L: 7D={s['avg_pnl_7d']}% | 30D={s['avg_pnl_30d']}%")
        print(f"   📈 Avg MFE: +{s['avg_mfe']}% | MAE: {s['avg_mae']}% | DD: {s['avg_drawdown']}%")
        print(f"   🎯 T1 Hit: {s['target_1_hit_rate']}% | T2 Hit: {s['target_2_hit_rate']}% | Stop Hit: {s['stop_hit_rate']}%")
        print(f"   ⏱️ Avg Days to T1: {s['avg_days_to_t1']}")
        print("="*80)

    def clear_results(self):
        self.results = []
        self.portfolio_results = []


# ==================== TEST ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("   TESTING ADVANCED BACKTESTER")
    print("="*60)
    
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

    bt = AdvancedBacktester(commission_pct=0.1)
    
    print("\n📊 Single backtest...")
    r = bt.backtest_single_date(df, '2024-06-01', 'TEST')
    bt.display_result(r)
    
    print("\n📊 Range backtest...")
    for d in ['2024-03-01', '2024-04-01', '2024-05-01', '2024-07-01']:
        bt.backtest_single_date(df, d, 'TEST')
    
    bt.display_summary()
    
    print("\n📊 Win rates...")
    ws = bt.get_win_rate_by_signal_type()
    print(f"   BUY: {ws['buy']['win_rate']}% | SELL: {ws['sell']['win_rate']}%")
    
    ss = bt.get_win_rate_by_strength()
    print(f"   HIGH: {ss['HIGH']['win_rate']}% | MED: {ss['MEDIUM']['win_rate']}% | LOW: {ss['LOW']['win_rate']}%")
    
    print("\n📤 Exporting...")
    bt.export_to_csv()
    bt.export_to_html()
    
    print("\n✅ Done!")
