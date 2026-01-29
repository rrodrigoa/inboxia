from __future__ import annotations

import re
from datetime import datetime
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.models import Embedding, Message
from app.providers.factory import get_provider

FILTER_RE = re.compile(r"(from|to|subject|before|after):([^\s]+)")


def _parse_filters(query: str) -> tuple[str, dict[str, str]]:
    filters = {match.group(1): match.group(2) for match in FILTER_RE.finditer(query)}
    clean_query = FILTER_RE.sub("", query).strip()
    return clean_query, filters


def _apply_filters(query, filters: dict[str, str]):
    if "from" in filters:
        query = query.filter(Message.from_email.ilike(f"%{filters['from']}%"))
    if "to" in filters:
        query = query.filter(Message.to_json.contains([filters["to"]]))
    if "subject" in filters:
        query = query.filter(Message.subject.ilike(f"%{filters['subject']}%"))
    if "before" in filters:
        try:
            dt = datetime.fromisoformat(filters["before"])
            query = query.filter(Message.sent_at < dt)
        except ValueError:
            pass
    if "after" in filters:
        try:
            dt = datetime.fromisoformat(filters["after"])
            query = query.filter(Message.sent_at > dt)
        except ValueError:
            pass
    return query


def retrieve_context(
    db: Session,
    account_id: int,
    query: str,
    selected_thread_id: int | None = None,
    top_k: int = 8,
) -> List[Tuple[Embedding, Message]]:
    base_query = db.query(Embedding, Message).join(Message, Embedding.message_id == Message.id)
    base_query = base_query.filter(Message.account_id == account_id)
    if selected_thread_id:
        base_query = base_query.filter(Message.thread_id == selected_thread_id)
        clean_query = query
    else:
        clean_query, filters = _parse_filters(query)
        base_query = _apply_filters(base_query, filters)
    provider = get_provider()
    query_vector = provider.embed([clean_query])[0]
    return (
        base_query.order_by(Embedding.vector.cosine_distance(query_vector))
        .limit(top_k)
        .all()
    )


def build_prompt(query: str, results: List[Tuple[Embedding, Message]]) -> tuple[str, List[dict]]:
    citations = []
    context_parts = []
    for embedding, message in results:
        citations.append(
            {
                "message_id": message.id,
                "sent_at": message.sent_at,
                "from_email": message.from_email,
                "subject": message.subject,
            }
        )
        context_parts.append(
            "\n".join(
                [
                    f"[Message {message.id} | {message.sent_at} | From: {message.from_email} | Subject: {message.subject}]",
                    embedding.content[:800],
                ]
            )
        )
    context = "\n\n".join(context_parts)
    prompt = (
        "Answer the question using only the context below. "
        "Do not invent facts. Cite message ids you used.\n\n"
        f"Question: {query}\n\nContext:\n{context}"
    )
    return prompt, citations


def answer_question(db: Session, account_id: int, query: str, selected_thread_id: int | None = None):
    results = retrieve_context(db, account_id, query, selected_thread_id)
    provider = get_provider()
    prompt, citations = build_prompt(query, results)
    answer = provider.chat(prompt)
    return answer, citations
