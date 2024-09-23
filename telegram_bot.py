import subprocess
import os
import mysecret
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes

# Define the mapping from station names to WMO IDs
station_to_wmo_id = {
    "Stuttgart": 10739,
    "Munich": 10868,
    "Milano": 16064,
    "Payerne": 66800,
    "Pietro": 16144,
    "LIPI": 16045,
    "Meiningen": 10548,
    "Lindenberg": 10393,
    "Essen": 10410,
    "LIRE": 16245,
    "Prag": 11520 
}

# Function to call the sounding script
def call_sounding_script(station, yy, mm, dd, hh, myparcel):
    if station not in station_to_wmo_id:
        raise ValueError(f"Unknown station: {station}")
    
    wmo_id = station_to_wmo_id[station]

    # Create directory structure for the station and date
    directory = os.path.join("soundings", station)
    os.makedirs(directory, exist_ok=True)

    # Construct the filename and command to call the R script with the arguments
    if station == "Payerne":
        filename = os.path.join(directory, f"{station}_{yy}{mm:02d}{dd:02d}_{hh:02d}00UTC.png")
        command = [
            "Rscript", "sounding_script_pay.R", 
            station, str(wmo_id), str(yy), str(mm), str(dd), str(hh), str(myparcel), filename
        ]
    else:    
        filename = os.path.join(directory, f"{station}_{yy}{mm:02d}{dd:02d}_{hh:02d}00UTC.png")
        command = [
            "Rscript", "sounding_script.R", 
            station, str(wmo_id), str(yy), str(mm), str(dd), str(hh), str(myparcel), filename
        ]

    try:
        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"R script output: {result.stdout}")
        return filename
    except subprocess.CalledProcessError as e:
        print(f"Error executing R script: {e.stderr}")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hi! Use /sounding <station> <yy> <mm> <dd> <hh> to get the sounding plot.')

# Command handler for /sounding
async def sounding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        args = context.args
        if len(args) != 6:
            await update.message.reply_text('Usage: /sounding <station> <yy> <mm> <dd> <hh> <parcel_type>')
            return
        
        station = args[0]
        yy = int(args[1])
        mm = int(args[2])
        dd = int(args[3])
        hh = int(args[4])
        myparcel = args[5]

        # Call the sounding script
        filename = call_sounding_script(station, yy, mm, dd, hh, myparcel)
        if filename:
            await update.message.reply_text('Sounding plot generated successfully.')
            with open(filename, 'rb') as photo:
                await update.message.reply_photo(photo=InputFile(photo))
        else:
            await update.message.reply_text('Failed to generate the sounding plot.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

# Command handler for /stations
async def stations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    station_list = "\n".join(station_to_wmo_id.keys())
    await update.message.reply_text(f"Available stations:\n{station_list}")

def main() -> None:
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(mysecret.API_TOKEN).build()

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
