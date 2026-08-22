#!/usr/bin/env Rscript

# Load the necessary library
library(thunder)
library(climate)

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
profile <- sounding_wyoming(wmo_id = wmo_id, yy = yy, mm = mm, dd = dd, hh = hh)
profile_data <- profile[[1]]

required_columns <- c("PRES", "HGHT", "TEMP", "DWPT", "DRCT", "SKNT")
if (!is.data.frame(profile_data) || !all(required_columns %in% names(profile_data)) || nrow(profile_data) == 0) {
    stop(sprintf("No complete sounding data available for WMO station %d at %04d-%02d-%02d %02d UTC.",
                             wmo_id, yy, mm, dd, hh))
}

# Generate filename and title based on the station and sounding time
title <- sprintf("%s - %02d %s %04d %04d UTC", station, dd, month.abb[mm], yy, hh * 100)

# Save the sounding profile to a file
sounding_save(filename = filename, title = title, 
              parcel = myparcel, SRH_polygon = "03km",
              profile_data$PRES, profile_data$HGHT,
              profile_data$TEMP, profile_data$DWPT,
              profile_data$DRCT, profile_data$SKNT)
