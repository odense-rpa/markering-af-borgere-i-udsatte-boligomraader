## Markering af borgere i udsatte boligområder

Automatisering der identificerer og markerer nye borgere i Odense Kommunes udsatte boligområder i KMD Momentum, samt tildeler den ansvarlige sagsbehandler og opretter en opfølgningsopgave.

## Hvad gør robotten?

1. **Henter borgere** fra KMD Momentum med målgruppe 6.1 eller 6.2, der har fået oprettet målgruppen inden for de seneste 15 dage
2. **Kontrollerer adresse** mod en Excel-liste (`Boligadresser.xlsx`) over adresser i udsatte boligområder — borgere uden matchende adresse springes over
3. **Springer over** borgere, der allerede har fået oprettet en relevant opgave inden for de seneste 30 dage
4. **Finder passende markering** baseret på borgerens adresse og uddannelsesniveau
5. **Tildeler sagsbehandler** baseret på borgerens målgruppe og opretter en opgave til denne
6. **Opretter markering** i Momentum, hvis borgeren ikke allerede har en aktiv markering med samme navn
7. **Registrerer aktivitet** via ODK-aktivitetssporing

## Forudsætninger

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
- Adgang til **Automation Server** (arbejdskø)
- Adgang til **KMD Momentum** (produktion)
- En **Odense SQL Server**-konto til aktivitetssporing

## Installation

```sh
uv sync
```

## Konfiguration

Kopiér `.env.example` til `.env` og udfyld følgende:

| Variabel | Beskrivelse |
|---|---|
| `ATS_URL` | URL til Automation Server API |
| `ATS_TOKEN` | API-token til Automation Server |

Følgende legitimationsoplysninger skal være opsat i Automation Server Credentials:

| Navn | Beskrivelse |
|---|---|
| `Momentum - produktion` | Klient-id, klient-hemmelighed og API-nøgle til KMD Momentum |
| `Odense SQL Server` | Brugernavn og adgangskode til ODK-aktivitetssporing |

## Kørsel

```sh
# Fyld arbejdskøen med nye borgere fra Momentum
uv run python main.py --queue

# Behandl arbejdskøen
uv run python main.py
```

### Argumenter

| Argument | Beskrivelse |
|---|---|
| `--excel-file <sti>` | Tilsidesæt stien til `Boligadresser.xlsx` (standard: `./Boligadresser.xlsx`) |
| `--queue` | Fyld arbejdskøen og afslut — kør ingen behandling |

## Adresseliste (`Boligadresser.xlsx`)

Excel-filen indeholder to kolonner:

- **Adresse** – Fuld gadenavn og husnummer for adresser i udsatte boligområder
- **Markering** – Det markeringsnavn, der skal oprettes i Momentum for den pågældende adresse (uddannelsessuffix tilføjes automatisk)

Filen må **ikke** committes til dette repository, da den kan indeholde følsomme oplysninger om geografiske risikoområder.

## Afhængigheder

| Pakke | Formål |
|---|---|
| `automation-server-client` | Arbejdskø-håndtering via Automation Server |
| `momentum-client` | Integration med KMD Momentum |
| `odk-tools` | Aktivitetssporing |
| `openpyxl` | Læsning af Excel-adresseliste |

## Persondatasikkerhed

Robotten behandler personoplysninger på vegne af Odense Kommune, herunder CPR-numre, adresseoplysninger og sociale klassifikationer (målgruppe 6.1/6.2).

- **Ingen personoplysninger** må lægges i dette repository — hverken som testdata, i kode eller i kommentarer
- `Boligadresser.xlsx` er ekskluderet via `.gitignore` og må aldrig committes
- Legitimationsoplysninger håndteres udelukkende via miljøvariabler (`.env`) og Automation Server Credentials
- Robotten læser og skriver udelukkende data i de fagsystemer, der er nødvendige for opgavens udførelse (KMD Momentum og ODK-sporing)
- Behandlingen sker på lovhjemlet grundlag som led i kommunens beskæftigelsesindsats — der foretages ingen videregivelse til tredjeparter

