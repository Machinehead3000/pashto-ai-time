"""
Web Search Plugin - Enables web search capabilities for the AI.
"""

from typing import Dict, Any, List, Optional
import logging
import json
import requests
from urllib.parse import quote_plus
from datetime import datetime, timedelta
from ..plugins import AIPlugin

logger = logging.getLogger(__name__)

class WebSearchPlugin(AIPlugin):
    """Plugin for performing web searches."""
    
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        """Initialize the web search plugin.
        
        Args:
            api_key: Google Custom Search API key.
            search_engine_id: Google Custom Search Engine ID.
        """
        super().__init__(
            name="web_search",
            description="Enables web search capabilities",
            version="1.0.0"
        )
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(hours=1)
    
    def configure(self, api_key: str, search_engine_id: str) -> None:
        """Configure the plugin with API credentials.
        
        Args:
            api_key: Google Custom Search API key.
            search_engine_id: Google Custom Search Engine ID.
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.enabled = bool(api_key and search_engine_id)
    
    def _get_cached_result(self, query: str) -> Optional[Dict]:
        """Get a cached search result if it exists and is fresh.
        
        Args:
            query: Search query.
            
        Returns:
            Cached result or None if not found or expired.
        """
        cache_key = query.lower().strip()
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.utcnow() - cached['timestamp'] < self.cache_ttl:
                return cached['result']
        return None
    
    def _cache_result(self, query: str, result: Dict) -> None:
        """Cache a search result.
        
        Args:
            query: Search query.
            result: Search results to cache.
        """
        cache_key = query.lower().strip()
        self.cache[cache_key] = {
            'result': result,
            'timestamp': datetime.utcnow()
        }
    
    def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Perform a web search.
        
        Args:
            query: Search query.
            num_results: Number of results to return (max 10).
            
        Returns:
            Dictionary containing search results.
        """
        if not self.enabled or not self.api_key or not self.search_engine_id:
            return {
                'success': False,
                'error': 'Web search is not properly configured',
                'results': []
            }
        
        # Check cache first
        cached = self._get_cached_result(query)
        if cached:
            return {**cached, 'cached': True}
        
        try:
            # Prepare request
            url = (
                'https://www.googleapis.com/customsearch/v1'
                f'?key={self.api_key}'
                f'&cx={self.search_engine_id}'
                f'&q={quote_plus(query)}'
                f'&num={min(max(1, num_results), 10)}'  # Limit to 10 results max
            )
            
            # Make request
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Process results
            results = []
            for item in data.get('items', [])[:num_results]:
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'display_link': item.get('displayLink', '')
                })
            
            result = {
                'success': True,
                'query': query,
                'results': results,
                'total_results': int(data.get('searchInformation', {}).get('totalResults', 0)),
                'search_time': float(data.get('searchInformation', {}).get('searchTime', 0)),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Cache the result
            self._cache_result(query, result)
            return result
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'query': query,
                'results': []
            }
    
    def process(self, context: Any, input_data: Any, **kwargs) -> Any:
        """Process input with web search capabilities.
        
        Args:
            context: The current AI context.
            input_data: Input data to process.
            **kwargs: Additional parameters including 'search_query' and 'num_results'.
            
        Returns:
            Processed output with search results if applicable.
        """
        if not self.enabled or not input_data or not isinstance(input_data, str):
            return input_data
            
        # Check if this is a search request
        search_trigger = kwargs.get('search_trigger', 'search:')
        if not input_data.startswith(search_trigger):
            return input_data
            
        # Extract search query
        query = input_data[len(search_trigger):].strip()
        if not query:
            return "Please provide a search query after the search trigger."
            
        # Perform search
        num_results = int(kwargs.get('num_results', 3))
        result = self.search(query, num_results)
        
        if not result.get('success'):
            return f"Search failed: {result.get('error', 'Unknown error')}"
            
        # Format results
        formatted = [f"Web search results for '{query}':\n"]
        for i, item in enumerate(result['results'], 1):
            formatted.append(
                f"{i}. {item['title']}\n"
                f"   {item['link']}\n"
                f"   {item['snippet']}\n"
            )
            
        return "\n".join(formatted)

# Register the plugin
from ..plugins import get_plugin_manager

def register() -> bool:
    """Register the web search plugin."""
    return get_plugin_manager().register_plugin(WebSearchPlugin())

# Auto-register the plugin when imported
register()
