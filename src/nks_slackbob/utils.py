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

MARKDOWN_LINK_PATTERN: re.Pattern[str] = re.compile(r"\[(.+?)\]\((.+?)\)")
"""Mønster for å kjenne igjen en Markdown lenke"""

KBS_BOLD_PATTERN: re.Pattern[str] = re.compile(r"\*+([\w\d -]+?)\*+")
"""KBS-en har en tendens til å legge på flere ** for å markere bold"""

KBS_ITALIC_PATTERN: re.Pattern[str] = re.compile(r"\_+([\w\d -]+?)\_+")
"""KBS-en har en tendens til å legge på flere __ for å markere italic"""


def markdown_to_slack(msg: str) -> str:
    """Konverter tekst i Markdown til Slack sitt mrkdwn format."""
    # Konverter lenker
    msg = re.sub(MARKDOWN_LINK_PATTERN, r"<\g<2>|\g<1>>", msg)
    # Konverter bold
    msg = re.sub(KBS_BOLD_PATTERN, r"*\g<1>*", msg)
    # Konverter italic
    msg = re.sub(KBS_ITALIC_PATTERN, r"_\g<1>_", msg)
    return msg


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


def convert_msg(slack_msg: dict[str, Any]) -> dict[str, str]:
    """Hjelpemetode som tar inn en Slack melding og konverterer til NKS KBS format."""
    result: dict[str, str] = {}
    if "app_id" in slack_msg:
        result["role"] = "ai"
        result["content"] = strip_msg(slack_msg.get("text", ""))
        # Kan ikke anta at "blocks" alltid er i svaret fra Bob
        if "blocks" in slack_msg and slack_msg["blocks"]:
            result["content"] = slack_msg["blocks"][0]["text"]["text"]
    else:
        result["role"] = "human"
        result["content"] = strip_msg(slack_msg["text"])
    return result


def is_bob_alive(url: httpx.URL) -> bool:
    """Sjekk om NKS KBS API er i live/oppe."""
    api_url = url.copy_with(path="/is_alive")
    try:
        reply = httpx.get(api_url)
        result: bool = reply.status_code == 200
        return result
    except httpx.ReadTimeout:
        return False
