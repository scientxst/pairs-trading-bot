"""
Statistical Analysis - Cointegration and statistical tests
========================================================
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
from typing import Tuple


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
    
    @staticmethod
    def calculate_spread(price1: pd.Series, price2: pd.Series, hedge_ratio: float) -> pd.Series:
        """Calculate the spread between two price series"""
        aligned_data = pd.concat([price1, price2], axis=1).dropna()
        y = aligned_data.iloc[:, 0]
        x = aligned_data.iloc[:, 1]
        
        spread = y - hedge_ratio * x
        spread.name = f"Spread_{price1.name}_{price2.name}"
        return spread
