"""
FastMCP server entry point for Kai - Economist data backbone.
Exposes tools for SEC filings, news streams, and financial calculations.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from typing import Any

# Import tool functions
from tools.sec_filings import fetch_filing_data
from tools.news_stream import get_news_stream
from tools.finance_math import calculate_valuation_metrics, calculate_risk_metrics
from cache.semantic_cache import SemanticCache


# Initialize MCP server
app = Server("kai-data-backbone")

# Initialize Semantic Cache
cache = SemanticCache()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools in the MCP server.
    """
    return [
        Tool(
            name="fetch_filing_data",
            description=(
                "Fetch SEC filing data (10-K, 10-Q, 8-K) for a company ticker. "
                "Returns recent filings with metadata and document URLs. "
                "Used by the Fundamental Analysis Specialist (Charlie) for deep business research."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT')"
                    },
                    "filing_type": {
                        "type": "string",
                        "description": "Type of SEC filing",
                        "enum": ["10-K", "10-Q", "8-K"],
                        "default": "10-K"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of recent filings to retrieve (max: 10)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["ticker"]
            }
        ),
        Tool(
            name="get_news_stream",
            description=(
                "Fetch recent news headlines for a stock ticker. "
                "Returns articles with titles, URLs, publication dates, and sources. "
                "Used by the Sentiment Analysis Specialist (Delta) to gauge market narratives."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT')"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (max: 30)",
                        "default": 7,
                        "minimum": 1,
                        "maximum": 30
                    },
                    "max_articles": {
                        "type": "integer",
                        "description": "Maximum number of articles to return (max: 50)",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["ticker"]
            }
        ),
        Tool(
            name="calculate_valuation_metrics",
            description=(
                "Calculate comprehensive valuation metrics including PE ratio, PEG ratio, "
                "and optionally DCF valuation. Essential for the Valuation Specialist (Gamma)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "price": {
                        "type": "number",
                        "description": "Current stock price"
                    },
                    "eps": {
                        "type": "number",
                        "description": "Earnings per share"
                    },
                    "growth_rate": {
                        "type": "number",
                        "description": "Expected earnings growth rate (as percentage, e.g., 15 for 15%)"
                    },
                    "free_cash_flows": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Optional list of projected free cash flows for DCF analysis"
                    },
                    "discount_rate": {
                        "type": "number",
                        "description": "WACC for DCF (default: 0.10)",
                        "default": 0.10
                    },
                    "terminal_growth": {
                        "type": "number",
                        "description": "Perpetual growth rate for DCF (default: 0.03)",
                        "default": 0.03
                    },
                    "shares_outstanding": {
                        "type": "number",
                        "description": "Number of shares outstanding (required for DCF)"
                    }
                },
                "required": ["price", "eps", "growth_rate"]
            }
        ),
        Tool(
            name="calculate_risk_metrics",
            description=(
                "Calculate risk metrics including volatility, Sharpe ratio, and moving averages. "
                "Used by the Valuation Specialist (Gamma) for risk assessment."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prices": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of historical prices"
                    },
                    "returns": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Optional list of returns (calculated from prices if not provided)"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "description": "Annual risk-free rate (default: 0.02)",
                        "default": 0.02
                    }
                },
                "required": ["prices"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Execute a tool by name with provided arguments.
    """
    try:
        # 1. Semantic Cache Lookup
        cached_result = cache.lookup(name, arguments)
        if cached_result:
            return [TextContent(
                type="text",
                text=json.dumps(cached_result, indent=2)
            )]

        # 2. Tool Execution
        if name == "fetch_filing_data":
            result = fetch_filing_data(
                ticker=arguments["ticker"],
                filing_type=arguments.get("filing_type", "10-K"),
                count=arguments.get("count", 3)
            )
        elif name == "get_news_stream":
            result = get_news_stream(
                ticker=arguments["ticker"],
                days=arguments.get("days", 7),
                max_articles=arguments.get("max_articles", 15)
            )
        elif name == "calculate_valuation_metrics":
            result = calculate_valuation_metrics(
                price=arguments["price"],
                eps=arguments["eps"],
                growth_rate=arguments["growth_rate"],
                free_cash_flows=arguments.get("free_cash_flows"),
                discount_rate=arguments.get("discount_rate", 0.10),
                terminal_growth=arguments.get("terminal_growth", 0.03),
                shares_outstanding=arguments.get("shares_outstanding")
            )
        elif name == "calculate_risk_metrics":
            result = calculate_risk_metrics(
                prices=arguments["prices"],
                returns=arguments.get("returns"),
                risk_free_rate=arguments.get("risk_free_rate", 0.02)
            )
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]
        
        # 3. Store result in Cache
        cache.store(name, arguments, result)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Error executing tool {name}: {str(e)}"
            })
        )]


async def main():
    """
    Main entry point for the MCP server.
    Runs the server using stdio transport.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
