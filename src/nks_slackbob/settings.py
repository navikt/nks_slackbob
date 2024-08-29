"""Innstillinger for prosjektet."""

from pydantic import AliasChoices, AnyHttpUrl, Field, SecretStr
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

    id: str = "A07JWHE9458"
    """Slack app id til boten"""

    kbs_endpoint: AnyHttpUrl = Url("http://nks-kbs")
    """Endepunkt for NKS KBS"""

    answer_timeout: float = 60.0
    """Tidsbegrensning, i sekunder, på hvor lenge vi venter på et svar fra modellen før vi gir opp"""

    # Variabler vi trenger for autentisering
    client_id: str = Field(validation_alias=AliasChoices("azure_app_client_id"))
    """Klient ID for applikasjonen - brukes for autentisering"""

    client_secret: SecretStr = Field(
        validation_alias=AliasChoices("azure_app_client_secret")
    )
    """Klient hemmelighet - brukes for autentisering"""

    auth_token_endpoint: AnyHttpUrl = Field(
        "http://localhost:8888/token",
        validation_alias=AliasChoices("azure_openid_config_token_endpoint"),
    )
    """Endepunkt å kalle på for å skaffe autentiseringstoken"""

    nais_environment: str = Field(
        "dev-gcp", validation_alias=AliasChoices("nais_cluster_name")
    )
    """Miljø applikasjonen kjører i - bestemmer scope for autentisering"""


# MERK: Vi ignorerer 'call-arg' for mypy ved instansiering på grunn av følgende
# bug: https://github.com/pydantic/pydantic/issues/6713
settings = Settings()  # type: ignore[call-arg]
"""Instansiering av konfigurasjon som burde benyttes for å hente innstillinger"""
