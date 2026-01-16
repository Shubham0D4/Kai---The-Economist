"""
Delta - Sentiment Analysis Agent
Analyzes news sentiment, market narratives, and retail trends.
"""

import os
import sys
import json
import argparse
import time
import random
from typing import Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from coordinator.personas import RiskPersona, get_delta_system_instruction
from mcp_server.tools.news_stream import get_news_stream

# Import Multi-LLM Client
from coordinator.llm_client import MultiLLMClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DeltaAgent:
    """
    Delta - Sentiment Analysis Specialist
    
    Analyzes news sentiment, market narratives, and trends.
    Adjusts analysis based on risk persona (Zen vs Alpha).
    """
    
    def __init__(self, persona: RiskPersona = RiskPersona.ALPHA):
        """
        Initialize Delta agent.
        
        Args:
            persona: Risk persona to apply (Zen or Alpha)
        """
        self.persona = persona
        self.name = "Delta"
        self.role = "Sentiment Analysis Specialist"
        
        # Initialize hybrid model with system instruction
        system_instruction = get_delta_system_instruction(persona)
        self.model = MultiLLMClient(system_instruction=system_instruction)
    
    def analyze(self, ticker: str, days: int = 7, max_articles: int = 15) -> Dict:
        """
        Perform sentiment analysis on a ticker.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back for news
            max_articles: Maximum number of articles to analyze
            
        Returns:
            Analysis results with sentiment assessment
        """
        # Fetch news stream
        print(f"[Delta] Fetching news for {ticker} (last {days} days)...")
        news_data = get_news_stream(ticker, days=days, max_articles=max_articles)
        
        if not news_data.get("success"):
            return {
                "agent": self.name,
                "ticker": ticker,
                "persona": self.persona.value,
                "error": news_data.get("error", "Failed to fetch news data"),
                "analysis": None
            }
        
        articles = news_data.get("articles", [])
        if not articles:
            return {
                "agent": self.name,
                "ticker": ticker,
                "persona": self.persona.value,
                "error": f"No news articles found for {ticker}",
                "analysis": None
            }
        
        # Prepare analysis prompt
        articles_text = "\n\n".join([
            f"**Article {i+1}:**\n"
            f"Title: {article['title']}\n"
            f"Source: {article.get('source', 'Unknown')}\n"
            f"Published: {article.get('published_at', 'Unknown')}"
            for i, article in enumerate(articles[:max_articles])
        ])
        
        prompt = f"""
Analyze the sentiment and market narrative for {ticker} based on recent news.

Recent News Headlines ({len(articles)} articles from last {days} days):

{articles_text}

Based on your expertise in sentiment analysis and your current risk persona, provide:

1. **Overall Sentiment**: Classify as Positive, Negative, or Neutral with intensity (1-10)
2. **Dominant Narratives**: Identify key themes and stories driving sentiment
3. **Sentiment Trends**: Detect any shifts or momentum changes
4. **Retail/Market Vibe**: Assess the overall market "vibe" and retail sentiment
5. **Risk Signals**: Identify sentiment-based risks aligned with your risk persona
6. **Recommendation**: Provide your sentiment view (Bullish/Neutral/Bearish) with confidence level

Format your response as a structured analysis with clear sections.
"""
        
        # Generate analysis with fallback logic
        print(f"[Delta] Analyzing sentiment for {ticker} with {self.persona.value} persona...")
        
        try:
            response = self.model.generate_content(prompt)
            
            return {
                "agent": self.name,
                "role": self.role,
                "ticker": ticker,
                "persona": self.persona.value,
                "news_analyzed": {
                    "article_count": len(articles),
                    "time_range": f"Last {days} days",
                    "sources": news_data.get("sources", [])
                },
                "analysis": response.text,
                "articles_sample": articles[:5],
                "token_usage": {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "candidates_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                }
            }
        except Exception as e:
            return {
                "agent": self.name,
                "ticker": ticker,
                "persona": self.persona.value,
                "error": f"LLM Generation Failed: {str(e)}",
                "analysis": None
            }
    
    def get_agent_card(self) -> Dict:
        """
        Get A2A Agent Card for Delta by loading the agent.json file.
        """
        card_path = os.path.join(os.path.dirname(__file__), "agent.json")
        try:
            with open(card_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Delta] Error loading agent card: {e}")
            return {
                "name": "Delta",
                "role": "Sentiment Analysis Specialist",
                "persona_support": ["zen", "alpha", "balanced"]
            }


def main():
    """Main entry point for testing Delta agent."""
    parser = argparse.ArgumentParser(description="Delta - Sentiment Analysis Agent")
    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    parser.add_argument("--persona", type=str, default="alpha", choices=["zen", "alpha"], help="Risk persona")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back")
    parser.add_argument("--max-articles", type=int, default=15, help="Maximum articles to analyze")
    
    args = parser.parse_args()
    
    # Create agent with specified persona
    persona = RiskPersona.ZEN if args.persona == "zen" else RiskPersona.ALPHA
    delta = DeltaAgent(persona=persona)
    
    # Perform analysis
    result = delta.analyze(args.ticker, args.days, args.max_articles)
    
    # Print results
    print("\n" + "="*80)
    print(f"DELTA'S SENTIMENT ANALYSIS - {args.ticker.upper()}")
    print(f"Persona: {persona.value.upper()}")
    print("="*80 + "\n")
    
    if result.get("error"):
        print(f"ERROR: {result['error']}")
    else:
        print(result["analysis"])
        print("\n" + "="*80)
        print(f"News Analyzed: {result['news_analyzed']['article_count']} articles ({result['news_analyzed']['time_range']})")
        print(f"Sources: {', '.join(result['news_analyzed']['sources'][:5])}")
        print("="*80)


if __name__ == "__main__":
    main()
