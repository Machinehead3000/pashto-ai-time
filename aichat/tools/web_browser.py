"""
Web browsing tool for fetching and analyzing web content.
"""
import re
import json
import urllib.parse
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

@dataclass
class WebPage:
    """Represents a web page with its content and metadata."""
    url: str
    status_code: int
    content_type: str
    title: str
    text: str
    html: str
    links: List[Dict[str, str]]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the WebPage object to a dictionary."""
        return {
            'url': self.url,
            'status_code': self.status_code,
            'content_type': self.content_type,
            'title': self.title,
            'text': self.text[:10000] + ('...' if len(self.text) > 10000 else ''),
            'html_length': len(self.html),
            'links_count': len(self.links),
            'metadata': self.metadata
        }
    
    def get_summary(self, max_length: int = 1000) -> str:
        """Get a summary of the page content."""
        if not self.text:
            return "No text content available."
            
        # Clean up the text
        text = ' '.join(self.text.split())
        if len(text) <= max_length:
            return text
            
        # Try to find a good breaking point
        sentences = re.split(r'(?<=[.!?])\s+', text)
        summary = []
        length = 0
        
        for sentence in sentences:
            if length + len(sentence) > max_length:
                break
            summary.append(sentence)
            length += len(sentence)
            
        return ' '.join(summary) + ('...' if len(text) > max_length else '')


class WebBrowser:
    """
    A simple web browser for fetching and analyzing web content.
    """
    
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    def __init__(self, headers: Optional[Dict[str, str]] = None, 
                 timeout: int = 30, verify_ssl: bool = True):
        """
        Initialize the web browser.
        
        Args:
            headers: Custom headers to use for requests
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.headers = headers or self.DEFAULT_HEADERS
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch(self, url: str, method: str = 'GET', **kwargs) -> WebPage:
        """
        Fetch a web page.
        
        Args:
            url: URL of the page to fetch
            method: HTTP method to use (GET, POST, etc.)
            **kwargs: Additional arguments to pass to requests.request()
            
        Returns:
            WebPage object with the page content and metadata
        """
        try:
            # Ensure URL has a scheme
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # Make the request
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs
            )
            
            # Parse the response
            return self._parse_response(response)
            
        except requests.RequestException as e:
            # Handle request errors
            return WebPage(
                url=url,
                status_code=0,
                content_type='',
                title=f'Error: {str(e)}',
                text=f'Error fetching URL: {str(e)}',
                html='',
                links=[],
                metadata={'error': str(e), 'error_type': type(e).__name__}
            )
    
    def _parse_response(self, response: requests.Response) -> WebPage:
        """
        Parse a response into a WebPage object.
        
        Args:
            response: requests.Response object
            
        Returns:
            WebPage object with parsed content
        """
        url = response.url
        status_code = response.status_code
        content_type = response.headers.get('content-type', '').split(';')[0]
        
        # Initialize with empty values
        title = ''
        text = ''
        html = ''
        links = []
        metadata = {
            'headers': dict(response.headers),
            'encoding': response.encoding,
            'cookies': [dict(cookie) for cookie in response.cookies] if response.cookies else [],
            'redirects': [r.url for r in response.history],
            'final_url': response.url,
            'content_length': int(response.headers.get('content-length', 0)) if response.headers.get('content-length') else None,
        }
        
        # Only parse HTML content
        if 'text/html' in content_type or content_type == 'application/xhtml+xml':
            try:
                # Parse with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get title
                title_tag = soup.find('title')
                title = title_tag.string if title_tag else 'No title'
                
                # Get clean text (without scripts, styles, etc.)
                for script in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    script.decompose()
                text = soup.get_text(separator='\n', strip=True)
                
                # Get all links
                links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    # Resolve relative URLs
                    full_url = urllib.parse.urljoin(url, href)
                    links.append({
                        'text': a.get_text(strip=True),
                        'url': full_url,
                        'is_external': not full_url.startswith(url)
                    })
                
                # Extract metadata
                metadata.update(self._extract_metadata(soup, url))
                
                # Get HTML (truncated if too large)
                html = str(soup)
                
            except Exception as e:
                # If parsing fails, fall back to raw text
                text = f"Error parsing HTML: {str(e)}\n\n{response.text[:5000]}"
                html = response.text
        else:
            # For non-HTML content, just use the raw text
            text = response.text
            html = response.text
            title = f'[{content_type}] {url}'
        
        return WebPage(
            url=url,
            status_code=status_code,
            content_type=content_type,
            title=title,
            text=text,
            html=html,
            links=links,
            metadata=metadata
        )
    
    def _extract_metadata(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """
        Extract metadata from the HTML document.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'meta': {},
            'open_graph': {},
            'twitter': {},
            'json_ld': [],
            'headings': {},
            'images': []
        }
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property', '').replace('og:', '').replace('twitter:', '')
            content = meta.get('content', '')
            
            if name and content:
                if name.startswith('og:'):
                    metadata['open_graph'][name[3:]] = content
                elif name.startswith('twitter:'):
                    metadata['twitter'][name[8:]] = content
                else:
                    metadata['meta'][name.lower()] = content
        
        # JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                json_data = json.loads(script.string)
                metadata['json_ld'].append(json_data)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Headings
        for level in range(1, 7):
            headings = [h.get_text(strip=True) for h in soup.find_all(f'h{level}')]
            if headings:
                metadata['headings'][f'h{level}'] = headings
        
        # Images
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                full_url = urllib.parse.urljoin(base_url, src)
                metadata['images'].append({
                    'url': full_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width'),
                    'height': img.get('height'),
                })
        
        return metadata
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform a web search (placeholder - would need an API key for a real search engine).
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, url, and snippet
        """
        # This is a placeholder that would use a search engine API
        # In a real implementation, you would use something like:
        # - Google Custom Search API
        # - SerpAPI
        # - DuckDuckGo API
        # - etc.
        
        return [{
            'title': f'Search result for: {query} (search not implemented)',
            'url': f'https://example.com/search?q={urllib.parse.quote(query)}',
            'snippet': 'This is a placeholder. In a real implementation, this would show search results.'
        }]


def fetch_webpage(url: str, **kwargs) -> Dict[str, Any]:
    """
    Fetch and analyze a web page.
    
    Args:
        url: URL of the page to fetch
        **kwargs: Additional arguments to pass to WebBrowser.fetch()
        
    Returns:
        Dictionary with page analysis
    """
    browser = WebBrowser()
    page = browser.fetch(url, **kwargs)
    return page.to_dict()


def search_web(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Perform a web search.
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        List of search results
    """
    browser = WebBrowser()
    return browser.search(query, num_results)
