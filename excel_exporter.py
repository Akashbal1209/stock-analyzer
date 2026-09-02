import pandas as pd
from datetime import datetime
import os
import subprocess
import platform


class ExcelExporter:
    def __init__(self):
        self.live_signals = []
        self.backtest_results = []
        self.search_history = []

    def add_live_signal(self, symbol, name, result):
        """Add a live signal to history"""
        if 'error' in result:
            return
        
        self.live_signals.append({
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Symbol': symbol,
            'Name': name,
            'Signal': result['signal'],
            'Confidence': result['confidence'],
            'Entry_Price': result['entry_price'],
            'Target_Price': result.get('target_1') or result.get('target_price'),
            'Stop_Loss': result.get('stop_loss'),
            'Risk_Reward': result.get('risk_reward'),
            'Final_Score': result['final_score'],
            'RSI': result['indicators'].get('RSI'),
            'MACD_Hist': result['indicators'].get('MACD_Histogram'),
            'SMA_20': result['indicators'].get('SMA_20'),
            'SMA_50': result['indicators'].get('SMA_50'),
            'Stoch_K': result['indicators'].get('Stoch_K'),
            'ADX': result['indicators'].get('ADX'),
            'ATR': result['indicators'].get('ATR'),
        })

    def add_backtest_result(self, result):
        """Add a backtest result to history"""
        if 'error' in result:
            return
        
        outcomes = result.get('outcomes', {})
        
        self.backtest_results.append({
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Symbol': result['symbol'],
            'Backtest_Date': result['backtest_date'],
            'Signal': result['signal'],
            'Confidence': result['confidence'],
            'Signal_Price': result.get('signal_price'),
            'Target_Price': result.get('target_1') or result.get('target_price'),
            'Stop_Loss': result.get('stop_loss'),
            'Price_1D': outcomes.get('1_day', {}).get('price'),
            'Change_1D_Pct': outcomes.get('1_day', {}).get('change_pct'),
            'PnL_1D_Pct': outcomes.get('1_day', {}).get('pnl_pct'),
            'Price_7D': outcomes.get('7_days', {}).get('price'),
            'Change_7D_Pct': outcomes.get('7_days', {}).get('change_pct'),
            'PnL_7D_Pct': outcomes.get('7_days', {}).get('pnl_pct'),
            'Price_30D': outcomes.get('30_days', {}).get('price'),
            'Change_30D_Pct': outcomes.get('30_days', {}).get('change_pct'),
            'PnL_30D_Pct': outcomes.get('30_days', {}).get('pnl_pct'),
            'Target_Hit': result.get('target_1_hit') or result.get('target_hit'),
            'Stop_Hit': result.get('stop_hit'),
            'Accuracy': result['accuracy'],
        })

    def add_search(self, query, matched_symbol, matched_name, category):
        """Add a search to history"""
        self.search_history.append({
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Search_Query': query,
            'Matched_Symbol': matched_symbol,
            'Matched_Name': matched_name,
            'Category': category,
        })

    def get_performance_summary(self):
        """Generate performance summary data"""
        summary = []
        
        summary.append({'Metric': 'Total Live Signals', 'Value': len(self.live_signals)})
        
        buy_count = sum(1 for s in self.live_signals if s['Signal'] == 'BUY')
        sell_count = sum(1 for s in self.live_signals if s['Signal'] == 'SELL')
        hold_count = sum(1 for s in self.live_signals if s['Signal'] == 'HOLD')
        
        summary.append({'Metric': 'BUY Signals', 'Value': buy_count})
        summary.append({'Metric': 'SELL Signals', 'Value': sell_count})
        summary.append({'Metric': 'HOLD Signals', 'Value': hold_count})
        
        summary.append({'Metric': '', 'Value': ''})
        summary.append({'Metric': 'Total Backtests', 'Value': len(self.backtest_results)})
        
        correct = sum(1 for b in self.backtest_results if 'CORRECT' in str(b.get('Accuracy', '')))
        incorrect = sum(1 for b in self.backtest_results if 'INCORRECT' in str(b.get('Accuracy', '')))
        
        summary.append({'Metric': 'Correct Signals', 'Value': correct})
        summary.append({'Metric': 'Incorrect Signals', 'Value': incorrect})
        
        if correct + incorrect > 0:
            accuracy = round(correct / (correct + incorrect) * 100, 1)
            summary.append({'Metric': 'Accuracy %', 'Value': f"{accuracy}%"})
        
        pnl_values = [b['PnL_7D_Pct'] for b in self.backtest_results 
                      if b.get('PnL_7D_Pct') is not None and b['Signal'] != 'HOLD']
        
        if pnl_values:
            avg_pnl = round(sum(pnl_values) / len(pnl_values), 2)
            summary.append({'Metric': 'Avg 7-Day P&L %', 'Value': f"{avg_pnl}%"})
            
            best_pnl = max(pnl_values)
            worst_pnl = min(pnl_values)
            summary.append({'Metric': 'Best Trade P&L %', 'Value': f"{best_pnl}%"})
            summary.append({'Metric': 'Worst Trade P&L %', 'Value': f"{worst_pnl}%"})
        
        summary.append({'Metric': '', 'Value': ''})
        summary.append({'Metric': 'Total Searches', 'Value': len(self.search_history)})
        
        return summary

    def export_to_excel(self, filename=None, auto_open=True):
        """
        Export all data to Excel file
        
        Parameters:
        - filename: Output filename (default: auto-generated with timestamp)
        - auto_open: Whether to automatically open the file after creation
        
        Returns:
        - Path to created file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Stock_Analysis_History_{timestamp}.xlsx"
        
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
                if self.live_signals:
                    df_signals = pd.DataFrame(self.live_signals)
                    df_signals.to_excel(writer, sheet_name='Live_Signals', index=False)
                else:
                    pd.DataFrame({'Message': ['No live signals recorded yet']}).to_excel(
                        writer, sheet_name='Live_Signals', index=False)
                
                if self.backtest_results:
                    df_backtest = pd.DataFrame(self.backtest_results)
                    df_backtest.to_excel(writer, sheet_name='Backtest_Results', index=False)
                else:
                    pd.DataFrame({'Message': ['No backtest results recorded yet']}).to_excel(
                        writer, sheet_name='Backtest_Results', index=False)
                
                if self.search_history:
                    df_search = pd.DataFrame(self.search_history)
                    df_search.to_excel(writer, sheet_name='Search_History', index=False)
                else:
                    pd.DataFrame({'Message': ['No searches recorded yet']}).to_excel(
                        writer, sheet_name='Search_History', index=False)
                
                summary_data = self.get_performance_summary()
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Performance_Summary', index=False)

            full_path = os.path.abspath(filename)
            print(f"\n✅ Excel file created: {full_path}")
            
            if auto_open:
                self.open_excel_file(full_path)
            
            return full_path
            
        except Exception as e:
            print(f"\n❌ Error creating Excel file: {e}")
            return None

    def open_excel_file(self, filepath):
        """Open Excel file automatically based on OS"""
        try:
            system = platform.system()
            
            if system == 'Windows':
                os.startfile(filepath)
                print("✅ Excel file opened automatically!")
                
            elif system == 'Darwin':
                subprocess.run(['open', filepath])
                print("✅ Excel file opened automatically!")
                
            elif system == 'Linux':
                subprocess.run(['xdg-open', filepath])
                print("✅ Excel file opened automatically!")
                
            else:
                print(f"⚠️ Could not auto-open file on {system}. Please open manually.")
                
        except Exception as e:
            print(f"⚠️ Could not auto-open file: {e}")
            print(f"   Please open manually: {filepath}")

    def export_live_signals_only(self, filename=None, auto_open=True):
        """Export only live signals"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Live_Signals_{timestamp}.xlsx"
        
        if not self.live_signals:
            print("❌ No live signals to export")
            return None
        
        try:
            df = pd.DataFrame(self.live_signals)
            df.to_excel(filename, index=False)
            full_path = os.path.abspath(filename)
            print(f"\n✅ Live signals exported: {full_path}")
            
            if auto_open:
                self.open_excel_file(full_path)
            
            return full_path
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def export_backtest_only(self, filename=None, auto_open=True):
        """Export only backtest results"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Backtest_Results_{timestamp}.xlsx"
        
        if not self.backtest_results:
            print("❌ No backtest results to export")
            return None
        
        try:
            df = pd.DataFrame(self.backtest_results)
            df.to_excel(filename, index=False)
            full_path = os.path.abspath(filename)
            print(f"\n✅ Backtest results exported: {full_path}")
            
            if auto_open:
                self.open_excel_file(full_path)
            
            return full_path
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def clear_history(self):
        """Clear all stored history"""
        self.live_signals = []
        self.backtest_results = []
        self.search_history = []
        print("✅ All history cleared")

    def get_stats(self):
        """Get current stats"""
        return {
            'live_signals': len(self.live_signals),
            'backtest_results': len(self.backtest_results),
            'searches': len(self.search_history)
        }


# Test the module
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   TESTING EXCEL EXPORTER MODULE")
    print("=" * 50 + "\n")
    
    exporter = ExcelExporter()
    
    sample_result = {
        'signal': 'BUY',
        'confidence': 75.5,
        'entry_price': 1250.00,
        'target_price': 1320.00,
        'stop_loss': 1210.00,
        'risk_reward': 1.75,
        'final_score': 0.45,
        'indicators': {
            'RSI': 42.5,
            'MACD_Histogram': 2.35,
            'SMA_20': 1235.50,
            'SMA_50': 1220.00,
            'Stoch_K': 35.2,
            'ADX': 28.5,
            'ATR': 25.3
        }
    }
    exporter.add_live_signal('RELIANCE', 'Reliance Industries Ltd', sample_result)
    
    sample_backtest = {
        'symbol': 'RELIANCE',
        'backtest_date': '2024-01-15',
        'signal': 'BUY',
        'confidence': 72.0,
        'signal_price': 1180.00,
        'target_price': 1250.00,
        'stop_loss': 1140.00,
        'outcomes': {
            '1_day': {'price': 1195.00, 'change_pct': 1.27, 'pnl_pct': 1.27},
            '7_days': {'price': 1240.00, 'change_pct': 5.08, 'pnl_pct': 5.08},
            '30_days': {'price': 1280.00, 'change_pct': 8.47, 'pnl_pct': 8.47},
        },
        'target_hit': True,
        'stop_hit': False,
        'accuracy': '✅ CORRECT'
    }
    exporter.add_backtest_result(sample_backtest)
    
    exporter.add_search('reliance', 'RELIANCE', 'Reliance Industries Ltd', 'DB_Stocks')
    
    stats = exporter.get_stats()
    print(f"📊 Current Stats:")
    print(f"   Live Signals: {stats['live_signals']}")
    print(f"   Backtest Results: {stats['backtest_results']}")
    print(f"   Searches: {stats['searches']}")
    
    print("\n📤 Exporting to Excel...")
    filepath = exporter.export_to_excel(auto_open=False)
    
    if filepath:
        print(f"\n✅ Test completed! File created at: {filepath}")
