"""
Data Manager - Handles market data fetching and storage
====================================================
"""

import pandas as pd
import yfinance as yf
from typing import List, Dict
from datetime import datetime
import os


class DataManager:
    """Handles all data fetching, cleaning, and storage operations"""
    
    def __init__(self, start_date: str = "2019-01-01", end_date: str = "2024-01-01"):
        self.start_date = start_date
        self.end_date = end_date
        self.data = {}
    
    def fetch_stock_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical stock data for given symbols
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary with symbol as key and DataFrame as value
        """
        print(f"Fetching data for {len(symbols)} symbols...")
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=self.start_date, end=self.end_date)
                
                if not data.empty:
                    # Clean the data
                    data = data.dropna()
                    self.data[symbol] = data
                    print(f"✓ {symbol}: {len(data)} records")
                else:
                    print(f"✗ {symbol}: No data available")
                    
            except Exception as e:
                print(f"✗ {symbol}: Error fetching data - {e}")
        
        return self.data
    
    def get_price_series(self, symbol: str, price_type: str = 'Close') -> pd.Series:
        """Get price series for a specific symbol"""
        if symbol in self.data:
            return self.data[symbol][price_type]
        else:
            raise ValueError(f"Data for {symbol} not found. Please fetch data first.")
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols"""
        return list(self.data.keys())
    
    def save_data(self, filepath: str = "data/processed/market_data.pkl"):
        """Save fetched data to disk"""
        if self.data:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            pd.to_pickle(self.data, filepath)
            print(f"Data saved to {filepath}")
    
    def load_data(self, filepath: str = "data/processed/market_data.pkl"):
        """Load data from disk"""
        if os.path.exists(filepath):
            self.data = pd.read_pickle(filepath)
            print(f"Data loaded from {filepath}")
        else:
            print(f"File {filepath} not found")
