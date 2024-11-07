import os
import yaml
import argparse
import subprocess
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="This script runs the HDL software from the paired_datasets.csv file")
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
    input_csv = os.path.join(base_path, sumstats_folder, config["SumStats"]["paired_data"])
    hdl_script = config["Scripts"]["HDL"]["HDL_software"]  
    hdl_script_path = os.path.join(base_path, hdl_script)
    ld_reference_folder = config["reference_genomes"]["reference_genomes_folder"]
    ld_reference_path = config["reference_genomes"]["UKB_imputed"]
    ld_reference_path = f"{base_path}{ld_reference_folder}{ld_reference_path}"

    output_folder = config["Results"]["results_folder"]
    output_location = config["Results"]["folder_hdl"]
    output_path = os.path.join(base_path, output_folder, output_location)

    # Ensure the output directory exists
    os.makedirs(output_path, exist_ok=True)

    run_hdl_from_csv(input_csv, args.env, hdl_script_path, ld_reference_path, output_path)

def run_hdl_from_csv(csv_file, env, hdl_script_path, ld_reference_path, output_path):
    data = pd.read_csv(csv_file)

    for index, row in data.iterrows():
        hdl_result = run_hdl(row, env, hdl_script_path, ld_reference_path, output_path)
        data.at[index, "hdl"] = hdl_result  # Update HDL column dynamically
        
        # Write back to the CSV file after processing each row
        data.to_csv(csv_file, index=False)

def run_hdl(row, env, hdl_script_path, ld_reference_path, output_path):
    try:
        id_1 = row["id_1"]
        gwas1_path = row[f'{env}_wrangled_path_1']
        id_2 = row["id_2"]
        gwas2_path = row[f'{env}_wrangled_path_2']
        hdl = row["hdl"]
    except ValueError as e:
        print(f"Error unpacking row: {row}")
        return 'Error'

    # Define the output file path
    out_file = os.path.join(output_path, f"{row['id_1']}_{row['label_1']}_{row['id_2']}_{row['label_2']}.Rout")

    # Ensure the specific output subdirectory exists
    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    if pd.isna(gwas1_path) or pd.isna(gwas2_path):
        print(f"One of the GWAS file paths is empty, skipping HDL for row: {row}")
        return 'Error'

    if hdl != 'True':
        try:
            subprocess.run([
                'Rscript', hdl_script_path,
                f"gwas1.df={gwas1_path}",
                f"gwas2.df={gwas2_path}",
                f"LD.path={ld_reference_path}",
                f"output.file={out_file}"
            ], check=True)
            return 'True'
        except subprocess.CalledProcessError:
            print(f"Error running HDL for row: {row}")
            return 'Error'
    else:
        return hdl

if __name__ == "__main__":
    main()
