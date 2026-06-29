"""Local support-data tools used by the graph."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .state import AgentState, Route

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "support_records.json"


def load_support_data() -> dict[str, Any]:
    """Load the local support dataset."""
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _find_order(query: str, data: dict[str, Any]) -> dict[str, Any] | None:
    order_match = re.search(r"\border\s*#?\s*(\d+)\b", query, flags=re.IGNORECASE)
    if not order_match:
        return None
    order_id = order_match.group(1)
    return next(
        (order for order in data["orders"] if str(order["order_id"]) == order_id),
        None,
    )


def _verified_customer(data: dict[str, Any]) -> dict[str, Any]:
    return next(
        customer for customer in data["customers"] if customer.get("support_verified") is True
    )


def _format_order_lookup(query: str, data: dict[str, Any]) -> str:
    order = _find_order(query, data)
    if order is None:
        known_orders = ", ".join(str(item["order_id"]) for item in data["orders"])
        return (
            "No matching order was found in local support data. "
            f"Known demo order ids: {known_orders}."
        )
    return (
        "ORDER_LOOKUP "
        f"order_id={order['order_id']} "
        f"customer={order['customer_name']} "
        f"email={order['email']} "
        f"status={order['status']} "
        f"carrier={order['carrier'] or 'not_assigned'} "
        f"tracking={order['tracking_number'] or 'not_available'} "
        f"estimated_delivery={order['estimated_delivery']} "
        f"total_usd={order['total_usd']} "
        f"last_update={order['last_update']}"
    )


def _format_risky_action(state: AgentState, data: dict[str, Any]) -> str:
    query = state.get("query", "")
    approval = state.get("approval") or {}
    customer = _verified_customer(data)
    action_type = "delete_account" if "delete" in query.lower() else "refund_and_notify"
    action_id = f"ACT-{state.get('thread_id', 'local').replace('thread-', '').replace('ui-', '')}"
    return (
        "APPROVED_ACTION "
        f"action_id={action_id} "
        f"action_type={action_type} "
        f"customer_id={customer['customer_id']} "
        f"customer={customer['name']} "
        f"email={customer['email']} "
        f"reviewer={approval.get('reviewer', 'unknown')} "
        f"comment={approval.get('comment', '')}"
    )


def _format_incident_result(attempt: int, data: dict[str, Any]) -> str:
    incident = data["incidents"][0]
    if attempt < int(incident["recover_after_attempts"]):
        return (
            "ERROR "
            f"incident_id={incident['incident_id']} "
            f"title={incident['title']} "
            f"status={incident['status']} "
            f"attempt={attempt + 1} "
            f"last_update={incident['last_update']}"
        )
    return (
        "INCIDENT_RECOVERY "
        f"incident_id={incident['incident_id']} "
        "status=recovered "
        f"attempt={attempt + 1} "
        f"last_update={incident['last_update']}"
    )


def execute_support_tool(state: AgentState) -> str:
    """Execute a local data-backed support tool for the current route."""
    data = load_support_data()
    route = state.get("route", "")
    attempt = state.get("attempt", 0)
    query = state.get("query", "")

    if route == Route.ERROR.value:
        return _format_incident_result(attempt, data)
    if route == Route.RISKY.value:
        return _format_risky_action(state, data)
    if route == Route.TOOL.value:
        return _format_order_lookup(query, data)

    policy = data["policies"][0]
    return (
        f"POLICY policy_id={policy['policy_id']} "
        f"topic={policy['topic']} "
        f"summary={policy['summary']}"
    )
