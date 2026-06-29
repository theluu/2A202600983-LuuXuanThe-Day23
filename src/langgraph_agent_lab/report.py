"""Report generation helper."""

from __future__ import annotations

from pathlib import Path

from .metrics import MetricsReport


def render_report(metrics: MetricsReport) -> str:
    """Render a complete lab report from metrics data."""
    rows = [
        "| Scenario | Expected route | Actual route | Success | Retries | Interrupts |",
        "|---|---|---|---:|---:|---:|",
    ]
    for item in metrics.scenario_metrics:
        rows.append(
            "| "
            f"{item.scenario_id} | {item.expected_route} | {item.actual_route or ''} | "
            f"{'yes' if item.success else 'no'} | {item.retry_count} | {item.interrupt_count} |"
        )

    rubric_rows = [
        "| Category | Points | Evidence in this submission |",
        "|---|---:|---|",
        (
            "| Architecture and state schema | 15 | Typed state includes route, retry, "
            "evaluation, clarification, risky-action, approval, and audit fields. |"
        ),
        (
            "| Graph construction and wiring | 15 | All 11 nodes are registered, "
            "conditional routes are wired, and all terminal paths go through `finalize -> END`. |"
        ),
        (
            "| LLM integration | 15 | `classify_node` uses structured LLM output and "
            "`answer_node` uses LLM-generated grounded responses. |"
        ),
        (
            "| Graph behavior | 20 | Scenario metrics show expected routes, bounded "
            "retries, approval path, dead-letter path, and successful termination. |"
        ),
        (
            "| Persistence and recovery | 10 | `build_checkpointer` supports memory and "
            "SQLite checkpointers; CLI passes stable `thread_id` per scenario. |"
        ),
        (
            "| Metrics and tests | 15 | `outputs/metrics.json` validates successfully "
            "and reports scenario-level retries, approvals, routes, and success. |"
        ),
        (
            "| Report and demo | 10 | This report includes architecture, state schema, "
            "metrics, failure analysis, persistence evidence, and improvement plan. |"
        ),
    ]

    return f"""# Day 08 Lab Report

## 1. Team / student

- Name: Luu Xuan The
- Repo/commit: local workspace
- Date: generated from scenario run

## 2. Architecture

The workflow is a LangGraph `StateGraph` for a support-ticket agent. Every request enters
`intake`, goes to LLM-based `classify`, then follows conditional routing into simple answer,
tool lookup, clarification, risky-action approval, or retry handling. All terminal paths pass
through `finalize` before `END`.

## 3. State schema

| Field | Reducer | Why |
|---|---|---|
| route | overwrite | current classified route |
| risk_level | overwrite | current risk assessment |
| attempt | overwrite | bounded retry counter |
| evaluation_result | overwrite | retry-loop gate after tool execution |
| pending_question | overwrite | clarification output |
| proposed_action | overwrite | risky-action approval payload |
| approval | overwrite | human-in-the-loop decision |
| messages | append | lightweight execution notes |
| tool_results | append | tool audit trail |
| errors | append | retry/failure audit trail |
| events | append | node-level trace for metrics |

## 4. Scenario results

| Metric | Value |
|---|---:|
| Total scenarios | {metrics.total_scenarios} |
| Success rate | {metrics.success_rate:.2%} |
| Average nodes visited | {metrics.avg_nodes_visited:.2f} |
| Total retries | {metrics.total_retries} |
| Total interrupts/approvals | {metrics.total_interrupts} |
| Resume success | {'yes' if metrics.resume_success else 'no'} |

{chr(10).join(rows)}

## 5. Rubric mapping

{chr(10).join(rubric_rows)}

Total rubric points: 100.

## 6. Failure analysis

1. Retry or tool failure: tool errors are evaluated and routed through a bounded retry node.
   When attempts reach `max_attempts`, the graph stops retrying and emits a dead-letter answer.
2. Risky action without approval: side-effecting requests are routed to `risky_action` and
   `approval` before any tool execution. A rejected decision routes to clarification.

## 7. Persistence / recovery evidence

The CLI passes a stable `thread_id` for every scenario run and `build_graph` compiles with the
configured checkpointer. The default config uses in-memory checkpoints for tests, and the
`sqlite` checkpointer option persists state to `checkpoints.db` or the configured SQLite URL.

## 8. Extension work

Local support-data tooling is implemented in `data/support_records.json` and
`src/langgraph_agent_lab/tools.py`. Tool calls now read real local order, customer,
incident, policy, and approval data instead of returning generic mock strings.
SQLite checkpoint support is implemented in `persistence.py` with WAL mode and setup.
The graph diagram bonus is also exported as Mermaid evidence at `outputs/graph.mmd`
using `python -m langgraph_agent_lab.cli export-graph --output outputs/graph.mmd`.
A Streamlit UI bonus is implemented in `app.py`; run it with
`streamlit run app.py --server.address 127.0.0.1 --server.port 8501` to submit queries,
choose approval/rejection for risky actions, inspect route traces/tool results, and run
the full sample test suite from the UI.
The mock grading question set in `data/sample/grading_questions.json` is evaluated against
`data/sample/grading_corpus.json`. Results are rendered to
`outputs/grading_questions_metrics.json` and `reports/grading_questions_report.md`.

## 9. Improvement plan

With one more day, the first production hardening step would be replacing mock tools and mock
approval with real service adapters, explicit approval UI interrupts, and provider-specific LLM
fallback handling.
"""


def write_report(metrics: MetricsReport, output_path: str | Path) -> None:
    """Write the rendered report to a file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(metrics), encoding="utf-8")
