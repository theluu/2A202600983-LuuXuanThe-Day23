"""Node functions for the LangGraph workflow."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .llm import get_llm
from .state import AgentState, make_event
from .tools import execute_support_tool


class Classification(BaseModel):
    route: str = Field(..., description="One of: simple, tool, missing_info, risky, error")
    risk_level: str = Field(..., description="high or low")
    reasoning: str = Field(..., description="Short explanation")

def classify_node(state: AgentState) -> dict:
    """Classify the query using LLM with structured output."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(Classification)
    
    prompt = f"""Classify this support ticket into ONE route.
Query: {state['query']}

Available routes:
- simple: General questions answerable without tools
- tool: Needs to lookup information (order status, etc.)
- missing_info: Vague or incomplete query
- risky: Actions with side effects (refund, delete, email, cancel)
- error: System failure or timeout

Priority: risky > tool > missing_info > error > simple

Respond with structured classification.
"""

    result: Classification = structured_llm.invoke(prompt)
    
    return {
        "route": result.route,
        "risk_level": result.risk_level,
        "messages": [f"classify: {result.route} ({result.reasoning})"],
        "events": [make_event("classify", "completed", f"Classified as {result.route}")]
    }

# ─── EXAMPLE: working node (provided for reference) ──────────────────
def intake_node(state: AgentState) -> dict:
    """Normalize raw query. This node is provided as a working example."""
    query = state.get("query", "").strip()
    return {
        "query": query,
        "messages": [f"intake:{query[:40]}"],
        "events": [make_event("intake", "completed", "query normalized")],
    }

def tool_node(state: AgentState) -> dict:
    """Execute the local support-data tool."""
    result = execute_support_tool(state)
    
    return {
        "tool_results": [result],
        "messages": [f"tool: {result[:60]}..."],
        "events": [make_event("tool", "completed", result)]
    }

def evaluate_node(state: AgentState) -> dict:
    """Evaluate if tool result is good enough."""
    tool_results = state.get("tool_results", [])
    latest = tool_results[-1] if tool_results else ""
    
    if "ERROR" in latest.upper():
        evaluation = "needs_retry"
    else:
        evaluation = "success"
    
    return {
        "evaluation_result": evaluation,
        "events": [make_event("evaluate", "completed", f"Tool evaluation: {evaluation}")]
    }

def answer_node(state: AgentState) -> dict:
    """Generate final answer using LLM."""
    llm = get_llm()
    
    context = "\n".join(state.get("tool_results", []))
    approval = state.get("approval", {})
    
    prompt = f"""Answer the user query based on available information.

Query: {state['query']}
Tool Results: {context}
Approval: {approval}

Give a helpful, professional response.
"""

    response = llm.invoke(prompt).content
    
    return {
        "final_answer": response,
        "messages": [f"answer: {response[:100]}..."],
        "events": [make_event("answer", "completed", "Final answer generated")]
    }

def ask_clarification_node(state: AgentState) -> dict:
    """Ask for missing information."""
    query = state.get("query", "")
    
    clarification = f"Để hỗ trợ bạn tốt hơn, bạn có thể cung cấp thêm thông tin về: {query} không?"
    
    return {
        "pending_question": clarification,
        "final_answer": clarification,
        "messages": [f"clarify: {clarification[:80]}..."],
        "events": [make_event("clarify", "completed", "Asked for clarification")]
    }

def risky_action_node(state: AgentState) -> dict:
    """Prepare risky action for approval."""
    query = state.get("query", "")
    
    proposed = (
        f"Proposed action: {query}\n"
        "This action has potential side effects and requires approval."
    )
    
    return {
        "proposed_action": proposed,
        "messages": ["risky_action: prepared proposal"],
        "events": [make_event("risky_action", "completed", "Risky action prepared for approval")]
    }

def approval_node(state: AgentState) -> dict:
    """Mock human approval (can be extended to real HITL)."""
    decision = state.get("approval_override") or {
        "approved": True,
        "reviewer": "mock-reviewer",
        "comment": "Approved for testing",
    }
    status = "approved" if decision.get("approved") else "rejected"
    
    return {
        "approval": decision,
        "messages": [f"approval: {status}"],
        "events": [make_event("approval", "completed", f"Action {status}")]
    }

def retry_or_fallback_node(state: AgentState) -> dict:
    """Increment attempt counter on failure."""
    attempt = state.get("attempt", 0) + 1
    
    return {
        "attempt": attempt,
        "errors": [f"Attempt {attempt} failed"],
        "messages": [f"retry: attempt {attempt}"],
        "events": [make_event("retry", "completed", f"Retry attempt {attempt}")]
    }

def dead_letter_node(state: AgentState) -> dict:
    """Handle unrecoverable failure."""
    return {
        "final_answer": (
            "Chúng tôi không thể xử lý yêu cầu lúc này. "
            "Vui lòng thử lại sau hoặc liên hệ hỗ trợ."
        ),
        "messages": ["dead_letter: escalated"],
        "events": [make_event("dead_letter", "completed", "Moved to dead letter queue")]
    }

def finalize_node(state: AgentState) -> dict:
    """Final node - all paths must go through here."""
    return {
        "events": [make_event("finalize", "completed", "Workflow finished successfully")]
    }
