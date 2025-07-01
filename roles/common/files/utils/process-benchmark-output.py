#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import argparse
import sys
import re

parser = argparse.ArgumentParser("process-benchmark-output.py")
parser.add_argument("-p", "--producer-log", required=True, help="Path to the file created by the producer benchmark process. name format: 'producer_<YEAR>_(Database|Kafka)_bench.csv'")
parser.add_argument("-c", "--consumer-log", required=True, help="Path to the file created by the consumer benchmark process. name format: 'consumer_<YEAR>_(Database|Kafka)_bench.csv'")
parser.add_argument("-o", "--output-dir", required=True, help="Path to the directory where the output plots will be saved.")
args = parser.parse_args()

producer_year = re.search(r"_(\d{4})_", args.producer_log).groups()[0]
consumer_year = re.search(r"_(\d{4})_", args.consumer_log).groups()[0]

producer_platform = re.search(r"_(Kafka|Database)_", args.producer_log).groups()[0]
consumer_platform = re.search(r"_(Kafka|Database)_", args.consumer_log).groups()[0]

if producer_year != consumer_year:
    print('Mismatched year between producer and consumer logs!')
    sys.exit(1)

if producer_platform != consumer_platform:
    print('Mismatched platform between producer and consumer logs!')
    sys.exit(1)
try:
    producer_df = pd.read_csv(args.producer_log, header=None, names=['message_id','produced_at'])  
    consumer_df = pd.read_csv(args.consumer_log, header=None, names=['message_id','consumed_at'])  

    merged_df = pd.merge(producer_df, consumer_df, on="message_id", how="left")

    merged_df["latency_ms"] = merged_df["consumed_at"] - merged_df["produced_at"]

    consumed = merged_df[merged_df["consumed_at"].notnull()]

    average_latency = consumed["latency_ms"].mean()
    lost_percentage = 100.0 * merged_df["consumed_at"].isnull().sum() / len(merged_df)

    print(f"Average Latency: {average_latency:.2f} ms")
    print(f"Lost Kinematic Messages: {lost_percentage:.2f}%")

    plt.figure(figsize=(10, 6))
    plt.hist(consumed["latency_ms"], bins=50, edgecolor='black')
    plt.title(f"Latency Distribution(ms) for {producer_year} Dataset Peak using {producer_platform}")
    plt.xlabel("Latency (ms)")
    plt.ylabel("Number of Kinematic Messages")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{args.output_dir}/{producer_platform}_{producer_year}.png")

except Exception as e:
    print(f"An error has occured:{e}")
    sys.exit(1)

sys.exit(0)
