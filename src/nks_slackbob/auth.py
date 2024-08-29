"""Autentisering i Entra ID på NAIS."""

import dataclasses
import datetime
from typing import Annotated, Any, cast

import httpx
from pydantic import AnyHttpUrl, SecretStr, UrlConstraints
from pydantic.dataclasses import dataclass
from pydantic_core import Url

ApiUrl = Annotated[Url, UrlConstraints(allowed_schemes=["api"])]
"""Type URL som beskriver et OAuth2 scope"""


@dataclass
class OAuth2Flow:
    """Håndter OAuth2 autentiseringsflyt.

    Klassen håndterer applikasjon til applikasjons flyten beskrevet her:
    https://doc.nais.io/auth/entra-id/how-to/consume-m2m/#acquire-token
    """

    client_id: str
    """Klient ID for applikasjonen som kaller"""

    client_secret: SecretStr
    """Klient hemmelighet for applikasjonen"""

    token_endpoint: AnyHttpUrl
    """Endepunkt for å hente autentiseringstoken"""

    scope: ApiUrl
    """Scope for autentiseringstoken"""

    _token: dict[str, Any] = dataclasses.field(default_factory=dict)
    """Privat lager for autentiseringstoken"""

    def _acquire_token(self) -> dict[str, Any]:
        """Hent autentiseringstoken fra Azure Entra ID på NAIS."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret.get_secret_value(),
            "scope": str(self.scope),
            "grant_type": "client_credentials",
        }
        response = httpx.post(str(self.token_endpoint), data=data).raise_for_status()
        json: dict[str, Any] = response.json()
        return json

    @property
    def last_update(self) -> datetime.datetime | None:
        """Hent tidspunkt for siste oppfriskning.

        Metoden returnerer `None` hvis det aldri er utført en oppfriskning
        """
        return self._token.get("last_update")

    @property
    def expires(self) -> datetime.datetime | None:
        """Hent tidspunkt for når autentiseringstoken utløper.

        Metoden returnerer `None` hvis det aldri er utført en oppfriskning
        """
        if self.last_update is None:
            return None
        return self.last_update + datetime.timedelta(seconds=self._token["expires_in"])

    def __call__(self) -> SecretStr:
        """Hent autentiseringstoken.

        Metoden kaller ut til `self.get_token()`.
        """
        return self.get_token()

    def get_token(self) -> SecretStr:
        """Hent autentiseringstoken.

        Denne metoden vil ha variabel latens ettersom autentiseringstoken må
        oppfriskes fra gang til gang. Dette gjør at henting av token mellom
        oppfriskninger går fort, men ved oppfriskning må det kalles ut for å
        hente nytt token.
        """
        # Trenger ikke å bry oss om tidssone, så lenge vi er internt konsekvente
        now = datetime.datetime.now(datetime.UTC)
        if (
            not self.last_update
            or (
                # MERK: `self.expires` vil alltid være definert hvis
                # 'self.last_update' er definert
                cast(datetime.datetime, self.expires) - datetime.timedelta(seconds=5)
                # Trekk fra litt for å unngå overlapp
            )
            < now
        ):
            self._token = self._acquire_token()
            self._token["last_update"] = now
        return SecretStr(self._token["access_token"])
