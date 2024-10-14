"""Formatering for Slack Block-er."""

from typing import Any

import httpx

from .utils import markdown_to_slack


def message_blocks(msg: dict[str, Any]) -> list[dict[str, Any]]:
    """Formater et svar fra KBS med Slack Block-er."""
    blocks: list[dict[str, Any]] = []
    blocks.append(answer_block(msg))
    context = context_block(msg)
    if context["elements"]:
        blocks.append(context)
    return blocks


def answer_block(msg: dict[str, Any]) -> dict[str, Any]:
    """Formater selve svaret fra KBS som en Slack Block."""
    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": markdown_to_slack(msg["answer"]["text"])},
        "expand": True,
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
    cite_url = format_citation_url(
        httpx.URL(doc["metadata"]["KnowledgeArticle_QuartoUrl"]), citation
    )
    return {
        "type": "mrkdwn",
        "text": (
            f"*<{cite_url}|{citation['title']}>*"
            f"\n_{markdown_to_slack(citation['text'])}_"
        ),
    }


def format_citation_url(
    base_url: httpx.URL, citation: dict[str, str], num_word: int = 4
) -> httpx.URL:
    """Formater sitering URL med text fragment.

    Text Fragment gjør det mulig å be nettleseren om å utheve tekst på en side
    man ikke har kontroll over (se
    https://developer.mozilla.org/en-US/docs/Web/URI/Fragment/Text_fragments)

    Args:
        base_url:
            Original URL til kunnskapsartikkelen
        citation:
            Siteringsstrukturen med tekst
        num_word:
            Antall ord å ta med i tekstfragmentet
    Returns:
        Ny URL med tekstfragment som uthever tekst
    """
    cite_text = citation.get("text", "")
    if not cite_text:
        return base_url
    cite_words = cite_text.replace("\n", " ").split(" ")
    start_fragment = " ".join(cite_words[0:num_word])
    end_fragment = " ".join(cite_words[-1 - num_word : -1])
    return base_url.copy_with(fragment=f":~:text={start_fragment},{end_fragment}")
