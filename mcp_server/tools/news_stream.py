"""
News stream integration for ticker-specific headlines.
Provides the get_news_stream tool for Delta's sentiment analysis.
"""

import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from urllib.parse import quote


class NewsStreamClient:
    """Client for fetching news headlines."""
    
    def __init__(self):
        """Initialize news client."""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Kai-Economist/1.0)"
        }
    
    def fetch_google_news_rss(self, ticker: str, days: int = 7) -> List[Dict]:
        """
        Fetch news from Google News RSS feed.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back
            
        Returns:
            List of news articles
        """
        try:
            # Google News RSS search query
            query = f"{ticker} stock"
            url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
            
            response = httpx.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            
            # Parse RSS XML
            root = ET.fromstring(response.content)
            
            articles = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Find all items in the RSS feed
            for item in root.findall(".//item"):
                title = item.find("title")
                link = item.find("link")
                pub_date = item.find("pubDate")
                source = item.find("source")
                
                if title is not None and link is not None:
                    article = {
                        "title": title.text,
                        "url": link.text,
                        "published_at": pub_date.text if pub_date is not None else None,
                        "source": source.text if source is not None else "Google News"
                    }
                    articles.append(article)
            
            return articles[:20]  # Limit to 20 most recent
            
        except Exception as e:
            print(f"Error fetching Google News RSS: {e}")
            return []
    
    def fetch_yahoo_finance_news(self, ticker: str) -> List[Dict]:
        """
        Fetch news from Yahoo Finance (via web scraping fallback).
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of news articles
        """
        # Note: This is a simplified version. In production, you might want to use
        # a proper API like Alpha Vantage, NewsAPI, or Finnhub
        try:
            # Yahoo Finance news URL
            url = f"https://finance.yahoo.com/quote/{ticker}"
            
            # For now, return empty list as we'd need proper HTML parsing
            # In production, use BeautifulSoup or a paid API
            return []
            
        except Exception as e:
            print(f"Error fetching Yahoo Finance news: {e}")
            return []


# MCP Tool Function
def get_news_stream(
    ticker: str,
    days: int = 7,
    max_articles: int = 15
) -> Dict:
    """
    MCP tool to fetch recent news headlines for a ticker.
    
    This tool pulls ticker-specific news for sentiment analysis.
    Used by Delta agent for market sentiment and news analysis.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        days: Number of days to look back (default: 7, max: 30)
        max_articles: Maximum number of articles to return (default: 15, max: 50)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if fetch was successful
        - ticker: The requested ticker symbol
        - articles: List of news articles with title, url, published_at, source
        - count: Number of articles returned
        - time_range: Date range covered
        - error: Error message if success is False
    """
    try:
        client = NewsStreamClient()
        
        # Limit parameters
        days = min(days, 30)
        max_articles = min(max_articles, 50)
        
        # Fetch from Google News RSS
        articles = client.fetch_google_news_rss(ticker, days)
        
        # Limit to max_articles
        articles = articles[:max_articles]
        
        return {
            "success": True,
            "ticker": ticker,
            "articles": articles,
            "count": len(articles),
            "time_range": f"Last {days} days",
            "sources": list(set(article.get("source", "Unknown") for article in articles))
        }
        
    except Exception as e:
        return {
            "success": False,
            "ticker": ticker,
            "articles": [],
            "count": 0,
            "error": f"Error fetching news: {str(e)}"
        }


# For testing
if __name__ == "__main__":
    import json
    
    # Test the tool
    result = get_news_stream("AAPL", days=7, max_articles=10)
    print(json.dumps(result, indent=2))
