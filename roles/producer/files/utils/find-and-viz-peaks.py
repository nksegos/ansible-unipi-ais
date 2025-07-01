#!/usr/bin/env python3

import re
import argparse
import sys
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

parser = argparse.ArgumentParser("find-and-viz-peaks.py")
parser.add_argument("-i", "--input-path", required=True, help="Path to the input CSV file(or dir containing CSV files, if running with --dir-mode) to be used.")
parser.add_argument("--dir-mode", action='store_true', help="Use this option to apply the checks to all csv files in the input path.")
parser.add_argument("--no-header", action='store_true', help="Use this option if the input file does not contain a header row.")
parser.add_argument("--headless", action='store_true', help="Use to limit text output only to $filename|$peak_hour.")
parser.add_argument("-c", "--column", default=0, help="The timestamp column index.")
parser.add_argument("-o", "--output-dir", required=True, help="Path to the directory where the output plots will be saved.")

args = parser.parse_args()

def dir_files_by_month(filename):
    regex_match = re.search(r"([A-Za-z]{3})(\d{4})", filename.name)
    if not regex_match:
        return (0, 0)
    mon, year = regex_match.groups()
    dt = datetime.strptime(mon, "%b")
    return (int(year), dt.month)

if args.dir_mode:
    search_space = sorted(Path(args.input_path).glob('*.csv'), key=dir_files_by_month) 
else:
    search_space = [Path(args.input_path)]

tz = ZoneInfo('Europe/Athens')

chunk_size = 1000000

file_peak_counts = {}

header_val=0 if not args.no_header else None

try:
    for file in search_space:
        if not args.headless:
            print(f"Processing file {file.name}...")
        hour_counts = {}
        for chunk in pd.read_csv(file, usecols=[int(args.column)], chunksize=chunk_size, header=header_val, names=['t']):
            chunk['hour'] = pd.to_datetime(chunk['t'], unit='ms', utc=True)
            chunk['hour'] = chunk['hour'].dt.tz_convert(tz).dt.floor('h', ambiguous=True)
            counts = chunk['hour'].value_counts()

            for time, count in counts.items():
                hour_counts[time] = hour_counts.get(time, 0) + count

        max_hour = max(hour_counts, key=hour_counts.get)
        file_peak_counts[str(file)] = {'dt': max_hour.strftime('%a, %d %b %Y %H:%M:%S %Z(%z)'), 'cnt': hour_counts[max_hour] }
        if not args.dir_mode:
            if not args.headless:
                print(f"The hour with the most rows is: {max_hour.strftime('%a, %d %b %Y %H:%M:%S %Z(%z)')} with {hour_counts[max_hour]} rows.")
            else:
                print(f"{file}|{max_hour.strftime('%a, %d %b %Y %H:%M:%S %Z(%z)')}")

    if args.dir_mode:
        peak_file, peak_dt = max(file_peak_counts.items(), key=lambda item: item[1]['cnt'])
        if not args.headless:
            print(f"The hour with the most rows is: {peak_dt['dt']} with {peak_dt['cnt']} rows from file: {peak_file}")
        else:
            print(f"{peak_file}|{peak_dt['dt']}")


    plt.figure(figsize=(10, 6))
    peak_dates = [file_peak_counts[fn]['dt'] for fn in file_peak_counts.keys()] 
    counts = [file_peak_counts[fn]['cnt'] for fn in file_peak_counts.keys()]

    if args.dir_mode:
        year = re.search(r"(\d{4})", Path(args.input_path).name).groups()[0]
        month = ''
        plt.bar(peak_dates, counts)
        plt.xticks(rotation=45, ha='right')
        plt.title(f"AIS message traffic peaks(hourly resolution) by month - {year}")
        plt.xlabel("Peak traffic date & hour")
        plt.ylabel("Count of kinematic AIS messages")
        plt.xlim((-0.5, len(peak_dates)-0.5))
        plt.tight_layout()
    else:
        month, year = re.search(r"([A-Za-z]{3})(\d{4})", Path(args.input_path).name).groups()
        plt.bar(peak_dates, counts)
        plt.xticks(rotation=45, ha='right')
        plt.title(f"AIS message traffic peak(hourly resolution) on {month} {year}")
        plt.xlabel("Peak traffic date & hour")
        plt.ylabel("Count of kinematic AIS messages")
        plt.xlim((-0.5, len(peak_dates)-0.5))
        plt.tight_layout()       


    if args.output_dir[-1] == '/':
        plt.savefig(f"{args.output_dir}{month}{year}_peaks.png")
    else:
        plt.savefig(f"{args.output_dir}/{month}{year}_peaks.png")
    
    sys.exit(0)

except Exception as e:

    print(f"An error has occured:{e}")
    sys.exit(1)

