import asyncio
import logging
import subprocess
import os
from datetime import datetime
from telegram import BotCommand, Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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

HELP_TEXT = (
    "SoundingBot: atmospheric sounding plots (Skew-T, hodograph, parameters)\n\n"
    "/sounding <station> <year> <mm> <dd> <hh> <parcel>\n"
    "  Example: /sounding Stuttgart 2024 07 01 12 MU\n"
    "  hh = hour in UTC (usually 00 or 12)\n"
    "  parcel = MU, ML, SB or none\n\n"
    "/stations - list available stations\n"
    "/help - show this message"
)

PARCELS = {"MU": "MU", "ML": "ML", "SB": "SB", "NONE": "none"}
STATIONS_BY_LOWER = {name.lower(): name for name in station_to_wmo_id}


def parse_sounding_args(args):
    """Validate the /sounding arguments; raises ValueError with a user-facing message."""
    if len(args) != 6:
        raise ValueError("Expected 6 arguments, got %d." % len(args))
    station = STATIONS_BY_LOWER.get(args[0].lower())
    if station is None:
        raise ValueError(f"Unknown station: {args[0]} (see /stations)")
    try:
        yy, mm, dd, hh = (int(a) for a in args[1:5])
        if not 1900 <= yy <= 2100:
            raise ValueError
        datetime(yy, mm, dd, hh)
    except ValueError:
        raise ValueError("Invalid date or time. Use a 4-digit year, e.g. 2024 07 01 12.") from None
    parcel = PARCELS.get(args[5].upper())
    if parcel is None:
        raise ValueError(f"Unknown parcel type: {args[5]} (use MU, ML, SB or none)")
    return station, yy, mm, dd, hh, parcel


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

# Command handler for /start and /help
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hi! " + HELP_TEXT)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)

# Anything that is not a known command or a plain request gets the help text
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Sorry, I did not understand that.\n\n" + HELP_TEXT)

# Command handler for /sounding
async def sounding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        station, yy, mm, dd, hh, myparcel = parse_sounding_args(context.args)
    except ValueError as e:
        await update.message.reply_text(f"{e}\n\n{HELP_TEXT}")
        return

    try:
        await update.message.chat.send_action("upload_document")
        # Run R in a worker thread so the bot's event loop (Telegram polling) is not blocked
        filename = await asyncio.to_thread(call_sounding_script, station, yy, mm, dd, hh, myparcel)
        if filename:
            # Sent as a file: Telegram needs about a minute to process these plots as photos
            # (and would downsize them to 1280 px), while a file upload takes about a second
            caption = f"{station} {yy}-{mm:02d}-{dd:02d} {hh:02d} UTC, parcel {myparcel}"
            with open(filename, 'rb') as plot:
                await update.message.reply_document(
                    document=InputFile(plot, filename=os.path.basename(filename)),
                    caption=caption,
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

async def post_init(application: Application) -> None:
    # Fills the command menu shown in Telegram
    try:
        await application.bot.set_my_commands([
            BotCommand("sounding", "Plot a sounding: <station> <year> <mm> <dd> <hh> <parcel>"),
            BotCommand("stations", "List available stations"),
            BotCommand("help", "Show help"),
        ])
    except Exception:
        logger.warning("Could not set the command menu", exc_info=True)

def main() -> None:
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(API_TOKEN)
        .read_timeout(30).write_timeout(30).connect_timeout(30).pool_timeout(30)
        .post_init(post_init)
        .build()
    )

    # Add command handler to start the bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add command handler for sounding
    application.add_handler(CommandHandler("sounding", sounding))

    # Add command handler for stations
    application.add_handler(CommandHandler("stations", stations))

    # Must stay last: unknown commands and plain text in private chats get the help text
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, unknown))

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    application.run_polling()

if __name__ == '__main__':
    main()
