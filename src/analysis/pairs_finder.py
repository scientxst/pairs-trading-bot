"""
Pairs Finder - Discovers cointegrated trading pairs
=================================================
"""

import pandas as pd
from dataclasses import dataclass
from typing import List
from ..data.data_manager import DataManager
from .statistical import StatisticalAnalyzer


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
                
                if current_combination % 10 == 0:
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
