# Script to generate beta from odds ratio and calculate standard error

import pandas as pd
import numpy as np
import yaml
import os
import csv
import gzip
import argparse
from collections import Counter

def main():
    parser = argparse.ArgumentParser(description="Calculate beta and standard error of beta when OR is present")
    parser.add_argument("--env", choices=["local", "remote"], required=True,
                        help="Specify the environment: local or remote")
    args = parser.parse_args()

    # Load configuration file
    config_file = "/home/maria/git/SOROLLA/config/config.yaml" if args.env == "local" else "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)
    
    # Extract paths
    base_path = config[args.env]["base_path"]
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    description_csv = config["SumStats"]["description_csv"]
    description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)
    
    # Process the main CSV
    print("Processing the main description CSV to update datasets with beta and SE calculations...")
    process_main_csv(args.env, description_csv_path)

def get_delimiter(file_path: str, sample_size: int = 4096) -> str:
    """Detect the delimiter of a file dynamically."""
    print(f"Detecting delimiter for file: {file_path}")
    if file_path.endswith('.gz'):
        with gzip.open(file_path, 'rt') as f:
            sample = f.read(sample_size)
    else:
        with open(file_path, 'r') as f:
            sample = f.read(sample_size)

    try:
        delimiter = csv.Sniffer().sniff(sample).delimiter
    except csv.Error:
        potential_delimiters = ['\t', ',', ';', ' ', '|']
        delimiter_counts = Counter(char for char in sample if char in potential_delimiters)
        delimiter = delimiter_counts.most_common(1)[0][0] if delimiter_counts else '\t'
    print(f"Detected delimiter: '{delimiter}'")
    return delimiter

def calculate_beta_and_se(data, or_col, se_col=None):
    """Calculate beta (log(OR)) and standard error (sebeta) for a dataset."""
    print("Converting columns to numeric types (if needed)...")
    try:
        if not np.issubdtype(data[or_col].dtype, np.number):
            data[or_col] = pd.to_numeric(data[or_col], errors='coerce')
        if se_col and se_col in data.columns and not np.issubdtype(data[se_col].dtype, np.number):
            data[se_col] = pd.to_numeric(data[se_col], errors='coerce')
    except Exception as e:
        print(f"Error converting columns to numeric: {e}")
        return data

    print("Dropping rows with missing OR values...")
    data = data.dropna(subset=[or_col])

    # Calculate beta
    if 'beta_added' not in data.columns or data['beta_added'].isna().all():
        print("Calculating beta (log(OR))...")
        data['beta_added'] = np.log(data[or_col])

    # Calculate SE_beta
    if 'sebeta' not in data.columns or data['sebeta'].isna().all():
        if se_col and se_col in data.columns:
            print("Calculating standard error (SE_beta)...")
            upperboundOR = data[or_col] + 1.96 * data[se_col]
            lowerboundOR = data[or_col] - 1.96 * data[se_col]
            upperboundbeta = np.log(upperboundOR)
            lowerboundbeta = np.log(lowerboundOR)
            data['sebeta'] = (upperboundbeta - lowerboundbeta) / (2 * 1.96)
        else:
            print("SE column not available, setting SE_beta to NaN...")
            data['sebeta'] = np.nan
    
    return data

def update_main_csv(env, row, description_csv_path):
    file_path = row[f'{env}_raw_path']  # Dynamically select the correct path based on the environment
    print(f"\nProcessing dataset: {row['label']} (Path: {file_path})")

    # Skip if both beta and SE are already added
    if pd.notna(row.get('b')) and pd.notna(row.get('se')):
        print(f"Skipping {row['label']} - beta and SE already present.")
        return row

    # Determine file compression and delimiter
    compression = 'gzip' if file_path.endswith('.gz') else None
    separator = get_delimiter(file_path)

    # Read the dataset
    print(f"Reading dataset with separator '{separator}' and compression: {compression}")
    try:
        data = pd.read_csv(file_path, sep=separator, compression=compression)
        print(f"Dataset {row['id']}_{row['label']} successfully loaded. First rows:\n{data.head(2)}")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return row

    # Calculate beta and SE
    print("Calculating beta and SE values...")
    data = calculate_beta_and_se(data, row['OR'], row.get('se', None))
    print(f"Modified dataset {row['id']}_{row['label']} preview:\n{data.head(2)}")

    # Save the modified dataset
    try:
        print("Saving the updated dataset...")
        data.to_csv(file_path, sep=separator, index=False, compression=compression)
        print(f"Dataset {file_path} successfully updated.")
    except Exception as e:
        print(f"Error saving updated dataset: {e}")

    # Update main CSV row
    if 'beta_added' in data.columns and row.get('b') is None:
        row['b'] = 'beta_added'
    if 'sebeta' in data.columns and row.get('se') is None:
        row['se'] = 'sebeta'

    # Save back the updated row
    print("Updating the main CSV...")
    try:
        main_csv = pd.read_csv(description_csv_path)
        main_csv.update(pd.DataFrame([row]))
        main_csv.to_csv(description_csv_path, index=False)
        print(f"Main CSV successfully updated with changes for {row['label']}.")
    except Exception as e:
        print(f"Error updating main CSV: {e}")

    return row

def process_main_csv(env, description_csv_path):
    """Process each row in the main CSV to update beta and SE columns."""
    print(f"Loading main CSV from: {description_csv_path}")
    main_csv = pd.read_csv(description_csv_path)
    print(f"Processing {len(main_csv)} datasets from the main CSV...")

    # Ensure all required arguments are passed to the update_main_csv function
    main_csv = main_csv.apply(lambda row: update_main_csv(env, row, description_csv_path), axis=1)

    print("Saving the final updated main CSV...")
    main_csv.to_csv(description_csv_path, index=False)
    print("All datasets processed and main CSV updated successfully.")

if __name__ == "__main__":
    main()
