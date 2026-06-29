"""Streamlit UI for the LangGraph support-ticket agent."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import streamlit as st

ROOT = Path(__file__).parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from langgraph_agent_lab.graph import build_graph  # noqa: E402
from langgraph_agent_lab.state import AgentState  # noqa: E402


def make_state(query: str, max_attempts: int, approval_override: dict[str, object]) -> AgentState:
    """Build a graph state from UI input."""
    thread_id = f"ui-{uuid4().hex[:12]}"
    return {
        "thread_id": thread_id,
        "scenario_id": "streamlit-ui",
        "query": query,
        "route": "",
        "risk_level": "unknown",
        "attempt": 0,
        "max_attempts": max_attempts,
        "final_answer": None,
        "evaluation_result": "",
        "pending_question": None,
        "proposed_action": None,
        "approval": None,
        "approval_override": approval_override,
        "messages": [],
        "tool_results": [],
        "errors": [],
        "events": [],
    }


def render_events(events: list[dict[str, object]]) -> None:
    """Render node events in a compact table."""
    if not events:
        return
    st.dataframe(
        [
            {
                "node": event.get("node"),
                "type": event.get("event_type"),
                "message": event.get("message"),
            }
            for event in events
        ],
        use_container_width=True,
        hide_index=True,
    )


st.set_page_config(page_title="LangGraph Agent Lab", layout="wide")

st.title("LangGraph Support Agent")

with st.sidebar:
    st.header("Run settings")
    sample = st.selectbox(
        "Sample query",
        [
            "How do I reset my password?",
            "Please lookup order status for order 12345",
            "Can you fix it?",
            "Refund this customer and send confirmation email",
            "Timeout failure while processing request",
            "Delete customer account after support verification",
        ],
    )
    max_attempts = st.number_input("Max retry attempts", min_value=1, max_value=5, value=3)
    approval_choice = st.radio("Risky action decision", ["Approve", "Reject"], horizontal=True)
    reviewer = st.text_input("Reviewer", value="streamlit-reviewer")
    comment = st.text_input(
        "Approval comment",
        value="Reviewed from Streamlit UI",
    )

query = st.text_area("Support ticket", value=sample, height=110)

if st.button("Run agent", type="primary", use_container_width=False):
    approval_override = {
        "approved": approval_choice == "Approve",
        "reviewer": reviewer,
        "comment": comment,
    }
    state = make_state(query, int(max_attempts), approval_override)
    graph = build_graph()

    with st.spinner("Running graph..."):
        result = graph.invoke(state, config={"configurable": {"thread_id": state["thread_id"]}})

    st.session_state["last_result"] = result

result = st.session_state.get("last_result")
if result:
    top = st.columns(4)
    top[0].metric("Route", result.get("route") or "unknown")
    top[1].metric("Risk", result.get("risk_level") or "unknown")
    top[2].metric("Attempts", result.get("attempt", 0))
    top[3].metric("Events", len(result.get("events", [])))

    st.subheader("Final answer")
    st.write(result.get("final_answer") or result.get("pending_question") or "No answer generated.")

    details = st.tabs(["Trace", "Tool results", "Approval", "Raw state"])
    with details[0]:
        render_events(result.get("events", []))
    with details[1]:
        tool_results = result.get("tool_results", [])
        if tool_results:
            for item in tool_results:
                st.code(item)
        else:
            st.caption("No tool calls for this route.")
    with details[2]:
        st.json(
            {
                "proposed_action": result.get("proposed_action"),
                "approval": result.get("approval"),
            }
        )
    with details[3]:
        st.json(result)
