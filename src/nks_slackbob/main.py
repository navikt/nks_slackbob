"""Applikasjonsoppsett for Slack bot-en."""

import functools
import logging
import random
import re

import httpx
from pydantic_core import Url
from slack_bolt import App
from slack_sdk import WebClient

from . import settings
from .auth import OAuth2Flow
from .expressions import WORKING_ON_ANSWER
from .utils import USERNAME_PATTERN, convert_msg, format_slack, is_bob_alive, strip_msg

API_URL = httpx.URL(str(settings.kbs_endpoint))
"""API URL til KBS systemet"""

# Set opp logging med Slack
logging.basicConfig(level=logging.INFO)

# Set opp autentisering
auth = OAuth2Flow(
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    token_endpoint=settings.auth_token_endpoint,
    scope=Url(
        f"api://{settings.nais_environment!s}.nks-aiautomatisering.nks-kbs/.default"
    ),
)

# Sett opp Slack app for å koble til Slack
app = App(token=settings.bot_token.get_secret_value())


def chat(client: WebClient, event: dict[str, str]) -> None:
    """Håndter et spørsmål på Slack ved å kalle NKS KBS."""
    # Hent ut samtale historie før vi svarer ut noe
    thread = event.get("thread_ts", event["ts"])
    chat_hist = client.conversations_replies(channel=event["channel"], ts=thread)
    # Start med å svare at vi jobber med et svar til bruker
    temp_msg = client.chat_postMessage(
        text=random.choice(WORKING_ON_ANSWER),
        channel=event["channel"],
        thread_ts=event["ts"],
    )
    # Lag en funksjon som kan brukes for å endre svar, dette gjør det enklere å
    # ha komplekse funksjoner senere som bruker både 'text' og 'blocks' for å
    # svare
    update_msg = functools.partial(
        client.chat_update,
        channel=temp_msg.get("channel"),  # type: ignore[arg-type]
        ts=temp_msg.get("ts"),  # type: ignore[arg-type]
    )
    # Sjekk tidlig om API-et kjører, slik at bruker slipper å vente
    if not is_bob_alive(API_URL):
        update_msg(text="Kunnskapsbasen kjører ikke akkurat nå :construction:")
        return
    # Hent ut chat historikk og spørsmål fra brukeren
    history = [convert_msg(msg) for msg in chat_hist.get("messages")[:-1]]  # type: ignore[index]
    question = strip_msg(event["text"])
    # Send spørsmål til NKS KBS
    try:
        reply = httpx.post(
            API_URL.copy_with(path="/api/v1/chat"),
            headers={"Authorization": f"Bearer {auth.get_token().get_secret_value()}"},
            json={"history": history, "question": question},
            timeout=settings.answer_timeout,
        )
        if reply.status_code != 200:
            app.logger.error(
                "Mottok status %s og begrunnelse %s",
                reply.status_code,
                reply.reason_phrase,
            )
            update_msg(text="Ånei! Noe gikk galt for kunnskapsbasen :scream:")
            return
    except httpx.ReadTimeout:
        app.logger.error(
            "Spørring mot kunnskapbasen tok for lang tid, ventet %.1f sekunder!",
            settings.answer_timeout,
        )
        update_msg(text="Kunnskapsbasen svarer ikke :shrug:")
        return
    # Hent respons fra KBS og formater det for Slack
    update_msg(text=format_slack(reply.json()))


@app.event("app_mention")
def slack_mention(event: dict[str, str], client: WebClient) -> None:
    """Håndter @bot meldinger på Slack."""
    app.logger.info(
        "App mention fra bruker %s, i kanal %s, med tråd %s",
        event["user"],
        event["channel"],
        event["ts"],
    )
    chat(client, event)


@app.event("message")
def thread_reply(event: dict[str, str], client: WebClient) -> None:
    """Håndter svar i tråder boten har besvart."""
    # Hvis meldingen ikke inneholder noe tekst avbryter vi prosessering
    if "text" not in event:
        return
    # Det første vi sjekker er om meldingen inneholder en '@bot' til oss, slike
    # meldinger blir besvart av 'slack_mention' over og hvis vi ikke stopper
    # prosessering her blir det to svar i tråden
    for username in re.findall(USERNAME_PATTERN, event["text"]):
        user = client.users_info(user=username)
        if user.get("user")["profile"].get("api_app_id") == settings.id:  # type: ignore[index]
            return
    # Sjekk om det er en direkte melding til boten, hvis det er det OG det ikke
    # er en tråd så svarer vi direkte
    if event["channel_type"] == "im" and "thread_ts" not in event:
        app.logger.info("Direkte melding fra bruker %s", event["user"])
        chat(client, event)
        return
    # Sjekk at meldingen er et svar i en tråd
    if "thread_ts" not in event:
        return
    # Hvis det er svar i en tråd så sjekker vi om boten er involvert i tråden,
    # hvis ikke så svarer vi ikke
    history = client.conversations_replies(
        channel=event["channel"], ts=event["thread_ts"]
    )
    we_replied = any(
        [
            msg["app_id"] == settings.id
            for msg in history.get("messages")  # type: ignore[union-attr]
            if "app_id" in msg
        ]
    )
    if not we_replied:
        return
    # Kommer vi hit så er det et spørsmål i en tråd som vi burde prøve å besvare
    app.logger.info(
        "Oppfølgningsspørsmål i tråd %s (kanal: %s), fra bruker %s",
        event["ts"],
        event["channel"],
        event["user"],
    )
    chat(client, event)


def main() -> None:
    """Inngangsporten til Slack boten."""
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    try:
        SocketModeHandler(app, app_token=settings.app_token.get_secret_value()).start()  # type: ignore[no-untyped-call]
    except KeyboardInterrupt:
        # Ignorer fordi det betyr at vi tester på kommandolinje og trenger ikke
        # beskjed at noe feilet
        pass


if __name__ == "__main__":
    main()
