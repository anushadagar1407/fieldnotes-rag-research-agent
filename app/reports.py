from .models import QueryResponse


def render_report(query: QueryResponse) -> str:
    lines = [
        f"# Research report: {query.question}",
        "",
        f"**Route:** `{query.route}`  ",
        f"**Mode:** `{query.mode}`",
        "",
        "## Summary",
        "",
        query.answer.strip(),
        "",
    ]
    if query.citations:
        lines.extend(["## Sources", ""])
        for citation in query.citations:
            lines.extend([
                f"### [{citation.citation_id}] {citation.source_name}",
                f"Score: `{citation.score:.3f}`  ",
                citation.excerpt.strip(),
                "",
            ])
    if query.warnings:
        lines.extend(["## Warnings", "", *[f"- {warning}" for warning in query.warnings], ""])
    return "\n".join(lines).strip() + "\n"
