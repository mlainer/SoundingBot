import asyncio
import logging
import subprocess
import os
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("sounding_bot")

# Token from the environment; falls back to a local mysecret.py (API_TOKEN) for older setups
API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    try:
        from mysecret import API_TOKEN
    except ImportError:
        raise SystemExit("Telegram token missing: set the TELEGRAM_BOT_TOKEN environment variable.")

# Define the mapping from station names to WMO IDs
station_to_wmo_id = {
    "Athens": 16716,
    "Belgrade": 13275,
    "Bucharest": 15420,
    "Budapest": 12843,
    "Copenhagen": 6180,
    "Dublin": 3918,
    "Essen": 10410,
    "Idar-Oberstein": 10618,
    "Jokioinen": 2963,
    "Legionowo": 12374,
    "Lindenberg": 10393,
    "Lipi": 16045,
    "Lire": 16245,
    "Lyon": 7481,
    "Madrid": 8221,
    "Meiningen": 10548,
    "Milano": 16064,
    "Munich": 10868,
    "Nimes": 7645,
    "Nottingham": 3377,
    "Payerne": 6610,
    "Pietro": 16144,
    "Prag": 11520,
    "Rome": 16242,
    "Sodankyla": 2836,
    "Stuttgart": 10739,
    "Toulouse": 7630,
    "Valentia": 3953,
    "Vienna": 11035,
    "Zagreb": 14240,
}

# Function to call the sounding script
def call_sounding_script(station, yy, mm, dd, hh, myparcel):
    if station not in station_to_wmo_id:
        raise ValueError(f"Unknown station: {station}")
    
    wmo_id = station_to_wmo_id[station]

    # Create directory structure for the station and date
    directory = os.path.join("soundings", station)
    os.makedirs(directory, exist_ok=True)

    # Wyoming first; Payerne falls back to the MeteoSwiss script (local archive or latest sounding)
    scripts = ["sounding_script.R"]
    if station == "Payerne":
        scripts.append("sounding_script_pay.R")

    filename = os.path.join(directory, f"{station}_{yy}{mm:02d}{dd:02d}_{hh:02d}00UTC.png")
    for script in scripts:
        command = [
            "Rscript", script,
            station, str(wmo_id), str(yy), str(mm), str(dd), str(hh), str(myparcel), filename
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print(f"R script output ({script}): {result.stdout}")
            return filename
        except subprocess.CalledProcessError as e:
            print(f"Error executing {script}: {e.stderr}")
        except Exception as e:
            print(f"Error running {script}: {str(e)}")
    return None

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Hi! Use /sounding <station> <year> <mm> <dd> <hh> <parcel> to get the sounding plot.\n'
        'Parcel: MU, ML, SB or none. Example: /sounding Stuttgart 2024 07 01 12 MU\n'
        'List stations with /stations.')

# Command handler for /sounding
async def sounding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        args = context.args
        if len(args) != 6:
            await update.message.reply_text('Usage: /sounding <station> <year> <mm> <dd> <hh> <parcel: MU|ML|SB|none>')
            return
        
        station = args[0]
        yy = int(args[1])
        mm = int(args[2])
        dd = int(args[3])
        hh = int(args[4])
        myparcel = args[5]

        # Run R in a worker thread so the bot's event loop (Telegram polling) is not blocked
        filename = await asyncio.to_thread(call_sounding_script, station, yy, mm, dd, hh, myparcel)
        if filename:
            await update.message.reply_text('Sounding plot generated successfully.')
            # Uploads can take a while; the default 5 s read timeout produced "Timed out" errors
            with open(filename, 'rb') as photo:
                await update.message.reply_photo(
                    photo=InputFile(photo),
                    read_timeout=60, write_timeout=60, connect_timeout=30, pool_timeout=30)
        else:
            await update.message.reply_text('Failed to generate the sounding plot.')
    except Exception as e:
        logger.exception("sounding command failed")
        await update.message.reply_text(f'Error: {str(e)}')

# Command handler for /stations
async def stations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    station_list = "\n".join(station_to_wmo_id.keys())
    await update.message.reply_text(f"Available stations:\n{station_list}")

def main() -> None:
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(API_TOKEN)
        .read_timeout(30).write_timeout(30).connect_timeout(30).pool_timeout(30)
        .build()
    )

    # Add command handler to start the bot
    application.add_handler(CommandHandler("start", start))

    # Add command handler for sounding
    application.add_handler(CommandHandler("sounding", sounding))

    # Add command handler for stations
    application.add_handler(CommandHandler("stations", stations))

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    application.run_polling()

if __name__ == '__main__':
    main()
