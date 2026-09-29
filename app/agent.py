"""Query routing, safe calculations, and grounded answer generation."""

from __future__ import annotations

import ast
import operator
import re
from typing import Any

from .config import Settings, settings
from .models import Citation, QueryResponse
from .retrieval import RetrievalIndex, SearchResult


class Calculator:
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def evaluate(self, expression: str) -> float:
        tree = ast.parse(expression, mode="eval")

        def visit(node: ast.AST) -> float:
            if isinstance(node, ast.Expression):
                return visit(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return float(node.value)
            if isinstance(node, ast.UnaryOp) and type(node.op) in self._operators:
                return self._operators[type(node.op)](visit(node.operand))
            if isinstance(node, ast.BinOp) and type(node.op) in self._operators:
                left, right = visit(node.left), visit(node.right)
                if isinstance(node.op, ast.Pow) and abs(right) > 12:
                    raise ValueError("Exponent is too large")
                return float(self._operators[type(node.op)](left, right))
            raise ValueError("Only numeric arithmetic is allowed")

        result = visit(tree)
        if abs(result) > 1e15:
            raise ValueError("Result is too large")
        return result


def _calculator_expression(question: str) -> str | None:
    cleaned = question.lower().replace("what is", "").replace("calculate", "").strip(" ?")
    if re.fullmatch(r"[\d\s+\-*/().%^]+", cleaned):
        return cleaned.replace("^", "**")
    return None


class ResearchAgent:
    def __init__(self, config: Settings | None = None):
        self.config = config or settings
        self.calculator = Calculator()

    def answer(self, question: str, index: RetrievalIndex, top_k: int | None = None) -> QueryResponse:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty")
        expression = _calculator_expression(question)
        if expression:
            value = self.calculator.evaluate(expression)
            return QueryResponse(question=question, answer=f"The calculated result is **{value:g}**.", route="calculator", mode="offline")
        results = index.search(question, top_k=top_k or self.config.top_k)
        if results:
            return self._answer_from_sources(question, results)
        return QueryResponse(
            question=question,
            answer="I could not find a matching passage in the indexed sources. Try uploading a relevant document or rephrasing the question.",
            route="direct",
            mode="offline",
            warnings=["No indexed passage matched this question."],
        )

    def _answer_from_sources(self, question: str, results: list[SearchResult]) -> QueryResponse:
        citations = [
            Citation(
                citation_id=f"S{position}",
                source_id=result.chunk.source_id,
                source_name=result.chunk.source_name,
                chunk_id=result.chunk.chunk_id,
                score=max(0.0, result.score),
                excerpt=result.chunk.text,
            )
            for position, result in enumerate(results, start=1)
        ]
        context = " ".join(f"[{citation.citation_id}] {citation.excerpt}" for citation in citations)
        warnings: list[str] = []
        answer = self._offline_answer(question, citations)
        mode = "offline"
        if self.config.anthropic_api_key:
            try:
                answer = self._anthropic_answer(question, context)
                mode = "anthropic"
            except Exception as exc:  # pragma: no cover - network/provider-dependent
                warnings.append(f"Model generation failed; used offline answer ({type(exc).__name__}).")
        trace = [
            {"rank": result.rank, "source": result.chunk.source_name, "score": round(result.score, 4)}
            for result in results
        ]
        if results[0].score < 0.08:
            warnings.append("Retrieval confidence is low; verify the cited passages.")
        return QueryResponse(
            question=question,
            answer=answer,
            route="documents",
            mode=mode,
            citations=citations,
            warnings=warnings,
            retrieval_trace=trace,
        )

    @staticmethod
    def _offline_answer(question: str, citations: list[Citation]) -> str:
        excerpts = [f"[{citation.citation_id}] {citation.excerpt.strip()}" for citation in citations[:3]]
        return f"Based on the indexed sources, the strongest evidence for **{question}** is: " + " ".join(excerpts)

    def _anthropic_answer(self, question: str, context: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        message = client.messages.create(
            model=self.config.anthropic_model,
            max_tokens=700,
            system="Answer only from the supplied context. Preserve [S1]-style citations and do not invent sources.",
            messages=[{"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}],
        )
        return "".join(getattr(block, "text", "") for block in message.content).strip() or self._offline_answer(question, [])
