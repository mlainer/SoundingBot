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

# Fetch the sounding profile using the passed arguments
# Define the URL and destination file path
url <- "https://data.geo.admin.ch/ch.meteoschweiz.messwerte/radiosondierungen/VZUS01.csv"
destfile <- "/app/VZUS01.csv"

# Download the CSV file
download.file(url, destfile, method = "curl")

# Load the CSV file with the correct header lines skipped and space as the separator
data <- read.csv(destfile, skip = 2, sep = " ", header = FALSE, encoding = "ISO-8859-1")

# Convert relevant columns to numeric format
pressure <- as.numeric(data[, 10])
altitude <- as.numeric(data[, 11])
temp <- as.numeric(data[, 12])
dpt <- as.numeric(data[, 14])
wd <- as.numeric(data[, 15])
ws <- as.numeric(data[, 16])

# Create the profile data frame with numeric columns
profile <- data.frame(
  pressure = pressure[2:100],   # Column 10: pressure
  altitude = altitude[2:100],   # Column 11: altitude
  temp = temp[2:100],           # Column 12: temperature
  dpt = dpt[2:100],             # Column 14: dew point temperature
  wd = wd[2:100],               # Column 15: wind direction
  ws = ws[2:100]                # Column 16: wind speed
)

# Generate filename and title based on the station and sounding time
title <- sprintf("%s - %02d %s %04d %04d UTC", station, dd, month.abb[mm], yy, hh * 100)

# Save the sounding profile to a file
sounding_save(filename = filename, title = title,
              parcel = myparcel, SRH_polygon = "03km",
              profile$pressure, profile$altitude, 
              profile$temp, profile$dpt, profile$wd, profile$ws)
