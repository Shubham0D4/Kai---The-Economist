"""
SEC EDGAR API integration for fetching company filings.
Provides the fetch_filing_data tool for Charlie's fundamental analysis.
"""

import httpx
from typing import Dict, List, Optional
from datetime import datetime
import json


class SECFilingsClient:
    """Client for SEC EDGAR API."""
    
    BASE_URL = "https://data.sec.gov"
    
    def __init__(self, user_agent: str = "Kai-Economist contact@example.com"):
        """
        Initialize SEC client.
        
        Args:
            user_agent: Required by SEC EDGAR API (must include contact info)
        """
        self.user_agent = user_agent
        self.headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate"
        }
    
    def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get CIK (Central Index Key) for a ticker symbol.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            CIK string with leading zeros, or None if not found
        """
        try:
            # SEC maintains a ticker to CIK mapping - using correct endpoint
            url = "https://www.sec.gov/files/company_tickers.json"
            response = httpx.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            ticker_upper = ticker.upper()
            
            # Search for ticker in the mapping
            for entry in data.values():
                if entry.get("ticker") == ticker_upper:
                    # CIK needs to be 10 digits with leading zeros
                    cik = str(entry["cik_str"]).zfill(10)
                    return cik
            
            return None
            
        except Exception as e:
            print(f"Error fetching CIK for {ticker}: {e}")
            return None
    
    def fetch_company_filings(
        self, 
        ticker: str, 
        filing_type: str = "10-K",
        count: int = 5
    ) -> Dict:
        """
        Fetch recent filings for a company.
        
        Args:
            ticker: Stock ticker symbol
            filing_type: Type of filing (10-K, 10-Q, 8-K, etc.)
            count: Number of recent filings to return
            
        Returns:
            Dictionary with filing metadata and links
        """
        try:
            # Get CIK for the ticker
            cik = self.get_company_cik(ticker)
            if not cik:
                return {
                    "success": False,
                    "error": f"Could not find CIK for ticker {ticker}",
                    "ticker": ticker,
                    "filings": []
                }
            
            # Fetch company submissions
            url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
            response = httpx.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract recent filings of the specified type
            recent_filings = data.get("filings", {}).get("recent", {})
            
            filings = []
            forms = recent_filings.get("form", [])
            filing_dates = recent_filings.get("filingDate", [])
            accession_numbers = recent_filings.get("accessionNumber", [])
            primary_documents = recent_filings.get("primaryDocument", [])
            
            for i, form in enumerate(forms):
                if form == filing_type and len(filings) < count:
                    accession = accession_numbers[i].replace("-", "")
                    filing_url = f"{self.BASE_URL}/Archives/edgar/data/{cik}/{accession}/{primary_documents[i]}"
                    
                    filings.append({
                        "form": form,
                        "filing_date": filing_dates[i],
                        "accession_number": accession_numbers[i],
                        "document_url": filing_url,
                        "description": f"{form} filed on {filing_dates[i]}"
                    })
            
            return {
                "success": True,
                "ticker": ticker,
                "cik": cik,
                "company_name": data.get("name", ""),
                "filing_type": filing_type,
                "filings": filings,
                "count": len(filings)
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "ticker": ticker,
                "filings": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error fetching filings: {str(e)}",
                "ticker": ticker,
                "filings": []
            }


# MCP Tool Function
def fetch_filing_data(
    ticker: str,
    filing_type: str = "10-K",
    count: int = 3
) -> Dict:
    """
    MCP tool to fetch SEC filing data for a company.
    
    This tool pulls 10-K, 10-Q, and other SEC filings for fundamental analysis.
    Used by Charlie agent for deep fundamental research.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        filing_type: Type of SEC filing (default: '10-K')
                    Options: '10-K' (annual), '10-Q' (quarterly), '8-K' (current events)
        count: Number of recent filings to retrieve (default: 3, max: 10)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if fetch was successful
        - ticker: The requested ticker symbol
        - company_name: Official company name
        - filing_type: Type of filing requested
        - filings: List of filing objects with metadata and URLs
        - error: Error message if success is False
    """
    client = SECFilingsClient()
    return client.fetch_company_filings(ticker, filing_type, min(count, 10))


# For testing
if __name__ == "__main__":
    # Test the tool
    result = fetch_filing_data("AAPL", "10-K", 2)
    print(json.dumps(result, indent=2))
