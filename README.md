# Sounding Plot Bot

## Overview

The Sounding Plot Bot is a Telegram bot that generates atmospheric radio sounding plots for various stations using an R script. Users can request sounding plots by specifying the station name and the desired date and time.

## Features

- Generate sounding plots for specified weather stations and times.
- List available weather stations.
- Simple and intuitive commands to interact with the bot.

## Commands

- `/start`: Start the bot and get a welcome message with usage instructions.
- `/sounding <station> <yy> <mm> <dd> <hh>`: Generate a sounding plot for the specified station and date/time.
- `/stations`: List all available stations that can be used with the bot.

## Installation

### Prerequisites

- Docker

### Setup

1. Clone the repository or download the script files.

2. Build the Docker image:
    ```sh
    docker build -t sounding-plot-bot .
    ```

3. Run the Docker container:
    ```sh
    docker run -d --name sounding-plot-bot sounding-plot-bot
    ```

### Configuration

1. Obtain your Telegram bot token from [BotFather](https://core.telegram.org/bots#botfather) on Telegram.

2. Modify the `telegram_bot.py` file to replace the placeholder token with your actual Telegram bot token:
    ```python
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()
    ```

## Usage

1. Start a chat with your bot on Telegram.

2. Use the `/start` command to get started and see the usage instructions.

3. Use the `/sounding` command followed by the station name and date/time parameters to generate a sounding plot. Example:
    ```
    /sounding Stuttgart 2023 07 01 12
    ```

4. Use the `/stations` command to list all available stations.

## Example

1. Start the bot:
    ```
    /start
    ```

    Response:
    ```
    Hi! Use /sounding <station> <yy> <mm> <dd> <hh> to get the sounding plot.
    ```

2. List available stations:
    ```
    /stations
    ```

    Response:
    ```
    Available stations:
    Stuttgart
    Munich
    Milano
    Payerne
    Pietro
    LIPI
    Meiningen
    Lindenberg
    Essen
    LIRE
    Prag
    ```

3. Generate a sounding plot for Stuttgart on July 1, 2023, at 12 UTC:
    ```
    /sounding Stuttgart 2023 07 01 12
    ```

    Response:
    ```
    Sounding plot generated successfully.
    [Plot Image]
    ```

## Error Handling

- If an unknown station is provided:
    ```
    Unknown station: <station>
    ```
- If the sounding plot generation fails:
    ```
    Failed to generate the sounding plot.
    ```
- If an invalid command format is used:
    ```
    Usage: /sounding <station> <yy> <mm> <dd> <hh>
    ```

## Acknowledgements

This project makes use of the [thundeR](https://github.com/bczernecki/thundeR) package. Special thanks to its contributors for their valuable work.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

The thundeR package is licensed under its own terms, which can be found in its [repository](https://github.com/bczernecki/thundeR).
