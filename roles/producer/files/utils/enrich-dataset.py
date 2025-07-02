#!/usr/bin/env python3

import pandas as pd
import argparse
import sys

parser = argparse.ArgumentParser("extract-rows.py")
parser.add_argument("-k", "--kinematic-data-file", required=True, help="Path to the input CSV file containing kinematic data.")
parser.add_argument("-s", "--static-data-file", required=True, help="Path to the input CSV file containing static data.")
parser.add_argument("-i", "--injection-interval", default=6, help="The interval of static data injection(in minutes) after the first appearance of a match.")
parser.add_argument("--no-header", action='store_true', help="Use this option if the input files do not contain a header row.")
parser.add_argument("-o", "--output-file", required=True, help="The path to the output file that will contain the extracted rows.")

args = parser.parse_args()

try:
    interval_msec = int(args.injection_interval) * 60 * 1000

    header_val=0 if not args.no_header else None

    kinematic_df = pd.read_csv(args.kinematic_data_file, header=header_val)
    static_df_pre = pd.read_csv(args.static_data_file, header=header_val)
    vessel_id = static_df_pre.columns[0]
    ship_type = static_df_pre.columns[2]
    static_df = static_df_pre.drop_duplicates(subset=vessel_id, keep='last') 
    static_df = static_df.loc[static_df[ship_type].isna() | static_df[ship_type].le(99)] 
    static_df[ship_type] = static_df[ship_type].astype('Int64')



    kinematic_df.columns = ["timestamp", "vessel_id"] + [f"kinematic_col_{i}" for i in range(2, len(kinematic_df.columns))]
    static_df.columns = ["vessel_id"] + [f"static_col_{i}" for i in range(1, len(static_df.columns))]
    
    kinematic_df["timestamp"] = kinematic_df["timestamp"].astype(int)
    common_ids = set(kinematic_df["vessel_id"]).intersection(set(static_df["vessel_id"]))

    all_rows = []
    for idx, row in kinematic_df.iterrows():
        all_rows.append((row["timestamp"], row.tolist()))

    for vessel_id in common_ids:
        subset_df = kinematic_df[kinematic_df["vessel_id"] == vessel_id]
        start_ts = subset_df["timestamp"].min() 
        end_ts = subset_df["timestamp"].max() 
        static_data = static_df[static_df["vessel_id"] == vessel_id].iloc[0].tolist() 

        for ts in range(start_ts, end_ts, interval_msec):
            if ts == start_ts:
                lagged_ts = ts + 30000 
            else: 
                lagged_ts = 30000
            if lagged_ts < end_ts: 
                new_row = [lagged_ts] + static_data  
                all_rows.append((lagged_ts , new_row))

    
    all_rows.sort(key=lambda x: x[0])

    with open(args.output_file, "w") as outfile:
        for idx, row in all_rows: 
            clean_row = ["" if pd.isna(column) else str(column) for column in row]
            outfile.write(",".join(clean_row) + "\n")

    sys.exit(0)

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

