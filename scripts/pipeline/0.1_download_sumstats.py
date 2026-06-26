import pandas as pd
import os
import subprocess
import argparse
import yaml
import gzip

def main():
    parser = argparse.ArgumentParser(description="This script takes the data from the catalog downloads the GWAS files into the RAW folder.")
    parser.add_argument("--env", choices=["local", "remote", "shared"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    # Load data based on environment
    if args.env == "local":
        config_file = "/home/maria/git/SOROLLA/config/config.yaml"
    elif args.env == "remote":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
    elif args.env == "shared":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/JON/config.yaml"
    else:
        raise ValueError("Environment not found, check if you specified the environment with --env or if the path is wrong")

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
    

    # Access the values
    base_path = config[args.env]["base_path"]
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    raw_folder = config["SumStats"]["raw_folder"]
    raw_catalog = config["SumStats"]["raw_catalog"]
    raw_sumstats_folder_path = os.path.join(base_path, raw_folder)
    print(raw_sumstats_folder_path)
    csv_file_path = os.path.join(base_path, sumstats_folder, raw_catalog)
    print(csv_file_path)
    csv_excell = pd.read_csv(csv_file_path)
    download_summarystatistics(csv_excell, raw_sumstats_folder_path)

def download_summarystatistics(df, raw_folder_path):
    """
    This is the function to download the Summary Statistics datasets.
    It needs a csv as input containing the columns FILENAME and SUMMARYSTATISTICS.
    row["filename"] == id + file extension
    row["summaryStatistics"] == direct link to dataset
    """

    for index, row in df.iterrows():
        print(f"Generating download command for {row['label']}")

        # Create the variable containing the final path where each row will be downloaded.
        # Change this path if not downloading in local.
        path_filename = f"{raw_folder_path}{row['filename']}"

        # Check dir
        os.makedirs(os.path.dirname(path_filename), exist_ok=True)
        
        if os.path.exists(path_filename):
            print(f"Dataset {path_filename} already exists. Skipping processing for this dataset.")
            continue
        
        # Create the wget command
        sumstats = row["summaryStatistics"]
        command = ["wget", "-O", path_filename, sumstats]
        print(f"Executing command: {' '.join(command)}")

        # Execute
        subprocess.run(command)
        
        
        # Modify vcf
        if "vcf" in row["filename"]:
            final_filename = row["filename"].replace(".vcf", "")
            final_path = f"{raw_folder_path}{final_filename}"

            try:
                # Decompress gzip file
                with gzip.open(path_filename, 'rt', encoding='utf-8') as file:
                    df_vcf = pd.read_csv(file, comment="#", delimiter="\t")

                # Save decompressed TSV
                df_vcf.to_csv(final_path, sep="\t", index=False)
                print(f"Processed VCF file saved to {final_path}")

            except Exception as e:
                print(f"Error processing VCF file {path_filename}: {e}")


if __name__ == "__main__":
    main()
