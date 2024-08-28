"""Innstillinger for prosjektet."""

from pydantic import HttpUrl, SecretStr
from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Innstillinger fra miljøvariabler."""

    model_config = SettingsConfigDict(
        env_prefix="nks_slackbob_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: SecretStr
    """Slack bot token"""

    app_token: SecretStr
    """Slack app token"""

    id: str = "A075RP88EV8"
    """Slack app id til boten"""

    kbs_endpoint: HttpUrl = Url("http://nks-kbs")
    """Endepunkt for NKS KBS"""

    answer_timeout: float = 60.0
    """Tidsbegrensning, i sekunder, på hvor lenge vi venter på et svar fra modellen før vi gir opp"""


# MERK: Vi ignorerer 'call-arg' for mypy ved instansiering på grunn av følgende
# bug: https://github.com/pydantic/pydantic/issues/6713
settings = Settings()  # type: ignore[call-arg]
"""Instansiering av konfigurasjon som burde benyttes for å hente innstillinger"""
