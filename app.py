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
from langgraph_agent_lab.metrics import metric_from_state, summarize_metrics  # noqa: E402
from langgraph_agent_lab.scenarios import load_scenarios  # noqa: E402
from langgraph_agent_lab.state import AgentState, initial_state  # noqa: E402
from langgraph_agent_lab.tools import load_support_data  # noqa: E402


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


def run_sample_suite() -> tuple[object, list[dict[str, object]]]:
    """Run all sample scenarios and return summary metrics plus raw results."""
    graph = build_graph()
    scenarios = load_scenarios(ROOT / "data" / "sample" / "scenarios.jsonl")
    metrics = []
    rows = []
    for scenario in scenarios:
        state = initial_state(scenario)
        result = graph.invoke(state, config={"configurable": {"thread_id": state["thread_id"]}})
        metric = metric_from_state(
            result,
            scenario.expected_route.value,
            scenario.requires_approval,
        )
        metrics.append(metric)
        rows.append(
            {
                "scenario": scenario.id,
                "query": scenario.query,
                "expected": metric.expected_route,
                "actual": metric.actual_route,
                "success": metric.success,
                "nodes": metric.nodes_visited,
                "retries": metric.retry_count,
                "approvals": metric.interrupt_count,
                "answer": result.get("final_answer") or result.get("pending_question"),
            }
        )
    return summarize_metrics(metrics), rows


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

main_tab, suite_tab, data_tab = st.tabs(["Single ticket", "All test scenarios", "Support data"])

with main_tab:
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
        st.write(
            result.get("final_answer")
            or result.get("pending_question")
            or "No answer generated."
        )

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

with suite_tab:
    st.subheader("Run all sample scenarios")
    st.caption(
        "This runs all routes: simple, tool lookup, missing info, "
        "risky approval, retry, dead letter."
    )
    if st.button("Run full test suite", type="primary"):
        with st.spinner("Running all scenarios through the graph..."):
            suite_report, suite_rows = run_sample_suite()
        st.session_state["suite_report"] = suite_report
        st.session_state["suite_rows"] = suite_rows

    suite_report = st.session_state.get("suite_report")
    suite_rows = st.session_state.get("suite_rows")
    if suite_report and suite_rows:
        metrics = st.columns(4)
        metrics[0].metric("Scenarios", suite_report.total_scenarios)
        metrics[1].metric("Success rate", f"{suite_report.success_rate:.0%}")
        metrics[2].metric("Retries", suite_report.total_retries)
        metrics[3].metric("Approvals", suite_report.total_interrupts)
        st.dataframe(suite_rows, use_container_width=True, hide_index=True)

with data_tab:
    st.subheader("Local support dataset")
    st.caption("Tool calls use this local data instead of returning generic mock strings.")
    st.json(load_support_data())
