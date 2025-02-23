#!/usr/bin/env Rscript

# Load the necessary library
library(thunder)

# Read command line arguments
args <- commandArgs(trailingOnly = TRUE)

# Assign command line arguments to variables
station <- args[1]
wmo_id <- as.integer(args[2])
yy <- as.integer(args[3])
mm <- as.integer(args[4])
dd <- as.integer(args[5])
hh <- as.integer(args[6])
myparcel <- args[7]
filename <- args[8]

# Define the directory where Payerne soundings are stored inside the Docker container
sounding_dir <- "/app/data/Soundings"

# Construct the expected filename
requested_file <- sprintf("%04d%02d%02d-%02d_PAY.csv", yy, mm, dd, hh)

# Full path to the requested file inside the container
file_path <- file.path(sounding_dir, requested_file)

# Default to the requested date/time
actual_yy <- yy
actual_mm <- mm
actual_dd <- dd
actual_hh <- hh

# Check if the file exists, otherwise download the latest sounding
if (!file.exists(file_path)) {
  cat(sprintf("Warning: Sounding file %s not found. Downloading latest available data...\n", requested_file))
  
  # Define the URL and temporary destination file inside the container
  url <- "https://data.geo.admin.ch/ch.meteoschweiz.messwerte/radiosondierungen/VZUS01.csv"
  temp_file <- "/app/VZUS01.csv"
  
  # Download the latest CSV file
  download.file(url, temp_file, method = "curl")
  
  # Use the downloaded file instead
  file_path <- temp_file
  
  # Read the first few rows to extract the correct timestamp (skip first 2 lines)
  latest_data <- read.csv(temp_file, skip = 2, sep = " ", header = FALSE, encoding = "ISO-8859-1")
  
  # Extract the timestamp from the second column of the third row (first data row)
  latest_timestamp <- as.character(latest_data[1, 2])  # Example: "202407041200"

  if (!is.na(latest_timestamp) && nchar(latest_timestamp) == 12) {
    actual_yy <- as.integer(substr(latest_timestamp, 1, 4))   # 2024
    actual_mm <- as.integer(substr(latest_timestamp, 5, 6))   # 07
    actual_dd <- as.integer(substr(latest_timestamp, 7, 8))   # 04
    actual_hh <- as.integer(substr(latest_timestamp, 9, 10))  # 12
  }
}

# Read the CSV file
data <- read.csv(file_path, skip = 2, sep = " ", header = FALSE, encoding = "ISO-8859-1")

# Convert relevant columns to numeric format
pressure <- as.numeric(data[, 10])
altitude <- as.numeric(data[, 11])
temp <- as.numeric(data[, 12])
dpt <- as.numeric(data[, 14])
wd <- as.numeric(data[, 15])
ws <- as.numeric(data[, 16])

# Create the profile data frame
profile <- data.frame(
  pressure = pressure[2:100],   # Column 10: pressure
  altitude = altitude[2:100],   # Column 11: altitude
  temp = temp[2:100],           # Column 12: temperature
  dpt = dpt[2:100],             # Column 14: dew point temperature
  wd = wd[2:100],               # Column 15: wind direction
  ws = ws[2:100]                # Column 16: wind speed
)

# Generate the correct title with the actual date (either requested or latest downloaded)
title <- sprintf("%s - %02d %s %04d %04d UTC", station, actual_dd, month.abb[actual_mm], actual_yy, actual_hh * 100)

# Save the sounding profile to a file
sounding_save(filename = filename, title = title,
              parcel = myparcel, SRH_polygon = "03km",
              profile$pressure, profile$altitude, 
              profile$temp, profile$dpt, profile$wd, profile$ws)

cat(sprintf("Successfully processed and saved: %s\n", filename))