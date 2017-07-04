#!/bin/sh
# Usage:
# $ bash merge-csv.sh [directory_with_csvs]

# Merge all non-header lines into merged.csv
for fname in $1/*
do 
    tail -n+2 $fname >> merged.csv;
done

# Get the unique rows by column 1, 2
awk -F"," '!seen[$1, $2]++' merged.csv > merged2.csv

# Sort the final rows in alpha order
sort merged2.csv > merged3.csv

# Rename and cleanup, commented out just in case
#rm merged.csv
#rm merged2.csv
#mv merged3.csv merged.csv

