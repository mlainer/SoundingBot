# 🎈 SoundingBot

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)
![R](https://img.shields.io/badge/R-thundeR-276DC3?logo=r&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-bot-26A5E4?logo=telegram&logoColor=white)

A Telegram bot that draws **atmospheric sounding plots** (Skew-T, hodograph and convective parameters) for European radiosonde stations. Send a station, a date and a parcel type, and the bot replies with the plot as an image file in full resolution (tap it to open; sending it as a Telegram photo would take about a minute and downscale it).

> Unofficial hobby project for weather enthusiasts. Plots are for information only and not a substitute for official forecasts or warnings.

## Contents

- [Features](#features)
- [Commands](#commands)
- [Quick start (Docker)](#quick-start-docker)
- [Configuration](#configuration)
- [Stations](#stations)
- [Data sources](#data-sources)
- [How it works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## Features

- Skew-T / hodograph plots with the parcel line of your choice (`MU`, `ML`, `SB` or none)
- 30 stations across Europe, addressed by name
- Payerne from Wyoming like all other stations, with an automatic fallback to MeteoSwiss data (local archive or latest sounding) if Wyoming fails
- Runs completely in Docker; no R or Python setup on the host

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with the help text |
| `/help` | Shows the usage and examples |
| `/stations` | Lists all available stations |
| `/sounding <station> <year> <mm> <dd> <hh> <parcel>` | Generates the plot |

Arguments of `/sounding`:

| Argument  | Meaning                                              | Example    |
|-----------|------------------------------------------------------|------------|
| `station` | Station name from `/stations` (upper/lower case does not matter) | `Stuttgart`|
| `year`    | 4-digit year                                         | `2024`     |
| `mm dd`   | Month and day                                        | `07 01`    |
| `hh`      | Hour in UTC (usually `00` or `12`)                   | `12`       |
| `parcel`  | `MU` most unstable, `ML` mixed layer, `SB` surface-based, `none` for no parcel line | `MU` |

Example:

```
/sounding Stuttgart 2024 07 01 12 MU
```

Typical replies:

| Situation | Reply |
|-----------|-------|
| Success | The plot as a PNG file (2000×1200 px) with a caption (station, time, parcel) |
| Wrong or incomplete arguments, unknown station or parcel, invalid date | A short explanation of the problem followed by the help text |
| Unknown command or plain text in a private chat | `Sorry, I did not understand that.` followed by the help text |
| No data or plotting failed | `Failed to generate the sounding plot.` |

## Quick start (Docker)

You need Docker and a Telegram bot token from [@BotFather](https://t.me/BotFather) (`/newbot`).

```bash
git clone https://github.com/mlainer/SoundingBot.git
cd SoundingBot
cp .env.example .env        # put your token into .env
docker compose up -d --build
docker compose logs -f      # Ctrl+C leaves the log view, the bot keeps running
```

The first build takes a while because R and thundeR are compiled.

Without Compose:

```bash
docker build -t sounding-plot-bot .
docker run -d --name sounding-plot-bot --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN=<your-token> sounding-plot-bot
```

### Alternative: run with the code mounted from the host

Mounting the project folder over `/app` lets you change the scripts without rebuilding the image (a restart is enough). The `/data` volume is optional and only provides the local Payerne archive (`/data/Soundings`) for the fallback.

```bash
docker run -d --name sounding-plot-bot --restart unless-stopped \
  --env-file .env \
  --volume "$(pwd)":/app \
  --volume /path/to/data:/data \
  sounding-plot-bot
```

If you used this setup with a `mysecret.py` (`API_TOKEN = "..."`) in the project folder, it keeps working. Plots are then written to `soundings/` in that folder.

## Configuration

| Setting | Required | Description |
|---------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | yes | Bot token from @BotFather, passed as environment variable (via `.env` with Compose) |
| `/data/Soundings` (volume) | no | Local Payerne archive (files named `YYYYMMDD-HH_PAY.csv`), only used by the MeteoSwiss fallback. See the commented volume in [docker-compose.yml](docker-compose.yml) |

For older setups a `mysecret.py` containing `API_TOKEN = "..."` is still used if the environment variable is not set. Never commit your token: `.env` and `mysecret.py` are listed in `.gitignore`.

Anyone who finds your bot can use it. Keep the bot's username private or add a user check if you run it for a closed group.

## Stations

Use the name as written (case does not matter). WMO IDs are the radiosonde station numbers.

| Station | WMO | Station | WMO | Station | WMO |
|---------|-----|---------|-----|---------|-----|
| Athens | 16716 | Lindenberg | 10393 | Prag | 11520 |
| Belgrade | 13275 | Lipi | 16045 | Rome | 16242 |
| Bucharest | 15420 | Lire | 16245 | Sodankyla | 2836 |
| Budapest | 12843 | Lyon | 7481 | Stuttgart | 10739 |
| Copenhagen | 6180 | Madrid | 8221 | Toulouse | 7630 |
| Dublin | 3918 | Meiningen | 10548 | Valentia | 3953 |
| Essen | 10410 | Milano | 16064 | Vienna | 11035 |
| Idar-Oberstein | 10618 | Munich | 10868 | Zagreb | 14240 |
| Jokioinen | 2963 | Nimes | 7645 | Payerne | 6610 (06610) |
| Legionowo | 12374 | Nottingham | 3377 | Pietro | 16144 |

`Lipi` and `Lire` are named after the ICAO codes of Udine and Pratica di Mare, and `Pietro` is San Pietro Capofiume. To add a station, extend `station_to_wmo_id` in [telegram_bot.py](telegram_bot.py).

## Data sources

- **Most stations:** the University of Wyoming sounding archive, fetched with `sounding_wyoming()` from the R package [climate](https://github.com/bczernecki/climate).
- **Payerne:** also from Wyoming (WMO 06610). If that request fails, the bot falls back to [MeteoSwiss open data](https://opendata.swiss) (`VZUS01.csv`): it uses the local archive file for the requested time, or otherwise downloads the latest sounding and plots that one. In the fallback case the plot title shows the real date and time, which may differ from the requested one.

Availability depends on these external services. If one is down, the plot cannot be generated.

## How it works

```
Telegram  -->  telegram_bot.py  -->  Rscript sounding_script.R  -->  PNG  -->  Telegram
                (python-telegram-bot)   (Wyoming, thundeR)
                          |
                          +-- Payerne only, if Wyoming fails:
                              Rscript sounding_script_pay.R (MeteoSwiss)
```

The Python bot receives the command, maps the station name to its WMO ID, runs `sounding_script.R`, and sends the resulting PNG back. For Payerne it runs `sounding_script_pay.R` if the Wyoming script fails. Plots are written to `soundings/<station>/` inside the container.

## Troubleshooting

| Problem | Hint |
|---------|------|
| Container exits right away with "Telegram token missing" | Set `TELEGRAM_BOT_TOKEN` (see [Configuration](#configuration)) |
| "Failed to generate the sounding plot." | No sounding for that station and time, or the data service is down. Check `docker compose logs` for the R error |
| "Unknown station" | Check the spelling, see `/stations` |
| Nothing happens in Telegram | Make sure only one program polls the same bot token |
| Overlapping text in the plot or `<U+00B0>` instead of `°` | The plot layout expects Helvetica-width fonts and a UTF-8 locale. The Dockerfile installs Liberation Sans and sets `LANG=C.UTF-8`; outside Docker install `fonts-liberation` and use a UTF-8 locale |

## Acknowledgements

- [thundeR](https://github.com/bczernecki/thundeR) by Bartosz Czernecki, Mateusz Taszarek and Piotr Szuster for the sounding calculations and plots
- [climate](https://github.com/bczernecki/climate) for access to the University of Wyoming sounding data
- [University of Wyoming](https://weather.uwyo.edu/upperair/sounding.html) and [MeteoSwiss](https://www.meteoswiss.admin.ch) for providing the data
- [python-telegram-bot](https://python-telegram-bot.org)

## Contributing

Issues and pull requests are welcome.

## License

[GNU General Public License v3.0](LICENSE). The R packages thundeR and climate are used under their own licenses. Sounding data belongs to its providers and is subject to their terms.
