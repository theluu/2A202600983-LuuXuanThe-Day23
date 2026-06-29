"""Runner for mock grading questions."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field


class GradingQuestion(BaseModel):
    id: str
    question: str
    must_contain_any: list[str] = Field(default_factory=list)
    must_not_contain: list[str] = Field(default_factory=list)
    expect_top1_doc_id: str
    grading_criteria: list[str] = Field(default_factory=list)


class CorpusDoc(BaseModel):
    doc_id: str
    title: str
    content: str


class GradingResult(BaseModel):
    id: str
    question: str
    answer: str
    expected_top1_doc_id: str
    actual_top1_doc_id: str
    top1_match: bool
    contains_required: bool
    violates_forbidden: bool
    success: bool


class GradingReport(BaseModel):
    total_questions: int
    success_rate: float
    top1_accuracy: float
    required_answer_rate: float
    results: list[GradingResult]


def load_grading_questions(path: str | Path) -> list[GradingQuestion]:
    """Load grading questions from JSON."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [GradingQuestion.model_validate(item) for item in payload]


def load_corpus(path: str | Path) -> list[CorpusDoc]:
    """Load local mock corpus documents."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [CorpusDoc.model_validate(item) for item in payload]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[\wÀ-ỹ]+", text.lower()))


def retrieve_top_doc(question: str, corpus: list[CorpusDoc]) -> CorpusDoc:
    """Return the document with the highest token overlap."""
    question_tokens = _tokens(question)
    return max(
        corpus,
        key=lambda doc: len(question_tokens & _tokens(f"{doc.title} {doc.content}")),
    )


def _sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]


def answer_from_doc(question: str, doc: CorpusDoc) -> str:
    """Generate a concise extractive answer from the retrieved document."""
    question_tokens = _tokens(question)
    sentence = max(
        _sentences(doc.content),
        key=lambda item: len(question_tokens & _tokens(item)),
    )
    return f"{sentence} (Nguồn: {doc.doc_id})"


def _contains_any(answer: str, terms: list[str]) -> bool:
    if not terms:
        return True
    lower_answer = answer.lower()
    return any(term.lower() in lower_answer for term in terms)


def _contains_forbidden(answer: str, terms: list[str]) -> bool:
    lower_answer = answer.lower()
    return any(term.lower() in lower_answer for term in terms)


def run_grading_questions(
    questions_path: str | Path,
    corpus_path: str | Path,
) -> GradingReport:
    """Run mock grading questions against the local corpus."""
    questions = load_grading_questions(questions_path)
    corpus = load_corpus(corpus_path)
    results: list[GradingResult] = []

    for question in questions:
        doc = retrieve_top_doc(question.question, corpus)
        answer = answer_from_doc(question.question, doc)
        top1_match = doc.doc_id == question.expect_top1_doc_id
        contains_required = _contains_any(answer, question.must_contain_any)
        violates_forbidden = _contains_forbidden(answer, question.must_not_contain)
        success = top1_match and contains_required and not violates_forbidden
        results.append(
            GradingResult(
                id=question.id,
                question=question.question,
                answer=answer,
                expected_top1_doc_id=question.expect_top1_doc_id,
                actual_top1_doc_id=doc.doc_id,
                top1_match=top1_match,
                contains_required=contains_required,
                violates_forbidden=violates_forbidden,
                success=success,
            )
        )

    total = len(results)
    return GradingReport(
        total_questions=total,
        success_rate=sum(item.success for item in results) / total,
        top1_accuracy=sum(item.top1_match for item in results) / total,
        required_answer_rate=sum(item.contains_required for item in results) / total,
        results=results,
    )


def write_grading_metrics(report: GradingReport, output_path: str | Path) -> None:
    """Write grading question metrics JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")


def render_grading_report(report: GradingReport) -> str:
    """Render a markdown report for grading questions."""
    rows = [
        "| Question | Expected doc | Actual doc | Required answer | Forbidden terms | Success |",
        "|---|---|---|---:|---:|---:|",
    ]
    for item in report.results:
        rows.append(
            "| "
            f"{item.id} | {item.expected_top1_doc_id} | {item.actual_top1_doc_id} | "
            f"{'yes' if item.contains_required else 'no'} | "
            f"{'yes' if item.violates_forbidden else 'no'} | "
            f"{'yes' if item.success else 'no'} |"
        )

    answers = ["## Answers"]
    for item in report.results:
        answers.append(f"### {item.id}")
        answers.append(f"**Question:** {item.question}")
        answers.append(f"**Answer:** {item.answer}")
        answers.append("")

    return f"""# Mock Grading Questions Report

## Summary

| Metric | Value |
|---|---:|
| Total questions | {report.total_questions} |
| Success rate | {report.success_rate:.2%} |
| Top-1 retrieval accuracy | {report.top1_accuracy:.2%} |
| Required answer rate | {report.required_answer_rate:.2%} |

## Results

{chr(10).join(rows)}

{chr(10).join(answers)}
"""


def write_grading_report(report: GradingReport, output_path: str | Path) -> None:
    """Write the markdown grading report."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_grading_report(report), encoding="utf-8")
