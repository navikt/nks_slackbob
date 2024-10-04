"""Formatering for Slack Block-er."""

from typing import Any


def message_block(msg: dict[str, Any]) -> list[dict[str, Any]]:
    """Formater et svar fra KBS med Slack Block-er."""
    blocks: list[dict[str, Any]] = []
    blocks.append(answer_block(msg))
    citations = context_block(msg)
    if citations["elements"]:
        blocks.append(citations)
    return blocks


def answer_block(msg: dict[str, Any]) -> dict[str, Any]:
    """Formater selve svaret fra KBS som en Slack Block."""
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": msg["answer"]["text"]},
    }


def context_block(msg: dict[str, Any]) -> dict[str, Any]:
    """Formater siteringer som Slack Block."""
    context_map = {ctx["metadata"]["KnowledgeArticleId"]: ctx for ctx in msg["context"]}
    return {
        "type": "context",
        "elements": [
            cite_block(cite, context_map[cite["article"]])
            # MERK: Det er maksimalt lov med 10 elementer i en 'context' block
            # vi kutter derfor antall siteringer hvis det er flere, noe som
            # veldig sjeldent forekommer
            for cite in msg["answer"]["citations"][:10]
        ],
    }


def cite_block(citation: dict[str, str], doc: dict[str, Any]) -> dict[str, Any]:
    """Formater en enkelt sitering som en Slack Block."""
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                f"*<{doc['metadata']['KnowledgeArticle_QuartoUrl']}|{citation['title']}>*"
                f"\n_{citation['text']}_"
            ),
        },
    }
