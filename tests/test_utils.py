"""Tester for å sjekke at ekstra funksjoner fungerer som forventet."""

from typing import Any

import pytest

from nks_slackbob.utils import format_slack, strip_msg


@pytest.fixture
def context() -> list[dict[str, Any]]:
    """Liste med kontekst dokumenter."""
    return [
        {
            "content": "Artikkel om dagpenger eller noe",
            "metadata": {"Title": "Dagpenger"},
        },
        {"content": "Sykepenger er best!", "metadata": {"Title": "Sykepenger"}},
    ]


@pytest.fixture
def answer_no_cites(context: list[dict[str, Any]]) -> dict[str, Any]:
    """Enkel melding fra KBS uten sitater."""
    return {
        "answer": {
            "text": "Enkel melding med bare tekst",
            "citations": [],
        },
        "context": context,
    }


@pytest.fixture
def answer_cites(context: list[dict[str, Any]]) -> dict[str, Any]:
    """Melding med siteringer."""
    return {
        "answer": {
            "text": "Enkel tekst uten mening",
            "citations": [
                {
                    "text": "Helt uten mening!",
                    "article": "article1",
                    "title": "Dagpenger",
                    "section": "Til bruker",
                }
            ],
        },
        "context": context,
    }


def test_format_no_cite(answer_no_cites: dict[str, Any]) -> None:
    """Sjekk at KBS melding uten sitering formateres riktig."""
    formatted = format_slack(answer_no_cites)
    assert formatted == answer_no_cites["answer"]["text"]


def test_format_cite(answer_cites: dict[str, Any]) -> None:
    """Sjekk at KBS melding med sitering formateres riktig."""
    formatted = format_slack(answer_cites)
    assert formatted.startswith(answer_cites["answer"]["text"])
    assert ">" in formatted


def test_strip_no_cite(answer_no_cites: dict[str, Any]) -> None:
    """Sjekk at å fjerne Slack formatering fungerer som forventet."""
    formatted = format_slack(answer_no_cites)
    stripped = strip_msg(formatted)
    assert stripped == answer_no_cites["answer"]["text"]


def test_strip_cite(answer_cites: dict[str, Any]) -> None:
    """Sjekk at å fjerne Slack formatering fungerer som forventet."""
    formatted = format_slack(answer_cites)
    stripped = strip_msg(formatted)
    assert stripped == answer_cites["answer"]["text"]


def test_strip_mention() -> None:
    """Sjekk at fjerning av @<brukernavn> fungerer."""
    assert strip_msg("<@U0G9QF9C6>") == ""


def test_strip_emoji() -> None:
    """Sjekk at emoji blir fjernet."""
    assert strip_msg(":mage:") == ""
    assert strip_msg("Hei :mage:") == "Hei"
    assert strip_msg(":mage: hei") == "hei"
