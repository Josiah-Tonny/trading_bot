import os
import requests
from typing import Dict, List, Optional, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class FinnhubClient:
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FINNHUB_KEY")
        if not self.api_key:
            raise ValueError("Finnhub API key not provided")
            
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the Finnhub API."""
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["token"] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Finnhub API request failed: {str(e)}")
    
    def get_quote(self, symbol: str) -> Dict[str, float]:
        """Get real-time quote for a symbol."""
        return self._make_request(f"quote?symbol={symbol}")
    
    def get_company_profile(self, symbol: str) -> Dict:
        """Get company profile."""
        return self._make_request(f"stock/profile2?symbol={symbol}")
    
    def get_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment for a company."""
        return self._make_request(f"news-sentiment?symbol={symbol}")
    
    def get_news(self, symbol: str, _from: Optional[str] = None, to: Optional[str] = None) -> List[Dict]:
        """Get company news."""
        if _from is None:
            _from = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
        if to is None:
            to = datetime.now().strftime('%Y-%m-%d')
            
        return self._make_request("company-news", {
            "symbol": symbol,
            "from": _from,
            "to": to
        })

# Create a singleton instance
finnhub_client = FinnhubClient()
