import pandas as pd
from difflib import SequenceMatcher
import os

# Import configuration
try:
    from config import EXCEL_FILE_PATH
except ImportError:
    EXCEL_FILE_PATH = "Indian_Stocks_Complete_Market_Cap_Classification.xlsx"


class StockLoader:
    def __init__(self, excel_path=None):
        self.excel_path = excel_path if excel_path else EXCEL_FILE_PATH
        self.all_stocks = []
        self.db_stocks = []
        self.large_cap = []
        self.mid_cap = []
        self.small_cap = []
        self.load_excel()

    def load_excel(self):
        """Load all stocks from Excel file"""
        if not os.path.exists(self.excel_path):
            print(f"❌ Excel file not found: {self.excel_path}")
            return

        try:
            # Load DB Stocks (your preferred)
            db_df = pd.read_excel(self.excel_path, sheet_name='DB_Stocks')
            for _, row in db_df.iterrows():
                if pd.notna(row['Symbol']) and isinstance(row['Symbol'], str):
                    self.db_stocks.append({
                        'symbol': row['Symbol'].strip().upper(),
                        'name': row['Symbol'].strip(),
                        'category': 'DB_Stocks',
                        'sector': 'Your Preferred',
                        'market_cap': 'N/A'
                    })

            # Load Large Cap
            large_df = pd.read_excel(self.excel_path, sheet_name='Large Cap (100)')
            for _, row in large_df.iterrows():
                if pd.notna(row.get('Symbol')) and isinstance(row.get('Symbol'), str):
                    self.large_cap.append({
                        'symbol': str(row['Symbol']).strip().upper(),
                        'name': str(row['Name']).strip() if pd.notna(row.get('Name')) else '',
                        'category': 'Large Cap',
                        'sector': str(row['Sector/Industry']) if pd.notna(row.get('Sector/Industry')) else '',
                        'market_cap': str(row['Market Cap (Approx)']) if pd.notna(row.get('Market Cap (Approx)')) else ''
                    })

            # Load Mid Cap
            mid_df = pd.read_excel(self.excel_path, sheet_name='Mid Cap (150)')
            for _, row in mid_df.iterrows():
                if pd.notna(row.get('Symbol')) and isinstance(row.get('Symbol'), str):
                    self.mid_cap.append({
                        'symbol': str(row['Symbol']).strip().upper(),
                        'name': str(row['Name']).strip() if pd.notna(row.get('Name')) else '',
                        'category': 'Mid Cap',
                        'sector': str(row['Sector/Industry']) if pd.notna(row.get('Sector/Industry')) else '',
                        'market_cap': str(row['Market Cap (Approx)']) if pd.notna(row.get('Market Cap (Approx)')) else ''
                    })

            # Load Small Cap
            small_df = pd.read_excel(self.excel_path, sheet_name='Small Cap (250)')
            for _, row in small_df.iterrows():
                if pd.notna(row.get('Symbol')) and isinstance(row.get('Symbol'), str):
                    self.small_cap.append({
                        'symbol': str(row['Symbol']).strip().upper(),
                        'name': str(row['Name']).strip() if pd.notna(row.get('Name')) else '',
                        'category': 'Small Cap',
                        'sector': str(row['Sector/Industry']) if pd.notna(row.get('Sector/Industry')) else '',
                        'market_cap': str(row['Market Cap (Approx)']) if pd.notna(row.get('Market Cap (Approx)')) else ''
                    })

            # Combine all stocks (DB stocks first for priority)
            self.all_stocks = self.db_stocks + self.large_cap + self.mid_cap + self.small_cap

            print(f"✅ Loaded {len(self.db_stocks)} DB Stocks")
            print(f"✅ Loaded {len(self.large_cap)} Large Cap Stocks")
            print(f"✅ Loaded {len(self.mid_cap)} Mid Cap Stocks")
            print(f"✅ Loaded {len(self.small_cap)} Small Cap Stocks")
            print(f"✅ Total: {len(self.all_stocks)} stocks available")

        except Exception as e:
            print(f"❌ Error loading Excel: {e}")

    def similarity_score(self, str1, str2):
        """Calculate similarity between two strings"""
        str1 = str1.lower()
        str2 = str2.lower()
        return SequenceMatcher(None, str1, str2).ratio()

    def search_stock(self, query):
        """
        Smart search for stocks
        - Works with symbol, name, or partial text
        - Returns list of matching stocks sorted by relevance
        """
        query = query.strip()
        if not query:
            return []

        query_upper = query.upper()
        query_lower = query.lower()
        results = []

        for stock in self.all_stocks:
            symbol = stock['symbol']
            name = stock['name'].lower()
            score = 0

            # Exact symbol match (highest priority)
            if symbol == query_upper:
                score = 100

            # Symbol starts with query
            elif symbol.startswith(query_upper):
                score = 90

            # Symbol contains query
            elif query_upper in symbol:
                score = 80

            # Exact name match
            elif name == query_lower:
                score = 85

            # Name starts with query
            elif name.startswith(query_lower):
                score = 75

            # Name contains query
            elif query_lower in name:
                score = 70

            # Fuzzy match on symbol
            else:
                sym_similarity = self.similarity_score(query, symbol)
                name_similarity = self.similarity_score(query, name)
                best_similarity = max(sym_similarity, name_similarity)
                
                if best_similarity > 0.5:
                    score = best_similarity * 60

            # Boost score for DB stocks (user's preferred)
            if score > 0 and stock['category'] == 'DB_Stocks':
                score += 5

            if score > 0:
                results.append({
                    'stock': stock,
                    'score': score
                })

        # Sort by score (highest first) and remove duplicates
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Remove duplicate symbols, keep highest scored
        seen_symbols = set()
        unique_results = []
        for r in results:
            if r['stock']['symbol'] not in seen_symbols:
                seen_symbols.add(r['stock']['symbol'])
                unique_results.append(r['stock'])

        return unique_results[:10]  # Return top 10 matches

    def get_stock_info(self, symbol):
        """Get full info for a specific stock symbol"""
        symbol = symbol.strip().upper()
        for stock in self.all_stocks:
            if stock['symbol'] == symbol:
                return stock
        # If not found in Excel, return basic info
        return {
            'symbol': symbol,
            'name': symbol,
            'category': 'Manual Entry',
            'sector': 'Unknown',
            'market_cap': 'N/A'
        }

    def display_search_results(self, results):
        """Display search results in a formatted way"""
        if not results:
            print("❌ No stocks found matching your search.")
            return None

        print("\n" + "=" * 70)
        print("  SEARCH RESULTS")
        print("=" * 70)
        print(f"{'#':<4} {'Symbol':<15} {'Name':<30} {'Category':<12}")
        print("-" * 70)

        for i, stock in enumerate(results, 1):
            name = stock['name'][:28] + '..' if len(stock['name']) > 30 else stock['name']
            print(f"{i:<4} {stock['symbol']:<15} {name:<30} {stock['category']:<12}")

        print("-" * 70)
        return results


# Test the module
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   TESTING STOCK LOADER MODULE")
    print("=" * 50 + "\n")

    loader = StockLoader()

    # Test searches
    test_queries = ["hdfc", "reliance", "tata", "sbi", "bajaj", "itc"]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        results = loader.search_stock(query)
        loader.display_search_results(results)
