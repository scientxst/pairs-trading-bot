"""
Main Streamlit Application for Pairs Trading Bot
================================================
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Fix import paths for both local and Streamlit Cloud
import sys
from pathlib import Path

# Get the project root directory
file_path = Path(__file__).resolve()
src_path = file_path.parent.parent  # Goes up to src/
root_path = src_path.parent  # Goes up to project root

# Add both to path
sys.path.insert(0, str(root_path))
sys.path.insert(0, str(src_path))

# Now import our modules
try:
    from src.data.data_manager import DataManager
    from src.analysis.pairs_finder import PairsFinder, TradingPair
    from src.analysis.statistical import StatisticalAnalyzer
except ImportError:
    try:
        from data.data_manager import DataManager
        from analysis.pairs_finder import PairsFinder, TradingPair
        from analysis.statistical import StatisticalAnalyzer
    except ImportError as e:
        st.error(f"Critical import error: {e}")
        st.error("Please check the project structure")
        st.stop()

# Import plotly
try:
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    st.error("Plotly not installed. Please run: pip install plotly")
    st.stop()


def initialize_session_state():
    """Initialize session state variables"""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = None
    if 'trading_pairs' not in st.session_state:
        st.session_state.trading_pairs = []
    if 'selected_pair' not in st.session_state:
        st.session_state.selected_pair = None


def sidebar_navigation():
    """Create sidebar navigation"""
    st.sidebar.title("🎯 Pairs Trading Bot")
    st.sidebar.markdown("---")
    
    pages = {
        "📊 Data Management": "data",
        "🔍 Pairs Discovery": "pairs",
        "📈 Analysis": "analysis",
        "⚙️ Strategy Config": "strategy", 
        "🧪 Backtesting": "backtest"
    }
    
    selected_page = st.sidebar.selectbox(
        "Navigate to:",
        list(pages.keys()),
        key="page_selector"
    )
    
    return pages[selected_page]


def show_data_management():
    """Data Management Page"""
    st.header("📊 Data Management")
    st.markdown("Fetch and manage market data for analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Stock Selection")
        
        # Predefined stock lists
        stock_lists = {
            "Tech Stocks": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM'],
            "Financial": ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF'],
            "Healthcare": ['JNJ', 'PFE', 'UNH', 'MRK', 'ABT', 'TMO', 'DHR', 'BMY', 'AMGN', 'GILD'],
            "Energy": ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'OXY', 'KMI']
        }
        
        selected_list = st.selectbox("Choose a stock list:", list(stock_lists.keys()))
        symbols = st.multiselect(
            "Select stocks:",
            stock_lists[selected_list],
            default=stock_lists[selected_list][:5]
        )
        
        # Custom symbols
        custom_symbols = st.text_input(
            "Or add custom symbols (comma-separated):",
            placeholder="AAPL, MSFT, GOOGL"
        )
        
        if custom_symbols:
            symbols.extend([s.strip().upper() for s in custom_symbols.split(',')])
    
    with col2:
        st.subheader("Date Range")
        end_date = st.date_input("End Date", value=datetime.now().date())
        start_date = st.date_input(
            "Start Date", 
            value=end_date - timedelta(days=365*4)
        )
    
    # Fetch Data Button
    if st.button("🔄 Fetch Market Data", type="primary"):
        if symbols:
            with st.spinner("Fetching market data..."):
                try:
                    data_manager = DataManager(
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d')
                    )
                    
                    # Fetch data
                    stock_data = data_manager.fetch_stock_data(symbols)
                    st.session_state.data_manager = data_manager
                    
                    # Show success message
                    st.success(f"✅ Successfully fetched data for {len(stock_data)} stocks!")
                    
                    # Display data summary
                    if stock_data:
                        st.subheader("Data Summary")
                        summary_data = []
                        for symbol, data in stock_data.items():
                            summary_data.append({
                                'Symbol': symbol,
                                'Records': len(data),
                                'Start Date': data.index[0].strftime('%Y-%m-%d'),
                                'End Date': data.index[-1].strftime('%Y-%m-%d'),
                                'Current Price': f"${data['Close'].iloc[-1]:.2f}"
                            })
                        
                        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
                        
                except Exception as e:
                    st.error(f"❌ Error fetching data: {str(e)}")
        else:
            st.warning("⚠️ Please select at least one stock symbol")


def show_pairs_discovery():
    """Pairs Discovery Page"""
    st.header("🔍 Pairs Discovery")
    
    if not st.session_state.data_manager:
        st.warning("⚠️ Please fetch market data first from the Data Management page")
        return
    
    st.markdown("Discover statistically cointegrated pairs for trading")
    
    # Parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cointegration_threshold = st.slider(
            "Cointegration p-value threshold:",
            0.01, 0.10, 0.05, 0.01,
            help="Lower values = stricter cointegration requirement"
        )
    
    with col2:
        adf_threshold = st.slider(
            "ADF p-value threshold:",
            0.01, 0.10, 0.05, 0.01,
            help="Lower values = stricter stationarity requirement"
        )
    
    with col3:
        min_observations = st.number_input(
            "Minimum observations:",
            min_value=50, max_value=1000, value=252,
            help="Minimum number of data points required"
        )
    
    # Finding Pairs Button
    if st.button("🔍 Find Trading Pairs", type="primary"):
        with st.spinner("Analyzing pairs... This may take a few minutes..."):
            try:
                pairs_finder = PairsFinder(
                    st.session_state.data_manager,
                    cointegration_threshold=cointegration_threshold,
                    adf_threshold=adf_threshold
                )
                
                symbols = st.session_state.data_manager.get_available_symbols()
                trading_pairs = pairs_finder.find_pairs(symbols)
                st.session_state.trading_pairs = trading_pairs
                
                if trading_pairs:
                    st.success(f"✅ Found {len(trading_pairs)} valid trading pairs!")
                    
                    # Display pairs table
                    pairs_data = []
                    for pair in trading_pairs:
                        pairs_data.append({
                            'Pair': f"{pair.symbol1} - {pair.symbol2}",
                            'Hedge Ratio': f"{pair.hedge_ratio:.4f}",
                            'Cointegration p-value': f"{pair.cointegration_pvalue:.4f}",
                            'ADF p-value': f"{pair.adf_pvalue:.4f}",
                            'Spread Std': f"{pair.spread_std:.2f}"
                        })
                    
                    st.dataframe(pd.DataFrame(pairs_data), use_container_width=True)
                else:
                    st.warning("⚠️ No pairs found with current criteria. Try relaxing the thresholds.")
                    
            except Exception as e:
                st.error(f"❌ Error finding pairs: {str(e)}")


def show_analysis():
    """Analysis Page"""
    st.header("📈 Pairs Analysis")
    st.info("�� Analysis functionality coming soon!")


def show_strategy_config():
    """Strategy Configuration Page"""
    st.header("⚙️ Strategy Configuration")
    st.info("🚧 Strategy configuration coming soon!")


def show_backtesting():
    """Backtesting Page"""
    st.header("🧪 Backtesting")
    st.info("🚧 Backtesting functionality coming soon!")


def run_app():
    """Main application runner"""
    st.write("Debug: run_app() called")  # Debug line
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar navigation
    current_page = sidebar_navigation()
    
    # Main content area
    if current_page == "data":
        show_data_management()
    elif current_page == "pairs":
        show_pairs_discovery()
    elif current_page == "analysis":
        show_analysis()
    elif current_page == "strategy":
        show_strategy_config()
    elif current_page == "backtest":
        show_backtesting()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("🤖 **Pairs Trading Bot v1.0**")


# Run directly if this file is executed
if __name__ == "__main__":
    run_app()
