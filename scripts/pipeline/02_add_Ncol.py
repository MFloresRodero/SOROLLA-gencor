import os
import yaml
import pandas as pd
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def main():
    parser = argparse.ArgumentParser(description="This script creates an N column if it doesn't already exist and updates the csv containing the information.")
    parser.add_argument("--env", choices=["local", "remote"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    # Load data based on environment
    config_file = "/home/maria/git/SOROLLA/config/config.yaml" if args.env == "local" else "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"

    # Load configuration file securely
    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_file}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML configuration: {e}")
        exit(1)

    # Access values from config
    base_path = config[args.env]["base_path"]
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    description_csv = config["SumStats"]["description_csv"]
    description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)

    # Call function to write N_col in CSV
    write_Ncol_in_csv(description_csv_path, args.env)

def add_Ncol_to_dataset(row, env):
    file_path = row[f'{env}_raw_path']
    
    # Detect file extension to handle different formats
    if file_path.endswith('.gz'):
        compression = 'gzip'
    elif file_path.endswith('.tsv') or file_path.endswith('.txt'):
        compression = None
    else:
        print(f"Warning: Unsupported file format for file {file_path}.")
        return row

    try:
        data = pd.read_csv(file_path, sep='\t', compression=compression)  # Assume tab-separated values for .tsv and .txt
    except EOFError:
        print(f"Warning: File {file_path} is corrupted or incomplete.")
        return row
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return row

    if pd.isna(row['N_col']):
        total_sample_size = row['N_num']
        data['N_added'] = total_sample_size
        try:
            if compression == 'gzip':
                data.to_csv(file_path, sep='\t', index=False, compression='gzip')  # Use tab separator
            else:
                data.to_csv(file_path, sep='\t', index=False)  # Use tab separator
            print(f"Dataset {file_path} has been modified and has the N column.")
            row['N_col'] = 'N_added'  # Update the input CSV to indicate N_col was added
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
    else:
        print(f"{row["id"]} already contains an N column")
    return row

def write_Ncol_in_csv(csv_file_path, env):
    df = pd.read_csv(csv_file_path)
    df = df.apply(lambda row: add_Ncol_to_dataset(row, env), axis=1)
    df.to_csv(csv_file_path, index=False, sep='\t')  # Ensure using tab separator for consistency

if __name__ == "__main__":
    main()
