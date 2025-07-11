import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

class NewsAPIClient:
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWSAPI_KEY")
        if not self.api_key:
            raise ValueError("NewsAPI key not provided")
            
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the NewsAPI."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"X-Api-Key": self.api_key}
        
        try:
            response = self.session.get(
                url, 
                headers=headers, 
                params=params or {},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"NewsAPI request failed: {str(e)}"
            if hasattr(e.response, 'json') and e.response.json().get('message'):
                error_msg += f" - {e.response.json()['message']}"
            raise Exception(error_msg)
    
    def get_top_headlines(
        self, 
        query: Optional[str] = None,
        category: Optional[str] = None,
        country: str = 'us',
        page_size: int = 10
    ) -> List[Dict]:
        """Get top headlines."""
        params = {
            'country': country,
            'pageSize': page_size
        }
        if query:
            params['q'] = query
        if category:
            params['category'] = category
            
        data = self._make_request("top-headlines", params)
        return data.get('articles', [])
    
    def get_everything(
        self, 
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        sort_by: str = 'publishedAt',
        page_size: int = 10
    ) -> List[Dict]:
        """Search all articles."""
        if not from_date:
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
            
        params = {
            'q': query,
            'from': from_date,
            'to': to_date,
            'sortBy': sort_by,
            'pageSize': page_size,
            'language': 'en'
        }
        
        data = self._make_request("everything", params)
        return data.get('articles', [])

# Create a singleton instance
news_client = NewsAPIClient()
