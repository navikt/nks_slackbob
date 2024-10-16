"""Applikasjonsoppsett for Slack bot-en."""

import datetime
import functools
import json
import random
import re
import uuid

import httpx
import structlog
from pydantic_core import Url
from slack_bolt import App
from slack_sdk import WebClient

from . import settings
from .auth import OAuth2Flow
from .blocks import message_blocks
from .expressions import WORKING_ON_ANSWER
from .logging import setup_logging
from .utils import (
    USERNAME_PATTERN,
    convert_msg,
    is_bob_alive,
    markdown_to_slack,
    strip_msg,
)

API_URL = httpx.URL(str(settings.kbs_endpoint))
"""API URL til KBS systemet"""

# Set opp logging med structlog
setup_logging()

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
    log = structlog.get_logger("slackbob").bind(
        channel=event.get("channel"),
        thread_ts=event.get("thread_ts"),
        ts=event.get("ts"),
        user=event.get("user"),
    )
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
        log.info("'/is_alive' endepunktet til KBS-en svarte ikke")
        update_msg(text="Kunnskapsbasen kjører ikke akkurat nå :construction:")
        return
    # Hent ut chat historikk og spørsmål fra brukeren
    history = [convert_msg(msg) for msg in chat_hist.get("messages")[:-1]]  # type: ignore[index]
    question = strip_msg(event["text"])
    reply = {}
    # Send spørsmål til NKS KBS
    request_id = uuid.uuid4().hex
    try:
        log = log.bind(request_id=request_id)
        with httpx.stream(
            "POST",
            API_URL.copy_with(path="/api/v1/stream/chat"),
            headers={
                "Authorization": f"Bearer {auth.get_token().get_secret_value()}",
                "X-Request-ID": request_id,
            },
            json={"history": history, "question": question},
            timeout=settings.answer_timeout,
        ) as r:
            if r.status_code != 200:
                log.error(
                    "KBS svarte ikke som forventet",
                    status_code=r.status_code,
                    reason=r.reason_phrase,
                )
                update_msg(
                    text=f"Ånei! Noe gikk galt for kunnskapsbasen :scream: (ID: {request_id})"
                )
                return
            # Brukes for å rate-limit oppdateringer til Slack. Ved for hyppig
            # oppdatering feiler Slack å oppdatere meldinger
            last_update = datetime.datetime.now()
            log.info("Strømmer svar til bruker")
            for line in r.iter_lines():
                if line.startswith("data: "):
                    _, data = line.split(" ", maxsplit=1)
                    reply = json.loads(data)
                    now = datetime.datetime.now()
                    if (
                        reply["answer"].get("text", None)
                        and now - last_update >= settings.update_rate_limit
                    ):
                        last_update = now
                        update_msg(
                            text=markdown_to_slack(reply["answer"]["text"]),
                            blocks=message_blocks(reply),
                        )
    except httpx.ReadTimeout:
        log.error(
            "Spørring mot kunnskapbasen tok for lang tid",
            timeout=settings.answer_timeout,
        )
        update_msg(text=f"Kunnskapsbasen svarer ikke (ID: {request_id}) :shrug:")
        return
    except json.decoder.JSONDecodeError as e:
        log.error(
            "Klarte ikke å dekode JSON svar fra KBS", kbs_data=data, exception=str(e)
        )
        update_msg(text=f"Kunnskapsbasen snakker i tunger (ID: {request_id}) :ghost:")
        return
    log.info("Svarer bruker fra KBS")
    # Hent respons fra KBS og formater det for Slack
    update_msg(
        text=markdown_to_slack(reply["answer"]["text"]), blocks=message_blocks(reply)
    )


@app.event("app_mention")
def slack_mention(event: dict[str, str], client: WebClient) -> None:
    """Håndter @bot meldinger på Slack."""
    structlog.get_logger("slackbob").info(
        "App mention fra bruker",
        channel=event.get("channel"),
        thread_ts=event.get("thread_ts"),
        ts=event.get("ts"),
        user=event.get("user"),
    )
    chat(client, event)


@app.event("message")
def thread_reply(event: dict[str, str], client: WebClient) -> None:
    """Håndter svar i tråder boten har besvart."""
    log = structlog.get_logger("slackbob").bind(
        channel=event.get("channel"),
        channel_type=event.get("channel_type"),
        message_type=event.get("type"),
        subtype=event.get("subtype"),
        thread_ts=event.get("thread_ts"),
        ts=event.get("ts"),
        user=event.get("user"),
    )
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
        log.info("Direkte melding fra bruker")
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
    log.info("Oppfølgningsspørsmål i tråd")
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
