import pandas as pd
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'yfinance', '-q'])
    import yfinance as yf

# Import configuration
try:
    from config import DEFAULT_PERIOD, DEFAULT_INTERVAL, NSE_SUFFIX, BSE_SUFFIX
except ImportError:
    DEFAULT_PERIOD = "1y"
    DEFAULT_INTERVAL = "1d"
    NSE_SUFFIX = ".NS"
    BSE_SUFFIX = ".BO"


class DataFetcher:
    def __init__(self):
        self.cache = {}
        self.default_period = DEFAULT_PERIOD
        self.default_interval = DEFAULT_INTERVAL
        self.nse_suffix = NSE_SUFFIX
        self.bse_suffix = BSE_SUFFIX

    def get_yahoo_symbol(self, symbol):
        """Convert NSE/BSE symbol to Yahoo Finance format"""
        symbol = symbol.strip().upper()
        
        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            return symbol
        
        return f"{symbol}{self.nse_suffix}"

    def fetch_data(self, symbol, period=None, interval=None):
        """
        Fetch historical data for a stock
        
        Parameters:
        - symbol: Stock symbol (e.g., 'RELIANCE', 'HDFCBANK')
        - period: Data period ('1mo', '3mo', '6mo', '1y', '2y', '5y')
        - interval: Data interval ('1d', '1wk', '1mo')
        
        Returns:
        - DataFrame with OHLCV data or None if failed
        """
        if period is None:
            period = self.default_period
        if interval is None:
            interval = self.default_interval
            
        yahoo_symbol = self.get_yahoo_symbol(symbol)
        cache_key = f"{yahoo_symbol}_{period}_{interval}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            print(f"📡 Fetching data for {symbol}...")
            
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                yahoo_symbol_bse = f"{symbol}{self.bse_suffix}"
                ticker = yf.Ticker(yahoo_symbol_bse)
                df = ticker.history(period=period, interval=interval)
                
                if df.empty:
                    print(f"❌ No data found for {symbol}")
                    return None

            df = df.reset_index()
            df.columns = [col if col != 'Date' else 'Date' for col in df.columns]
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
            elif 'Datetime' in df.columns:
                df['Date'] = pd.to_datetime(df['Datetime']).dt.tz_localize(None)
                df = df.drop('Datetime', axis=1)

            required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = df[[col for col in required_cols if col in df.columns]]

            self.cache[cache_key] = df

            print(f"✅ Fetched {len(df)} days of data for {symbol}")
            return df

        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")
            return None

    def fetch_data_by_date_range(self, symbol, start_date, end_date=None):
        """
        Fetch data for specific date range
        
        Parameters:
        - symbol: Stock symbol
        - start_date: Start date (string 'YYYY-MM-DD' or datetime)
        - end_date: End date (string 'YYYY-MM-DD' or datetime), defaults to today
        
        Returns:
        - DataFrame with OHLCV data
        """
        yahoo_symbol = self.get_yahoo_symbol(symbol)

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        try:
            print(f"📡 Fetching data for {symbol} from {start_date.date()} to {end_date.date()}...")
            
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                yahoo_symbol_bse = f"{symbol}{self.bse_suffix}"
                ticker = yf.Ticker(yahoo_symbol_bse)
                df = ticker.history(start=start_date, end=end_date)
                
                if df.empty:
                    print(f"❌ No data found for {symbol} in given date range")
                    return None

            df = df.reset_index()
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
            elif 'Datetime' in df.columns:
                df['Date'] = pd.to_datetime(df['Datetime']).dt.tz_localize(None)
                df = df.drop('Datetime', axis=1)

            required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = df[[col for col in required_cols if col in df.columns]]

            print(f"✅ Fetched {len(df)} days of data")
            return df

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None

    def get_current_price(self, symbol):
        """Get current/latest price for a stock"""
        yahoo_symbol = self.get_yahoo_symbol(symbol)
        
        try:
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            
            if price is None:
                df = ticker.history(period='5d')
                if not df.empty:
                    price = df['Close'].iloc[-1]
            
            return price
            
        except Exception as e:
            print(f"❌ Error getting current price: {e}")
            return None

    def get_stock_info(self, symbol):
        """Get basic stock information"""
        yahoo_symbol = self.get_yahoo_symbol(symbol)
        
        try:
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
            }
            
        except Exception as e:
            print(f"❌ Error getting stock info: {e}")
            return None

    def clear_cache(self):
        """Clear the data cache"""
        self.cache = {}
        print("✅ Cache cleared")


# Test the module
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   TESTING DATA FETCHER MODULE")
    print("=" * 50 + "\n")

    fetcher = DataFetcher()

    test_symbol = "RELIANCE"
    
    df = fetcher.fetch_data(test_symbol, period='3mo')
    
    if df is not None:
        print(f"\n📊 Data for {test_symbol}:")
        print(f"   Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
        print(f"   Total records: {len(df)}")
        print(f"\n   Last 5 days:")
        print(df.tail().to_string(index=False))
        
        price = fetcher.get_current_price(test_symbol)
        print(f"\n   Current Price: ₹{price:.2f}" if price else "\n   Current Price: N/A")

    print("\n" + "-" * 50)
    test_symbol2 = "HDFCBANK"
    df2 = fetcher.fetch_data(test_symbol2, period='1mo')
    
    if df2 is not None:
        print(f"\n📊 Data for {test_symbol2}:")
        print(df2.tail().to_string(index=False))
