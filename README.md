# Slackbot for NKS Kunnskapsbase Basert Språkmodell

![Logo av Bob](./bob.svg)

Denne slackboten representerer Bob - NAV Kontaktsenter sin Kunnskapsbase Baserte
Språkmodell.

## Bruk

Bot-en er installert i NAV-IT Slack-en og vil automatisk motta og svare på
forespørsler der når applikasjonen kjører på NAIS. Applikasjonen blir automatisk
deploy-et til NAIS ved hjelp av [en Github
Action](.github/workflows/build_deploy.yml) og man trenger ikke å foreta seg noe
mer enn å passe på at deploy fungerte.

## Utvikling

Prosjektet bruker [`uv`](https://docs.astral.sh/uv/) og man kan installere
prosjektet, og avhengigheter, med:

```bash
uv sync --frozen
```

> [!IMPORTANT]
> Pass på å aktivere `pre-commit` med `uv run pre-commit install` første gang
> man kloner prosjektet. Dette gir en ekstra sikkerhet for at kodekvalitet blir
> vedlikeholdt mellom forskjellige maskiner, IDE-er og utviklerverktøy.

Applikasjonen kjører ikke lokalt da den er avhengig av autentisering mot
[`nks_kbs`](https://github.com/navikt/nks_kbs).

### Testing

For funksjonaliteten som kan testes lokalt finnes det enkle tester i
[`./tests`](./tests/).

Disse kan kjøres med:

```bash
uv run pytest
```

> [!TIP]
> Prosjektet inneholder en [`justfile`](https://github.com/casey/just) som
> automatiserer en del enkle oppgaver.
>
> Man kan for eksempel få `ruff` til å fikse koden ved å kjøre `just fix`.
