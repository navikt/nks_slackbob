"""Tester for å sjekke at ekstra funksjoner fungerer som forventet."""

from typing import Any

import pytest

from nks_slackbob.utils import strip_msg


@pytest.fixture
def context() -> list[dict[str, Any]]:
    """Liste med kontekst dokumenter."""
    return [
        {
            "content": "Artikkel om dagpenger eller noe",
            "metadata": {
                "Title": "Dagpenger",
                "KnowledgeArticleId": "id1",
                "KnowledgeArticle_QuartoUrl": "https://localhost/id1",
            },
        },
        {
            "content": "Sykepenger er best!",
            "metadata": {
                "Title": "Sykepenger",
                "KnowledgeArticleId": "id2",
                "KnowledgeArticle_QuartoUrl": "https://localhost/id2",
            },
        },
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
                    "article": "id1",
                    "title": "Dagpenger",
                    "section": "Til bruker",
                }
            ],
        },
        "context": context,
    }


def test_strip_mention() -> None:
    """Sjekk at fjerning av @<brukernavn> fungerer."""
    assert strip_msg("<@U0G9QF9C6>") == ""


def test_strip_emoji() -> None:
    """Sjekk at emoji blir fjernet."""
    assert strip_msg(":mage:") == ""
    assert strip_msg("Hei :mage:") == "Hei"
    assert strip_msg(":mage: hei") == "hei"
