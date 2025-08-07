#main.py
"""
Pairs Trading

Comprehensive pairs trading bot that implements mean-reversion strategies
using cointegration analysis and statistical methods.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

@dataclass
class TradingPair:
    """Data class to represent a trading pair"""
    symbol1: str
    symbol2: str
    hedge_ratio: float
    cointegration_pvalue: float
    adf_pvalue: float
    spread_mean: float
    spread_std: float

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

class StatisticalAnalyzer:
    """Performs cointegration analysis and statistical tests"""
    
    @staticmethod
    def test_cointegration(price1: pd.Series, price2: pd.Series) -> Tuple[float, float, float]:
        """
        Test for cointegration between two price series
        
        Returns:
            (cointegration_pvalue, hedge_ratio, adf_pvalue)
        """
        # Align the series by dates
        aligned_data = pd.concat([price1, price2], axis=1).dropna()
        if len(aligned_data) < 30:
            return 1.0, 0.0, 1.0  # Not enough data
        
        y = aligned_data.iloc[:, 0]
        x = aligned_data.iloc[:, 1]
        
        # Perform cointegration test
        coint_stat, coint_pvalue, _ = coint(y, x)
        
        # Calculate hedge ratio using OLS regression
        model = OLS(y, x).fit()
        hedge_ratio = model.params[0]
        
        # Calculate spread and test for stationarity
        spread = y - hedge_ratio * x
        adf_stat, adf_pvalue, _, _, _, _ = adfuller(spread, autolag='AIC')
        
        return coint_pvalue, hedge_ratio, adf_pvalue
    
    @staticmethod
    def calculate_spread_stats(price1: pd.Series, price2: pd.Series, hedge_ratio: float) -> Tuple[float, float]:
        """Calculate spread mean and standard deviation"""
        aligned_data = pd.concat([price1, price2], axis=1).dropna()
        y = aligned_data.iloc[:, 0]
        x = aligned_data.iloc[:, 1]
        
        spread = y - hedge_ratio * x
        return spread.mean(), spread.std()

class PairsFinder:
    """Finds and validates trading pairs"""
    
    def __init__(self, data_manager: DataManager, 
                 cointegration_threshold: float = 0.05,
                 adf_threshold: float = 0.05):
        self.data_manager = data_manager
        self.cointegration_threshold = cointegration_threshold
        self.adf_threshold = adf_threshold
        self.analyzer = StatisticalAnalyzer()
    
    def find_pairs(self, symbols: List[str]) -> List[TradingPair]:
        """
        Find cointegrated pairs from a list of symbols
        
        Args:
            symbols: List of stock symbols to analyze
            
        Returns:
            List of valid TradingPair objects
        """
        valid_pairs = []
        total_combinations = len(symbols) * (len(symbols) - 1) // 2
        current_combination = 0
        
        print(f"Analyzing {total_combinations} possible pairs...")
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                current_combination += 1
                symbol1, symbol2 = symbols[i], symbols[j]
                
                if current_combination % 50 == 0:
                    print(f"Progress: {current_combination}/{total_combinations}")
                
                try:
                    price1 = self.data_manager.get_price_series(symbol1)
                    price2 = self.data_manager.get_price_series(symbol2)
                    
                    # Test cointegration
                    coint_pvalue, hedge_ratio, adf_pvalue = self.analyzer.test_cointegration(price1, price2)
                    
                    # Check if pair meets our criteria
                    if (coint_pvalue <= self.cointegration_threshold and 
                        adf_pvalue <= self.adf_threshold):
                        
                        # Calculate spread statistics
                        spread_mean, spread_std = self.analyzer.calculate_spread_stats(
                            price1, price2, hedge_ratio
                        )
                        
                        pair = TradingPair(
                            symbol1=symbol1,
                            symbol2=symbol2,
                            hedge_ratio=hedge_ratio,
                            cointegration_pvalue=coint_pvalue,
                            adf_pvalue=adf_pvalue,
                            spread_mean=spread_mean,
                            spread_std=spread_std
                        )
                        
                        valid_pairs.append(pair)
                        print(f"✓ Found pair: {symbol1}-{symbol2} (coint_p: {coint_pvalue:.4f}, adf_p: {adf_pvalue:.4f})")
                
                except Exception as e:
                    continue  # Skip this pair if there's an error
        
        print(f"\nFound {len(valid_pairs)} valid pairs out of {total_combinations} combinations")
        return valid_pairs

# Example usage and testing
if __name__ == "__main__":
    # Example: Find pairs among tech stocks
    tech_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 
        'META', 'NVDA', 'NFLX', 'ADBE', 'CRM'
    ]
    
    print("=== Pairs Trading Bot Demo ===")
    
    # Initialize data manager
    data_manager = DataManager(start_date="2020-01-01", end_date="2024-01-01")
    
    # Fetch data
    stock_data = data_manager.fetch_stock_data(tech_stocks)
    
    # Find pairs
    pairs_finder = PairsFinder(data_manager)
    trading_pairs = pairs_finder.find_pairs(list(stock_data.keys()))
    
    # Display results
    if trading_pairs:
        print("\n=== Top Trading Pairs ===")
        for i, pair in enumerate(trading_pairs[:3], 1):
            print(f"\n{i}. {pair.symbol1} - {pair.symbol2}")
            print(f"   Hedge Ratio: {pair.hedge_ratio:.4f}")
            print(f"   Cointegration p-value: {pair.cointegration_pvalue:.4f}")
            print(f"   ADF p-value: {pair.adf_pvalue:.4f}")
            print(f"   Spread Mean: {pair.spread_mean:.4f}")
            print(f"   Spread Std: {pair.spread_std:.4f}")
    else:
        print("No valid pairs found with current criteria.")
