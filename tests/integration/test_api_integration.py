import pytest
import pandas as pd
from datetime import datetime, timedelta
import os
import time

# This test file should be run with real API calls
pytestmark = pytest.mark.integration

# Skip tests if API keys are not available
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv("ALPHAVANTAGE_KEY"),
        os.getenv("FINNHUB_KEY"),
        os.getenv("NEWSAPI_KEY")
    ]),
    reason="Missing one or more API keys for integration tests"
)

class TestRealAPIIntegration:
    """Integration tests using real API calls."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Import here to avoid loading env vars during test collection
        from app.alpha_vantage_client import alpha_vantage_client
        from app.finnhub_client import finnhub_client
        from app.news_client import news_client
        
        self.av_client = alpha_vantage_client
        self.fh_client = finnhub_client
        self.news_client = news_client
        
        # Add delay between tests to avoid rate limiting
        time.sleep(1)
    
    def test_alpha_vantage_real_data(self):
        """Test Alpha Vantage with real API call."""
        # Test with a popular symbol and recent timeframe
        df = self.av_client.get_ohlc_data("AAPL", "1d")
        
        # Validate the response
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        print(f"\nAlpha Vantage Data for AAPL (1d):")
        print(f"Latest data point: {df.index[0]}")
        print(f"Latest close price: {df['close'].iloc[0]}")
        
        # Basic validation
        assert all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume'])
        assert df.index.is_monotonic_increasing
        
        # Check that the most recent date is recent (within last 7 days)
        most_recent = df.index.max()
        assert (datetime.now().date() - most_recent.date()) <= timedelta(days=7)
    
    def test_finnhub_real_data(self):
        """Test Finnhub with real API call."""
        # Test getting a stock quote
        quote = self.fh_client.get_quote("AAPL")
        
        # Print the quote for visibility
        print("\nFinnhub Quote for AAPL:")
        print(f"Current Price: {quote.get('c')}")
        print(f"Daily High: {quote.get('h')}")
        print(f"Daily Low: {quote.get('l')}")
        
        # Basic validation
        assert isinstance(quote, dict)
        assert 'c' in quote  # current price
        assert 'h' in quote  # high price
        assert 'l' in quote  # low price
        assert 'o' in quote  # open price
        assert 'pc' in quote  # previous close
    
    def test_newsapi_real_data(self):
        """Test NewsAPI with real API call."""
        # Test getting top headlines
        articles = self.news_client.get_top_headlines("business", page_size=2)
        
        # Print article info for visibility
        print("\nLatest Business Headlines:")
        for i, article in enumerate(articles[:2], 1):
            print(f"{i}. {article.get('title')} - {article.get('source', {}).get('name')}")
        
        # Basic validation
        assert isinstance(articles, list)
        if articles:  # API might return empty list if rate limited
            article = articles[0]
            assert 'title' in article
            assert 'url' in article
            assert 'publishedAt' in article
    
    def test_combined_workflow_analysis(self):
        """Test a complete trading analysis workflow using all APIs."""
        symbol = "MSFT"
        print(f"\nRunning combined analysis for {symbol}...")
        
        # 1. Get stock data
        print("\n1. Fetching stock data...")
        df = self.av_client.get_ohlc_data(symbol, "1d")
        latest_price = df['close'].iloc[0]
        print(f"Latest {symbol} price: {latest_price}")
        
        # 2. Get company profile
        print("\n2. Fetching company profile...")
        profile = self.fh_client.get_company_profile2(symbol)
        company_name = profile.get('name', 'N/A')
        print(f"Company: {company_name}")
        print(f"Industry: {profile.get('finnhubIndustry', 'N/A')}")
        
        # 3. Get news sentiment
        print("\n3. Analyzing news sentiment...")
        sentiment = self.fh_client.get_news_sentiment(symbol)
        print(f"Sentiment Score: {sentiment.get('sentiment', {}).get('score', 'N/A')}")
        print(f"Buzz: {sentiment.get('buzz', {}).get('buzz', 'N/A')}")
        
        # 4. Get recent news
        print("\n4. Fetching recent news...")
        articles = self.news_client.get_everything(
            query=f"{company_name} OR {symbol}",
            sort_by="publishedAt",
            page_size=3
        )
        
        print("\nRecent News Headlines:")
        for i, article in enumerate(articles[:3], 1):
            print(f"{i}. {article.get('title')} - {article.get('source', {}).get('name')}")
        
        # 5. Basic technical analysis
        print("\n5. Running technical analysis...")
        if len(df) > 20:  # Ensure we have enough data for SMA
            sma_20 = df['close'].rolling(window=20).mean().iloc[0]
            print(f"20-day SMA: {sma_20:.2f}")
            print("Current price is above 20-day SMA" if latest_price > sma_20 else "Current price is below 20-day SMA")
        
        # 6. Make a simple trading decision
        print("\n6. Trading Decision:")
        if len(df) > 1:
            price_change = ((df['close'].iloc[0] / df['close'].iloc[1]) - 1) * 100
            print(f"24h Price Change: {price_change:.2f}%")
            
            if price_change > 0:
                print("Bullish momentum detected")
            elif price_change < 0:
                print("Bearish momentum detected")
            else:
                print("Neutral momentum")
        
        print("\nAnalysis complete!")
        
        # Basic validations
        assert not df.empty
        assert isinstance(profile, dict)
        assert 'name' in profile
        assert 'ticker' in profile
        
        if articles:
            assert isinstance(articles, list)
            assert len(articles) > 0

# Only run these tests if explicitly requested
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (deselect with '-m "
        "not integration')",
    )
