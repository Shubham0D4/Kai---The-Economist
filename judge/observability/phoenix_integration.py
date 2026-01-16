"""
Arize Phoenix Observability Integration
Provides tracing and monitoring for agent debates.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from phoenix.otel import register
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
    PHOENIX_AVAILABLE = True
except ImportError:
    PHOENIX_AVAILABLE = False
    print("[WARNING] Arize Phoenix not available. Install with: pip install arize-phoenix")


class PhoenixTracer:
    """
    Wrapper for Arize Phoenix tracing.
    Tracks agent calls, MCP tool usage, and grounding sources.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize Phoenix tracer.
        
        Args:
            enabled: Whether to enable Phoenix tracing
        """
        self.enabled = enabled and PHOENIX_AVAILABLE
        self.tracer = None
        
        if self.enabled:
            try:
                # Register Phoenix
                tracer_provider = register(
                    project_name="kai-economist",
                    endpoint="http://localhost:6006/v1/traces"
                )
                
                # Get tracer
                self.tracer = trace.get_tracer("kai.coordinator")
                
                print("[PHOENIX] Observability enabled")
                print("[PHOENIX] View traces at http://localhost:6006")
            except Exception as e:
                print(f"[PHOENIX] Failed to initialize: {e}")
                self.enabled = False
        else:
            print("[PHOENIX] Observability disabled")
    
    def start_debate_trace(self, ticker: str, persona: str) -> Optional[Any]:
        """
        Start a trace for a complete debate.
        
        Args:
            ticker: Stock ticker
            persona: Risk persona
            
        Returns:
            Span context or None
        """
        if not self.enabled or not self.tracer:
            return None
        
        span = self.tracer.start_span(
            "debate",
            attributes={
                "ticker": ticker,
                "persona": persona,
                "debate.type": "round_robin",
                "debate.rounds": 3
            }
        )
        
        return span
    
    def trace_agent_call(
        self,
        agent_name: str,
        round_number: int,
        ticker: str,
        parent_span: Optional[Any] = None
    ):
        """
        Create a span for an agent call.
        
        Args:
            agent_name: Name of the agent
            round_number: Round number
            ticker: Stock ticker
            parent_span: Parent span context
            
        Returns:
            Span context
        """
        if not self.enabled or not self.tracer:
            return None
        
        span_name = f"{agent_name}_round_{round_number}"
        
        if parent_span:
            ctx = trace.set_span_in_context(parent_span)
            span = self.tracer.start_span(
                span_name,
                context=ctx,
                attributes={
                    "agent.name": agent_name,
                    "agent.round": round_number,
                    "ticker": ticker
                }
            )
        else:
            span = self.tracer.start_span(
                span_name,
                attributes={
                    "agent.name": agent_name,
                    "agent.round": round_number,
                    "ticker": ticker
                }
            )
        
        return span
    
    def log_mcp_tool_call(
        self,
        span: Optional[Any],
        tool_name: str,
        parameters: Dict[str, Any],
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """
        Log an MCP tool call within a span.
        
        Args:
            span: Current span
            tool_name: Name of MCP tool
            parameters: Tool parameters
            result: Tool result
            error: Error message if failed
        """
        if not self.enabled or not span:
            return
        
        # Add event to span
        span.add_event(
            f"mcp_tool.{tool_name}",
            attributes={
                "tool.name": tool_name,
                "tool.parameters": str(parameters),
                "tool.success": error is None
            }
        )
        
        if result:
            span.set_attribute(f"tool.{tool_name}.result_size", len(str(result)))
        
        if error:
            span.set_attribute(f"tool.{tool_name}.error", error)
            span.set_status(Status(StatusCode.ERROR, error))
    
    def log_grounding_source(
        self,
        span: Optional[Any],
        source: str,
        source_type: str = "unknown"
    ):
        """
        Log a grounding source for traceability.
        
        Args:
            span: Current span
            source: Description of the source
            source_type: Type of source (filing, news, calculation, etc.)
        """
        if not self.enabled or not span:
            return
        
        span.add_event(
            "grounding_source",
            attributes={
                "source.description": source,
                "source.type": source_type
            }
        )
    
    def log_formula(
        self,
        span: Optional[Any],
        formula_name: str,
        formula: str,
        parameters: Dict[str, Any],
        result: Any
    ):
        """
        Log a formula for traceability.
        
        Args:
            span: Current span
            formula_name: Name of the formula
            formula: Formula expression
            parameters: Input parameters
            result: Calculation result
        """
        if not self.enabled or not span:
            return
        
        span.add_event(
            "formula_calculation",
            attributes={
                "formula.name": formula_name,
                "formula.expression": formula,
                "formula.parameters": str(parameters),
                "formula.result": str(result)
            }
        )
    
    def log_cross_critique(
        self,
        span: Optional[Any],
        critic: str,
        target: str,
        critique_length: int
    ):
        """
        Log a cross-critique event.
        
        Args:
            span: Current span
            critic: Agent providing critique
            target: Agent being critiqued
            critique_length: Length of critique text
        """
        if not self.enabled or not span:
            return
        
        span.add_event(
            "cross_critique",
            attributes={
                "critique.critic": critic,
                "critique.target": target,
                "critique.length": critique_length
            }
        )
    
    def end_span(self, span: Optional[Any], success: bool = True, error: Optional[str] = None):
        """
        End a span.
        
        Args:
            span: Span to end
            success: Whether the operation succeeded
            error: Error message if failed
        """
        if not self.enabled or not span:
            return
        
        if not success and error:
            span.set_status(Status(StatusCode.ERROR, error))
        else:
            span.set_status(Status(StatusCode.OK))
        
        span.end()
    
    def get_trace_url(self, span: Optional[Any]) -> Optional[str]:
        """
        Get the Phoenix UI URL for a trace.
        
        Args:
            span: Span to get URL for
            
        Returns:
            URL string or None
        """
        if not self.enabled or not span:
            return None
        
        # Phoenix UI is typically at localhost:6006
        return "http://localhost:6006"


# Global tracer instance
_phoenix_tracer: Optional[PhoenixTracer] = None


def get_phoenix_tracer(enabled: bool = True) -> PhoenixTracer:
    """
    Get or create the global Phoenix tracer.
    
    Args:
        enabled: Whether to enable Phoenix
        
    Returns:
        PhoenixTracer instance
    """
    global _phoenix_tracer
    
    if _phoenix_tracer is None:
        phoenix_enabled = enabled and os.getenv("PHOENIX_ENABLED", "true").lower() == "true"
        _phoenix_tracer = PhoenixTracer(enabled=phoenix_enabled)
    
    return _phoenix_tracer


# For testing
if __name__ == "__main__":
    # Test Phoenix integration
    tracer = get_phoenix_tracer(enabled=True)
    
    # Start debate trace
    debate_span = tracer.start_debate_trace("AAPL", "zen")
    
    # Trace agent call
    agent_span = tracer.trace_agent_call("charlie", 1, "AAPL", debate_span)
    
    # Log MCP tool call
    tracer.log_mcp_tool_call(
        agent_span,
        "fetch_filing_data",
        {"ticker": "AAPL", "filing_type": "10-K"},
        result={"success": True, "filings": []}
    )
    
    # Log grounding source
    tracer.log_grounding_source(agent_span, "10-K filing 2025-10-31", "sec_filing")
    
    # Log formula
    tracer.log_formula(
        agent_span,
        "PE Ratio",
        "PE = Price / EPS",
        {"price": 150.0, "eps": 6.5},
        23.08
    )
    
    # End spans
    tracer.end_span(agent_span, success=True)
    tracer.end_span(debate_span, success=True)
    
    print(f"[TEST] Trace URL: {tracer.get_trace_url(debate_span)}")
