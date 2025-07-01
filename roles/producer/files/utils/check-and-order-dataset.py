#!/usr/bin/env python3

import argparse
import csv
from csvsort import csvsort
import sys

parser = argparse.ArgumentParser("check-and-order-dataset.py")
parser.add_argument("-f", "--filename", required=True, help="Path to the input CSV file to be checked for correct sorting.")
parser.add_argument("--no-header", action='store_true', help="Use this option if the input file does not contain a header row.")
parser.add_argument("-c", "--column", default=0, help="The timestamp column index to be used for ordering.")
group = parser.add_mutually_exclusive_group()
group.add_argument("--exit-on-first-unordered", action='store_true', help="Use this option to have the checker exit at the first instance of out of order timestamps.")
group.add_argument("--fix-ordering", action='store_true', help="Use this option to sort the input file inplace if timestamps are found to be out of order.")

args = parser.parse_args()

matches_found = 0
print(f"Checking for timestamp order in input file: {args.filename} - Column Index: {args.column}")
with open(args.filename, 'r', newline='') as file:
    reader = csv.reader(file)
    prev_timestamp = None
    prev_line_num = None


    if args.no_header:
        count_start = 1
    else: 
        next(reader)
        count_start = 2

    for line_num, row in enumerate(reader, start=count_start): 
        if not row:
            continue 

        timestamp = int(row[args.column])

        if prev_timestamp is not None and timestamp < prev_timestamp:
            matches_found += 1
            print(f"Timestamps out of order at line {prev_line_num}: {prev_timestamp} followed by {timestamp} on line {line_num}")
            
            if args.fix_ordering or args.exit_on_first_unordered:
                break

        prev_line_num = line_num
        prev_timestamp = timestamp

if matches_found == 0:
    print("Check completed, timestamps are in order.")
    exit_code = 0
elif ( matches_found > 0 ) and ( args.exit_on_first_unordered or args.fix_ordering ):
    print("Check completed, at least one timestamp out of order")
    if args.fix_ordering:
        print(f"Sorting input file {args.filename}...")
        try:
            csvsort(args.filename,[args.column])
            print("Sorting completed.")
            exit_code = 0
        except Exception as e:
            print(f"Sorting failed. An error has occured:{e}")
            exit_code = 1
    else:
        exit_code = 1
else:
    print(f"Check completed, {matches_found} timestamps found to be out of order")
    exit_code = 1


sys.exit(exit_code)
