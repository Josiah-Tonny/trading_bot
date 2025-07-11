import os
import requests
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

class AlphaVantageClient:
    """Client for interacting with the Alpha Vantage API."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: str = None):
        """Initialize the Alpha Vantage client.
        
        Args:
            api_key: Your Alpha Vantage API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided or set in ALPHA_VANTAGE_API_KEY environment variable")
        
        # Set up session with retry strategy
        self.session = requests.Session()
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make a request to the Alpha Vantage API.
        
        Args:
            params: Query parameters for the API request.
            
        Returns:
            The parsed JSON response.
            
        Raises:
            requests.exceptions.RequestException: If there's an error making the request.
            ValueError: If the API returns an error message.
        """
        # Add API key to params
        params['apikey'] = self.api_key
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for error messages in response
            if "Error Message" in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            if "Note" in data and "rate limit" in data["Note"].lower():
                raise ValueError("API rate limit exceeded")
                
            return data
            
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Request failed: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Failed to parse API response: {str(e)}")
    
    def get_ohlc_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Get OHLC (Open, High, Low, Close) data for a symbol.
        
        Args:
            symbol: The stock symbol to get data for (e.g., 'AAPL').
            timeframe: The timeframe for the data (e.g., '5m', '1h', '1d').
            
        Returns:
            A pandas DataFrame with OHLC data and volume, indexed by datetime.
            
        Raises:
            ValueError: If the timeframe is not supported or API returns an error.
        """
        # Map user-friendly timeframes to Alpha Vantage intervals
        tf_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "60min",
            "4h": "60min",  # Alpha Vantage only supports up to 60min for intraday
            "1d": "Daily"
        }
        
        # Validate timeframe
        if timeframe not in tf_map:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported timeframes: {', '.join(tf_map.keys())}")
        
        interval = tf_map[timeframe]
        
        # Set up API parameters based on interval
        params = {
            "function": "TIME_SERIES_INTRADAY" if interval != "Daily" else "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",
            "datatype": "json"
        }
        
        if interval != "Daily":
            params["interval"] = interval
        
        try:
            data = self._make_request(params)
            
            # Extract the time series data
            if interval == "Daily":
                time_series = data.get("Time Series (Daily)", {})
            else:
                time_series = data.get(f"Time Series ({interval})", {})
            
            if not time_series:
                raise ValueError("No time series data found in API response")
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Rename columns to standard format
            df = df.rename(columns={
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low',
                '4. close': 'close',
                '5. volume': 'volume'
            })
            
            # Convert index to datetime
            df.index = pd.to_datetime(df.index)
            
            # Convert data types
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col])
            df['volume'] = pd.to_numeric(df['volume'])
            
            # Sort by datetime (oldest first)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            raise ValueError(f"Failed to get OHLC data: {str(e)}")

# Create a singleton instance
alpha_vantage_client = AlphaVantageClient()
