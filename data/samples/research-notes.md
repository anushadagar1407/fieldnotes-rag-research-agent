# Research notes

I built Fieldnotes as a retrieval-augmented generation (RAG) research console. It searches local source passages first, then keeps each answer tied to the evidence that supports it.

When I build evidence-led systems, I want every answer to point back to a source passage. I check retrieval quality with realistic questions instead of only synthetic examples.

I record the question, selected passages, route, and warnings in an audit trail. That gives me a practical way to inspect a result and challenge it when the evidence is weak.
