"""Hjelpefunksjoner som gjør livet enklere i møte med Slack."""

import re
from typing import Any

import httpx

USERNAME_PATTERN: re.Pattern[str] = re.compile(r"<@([A-Z0-9]+)>")
"""Mønster for å kjenne igjen Slack brukernavn"""

EMOJI_PATTERN: re.Pattern[str] = re.compile(r":([a-zA-Z0-9_-]+):")
"""Mønster for å kjenne igjen Slack emoji"""

QUOTE_PATTERN: re.Pattern[str] = re.compile(r"^>(.*)", re.MULTILINE)
"""Mønster for å kjenne igjen et Slack sitat"""

QUOTE_LINK_PATTERN: re.Pattern[str] = re.compile(r"\(_(.*)_\)")
"""Mønster for å kjenne igjen en Slack sitat forklaring/lenke"""


def strip_msg(msg: str) -> str:
    """Filtrer ut tekst i meldingen som vi ikke ønsker å sende til NKS KBS."""
    # Filtrer ut Slack emoji
    msg = re.sub(EMOJI_PATTERN, "", msg)
    # Filtrer ut '@bruker' strenger
    msg = re.sub(USERNAME_PATTERN, "", msg)
    # Filtrer ut sitater
    msg = re.sub(QUOTE_PATTERN, "", msg)
    # Filtrer ut lenke til sitater
    msg = re.sub(QUOTE_LINK_PATTERN, "", msg)
    # Vi kjører 'strip' tilslutt slik at vi eventuelt fjerner mellomrom som
    # oppstår fordi vi har fjernet tekst
    return msg.strip()


def convert_msg(slack_msg: dict[str, str]) -> dict[str, str]:
    """Hjelpemetode som tar inn en Slack melding og konverterer til NKS KBS format."""
    result: dict[str, str] = {}
    result["role"] = "ai" if "app_id" in slack_msg else "human"
    text = strip_msg(slack_msg["text"])
    result["content"] = text
    return result


def format_slack(data: dict[str, Any]) -> str:
    """Formater en melding fra KBS til en streng som kan brukes på Slack."""
    text: str = data["answer"]["text"]
    cites = "\n\n".join(
        [
            f"> {cite['text'].replace('\n', ' ')}\n"
            f"(_{cite['title'] or 'Uten tittel'}_ / "
            f"_{cite['section'] or 'Uten seksjon'}_)"
            for cite in data["answer"]["citations"]
        ]
    )
    if cites:
        text += f"\n{cites}"
    return text


def is_bob_alive(url: httpx.URL) -> bool:
    """Sjekk om NKS KBS API er i live/oppe."""
    api_url = url.copy_with(path="/is_alive")
    try:
        reply = httpx.get(api_url)
        result: bool = reply.status_code == 200
        return result
    except httpx.ReadTimeout:
        return False
