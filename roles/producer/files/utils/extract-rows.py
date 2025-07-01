#!/usr/bin/env python3

import pandas as pd
from datetime import datetime, timezone
import argparse
import sys

parser = argparse.ArgumentParser("extract-rows.py")
parser.add_argument("-i", "--input-file", required=True, help="Path to the input CSV file to be used.")
parser.add_argument("-t", "--from-timestamp", required=True, help="The datetime timestamp from which the row extraction should take place. Format expected: '%%a, %%d %%b %%Y %%H:%%M:%%S %%Z(%%z)'. NOTE: The extraction will floor down to the timestamp hour as a starting point.")
parser.add_argument("-r", "--time-range-hours", default=1, help="The duration of the row extraction time range in hours")
parser.add_argument("--no-header", action='store_true', help="Use this option if the input file does not contain a header row.")
parser.add_argument("-c", "--column", default=0, help="The timestamp column index.")
parser.add_argument("-o", "--output-file", default=None, help="The path to the output file that will contain the extracted rows.")

args = parser.parse_args()


try:
    input_dt = datetime.strptime(args.from_timestamp,"%a, %d %b %Y %H:%M:%S %Z(%z)").astimezone(timezone.utc)
    start_hour_utc = input_dt.replace(minute=0, second=0, microsecond=0)
    end_hour_utc = start_hour_utc + pd.Timedelta(hours=int(args.time_range_hours))

    header_val=0 if not args.no_header else None

    df = pd.read_csv(args.input_file, header=header_val)

    timestamp_col = df.columns[int(args.column)]

    timestamps = pd.to_datetime(df[timestamp_col], unit='ms', utc=True)
    mask = (timestamps >= start_hour_utc) & (timestamps < end_hour_utc)

    result = df[mask].copy()

    print(result)

    if args.output_file:
        result.to_csv(args.output_file, index=False)

    sys.exit(0)

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

