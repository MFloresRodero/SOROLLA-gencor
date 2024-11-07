import os
import yaml
import argparse
import subprocess
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="This script runs the ldsc software from the paired_datasets.csv file")
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
    ldsc_script = config["Scripts"]["ldsc"]["ldsc_software"]
    ldsc_script_path = os.path.join(base_path, ldsc_script)
    singularity_env = config[args.env]["environments_folder"]
    singularity_file = config[args.env]["singularity_ldsc"]
    singularity_env_path = os.path.join(singularity_env, singularity_file)
    ldsc_output_folder = config["Results"]["results_folder"]
    ldsc_output_location = config["Results"]["folder_ldsc"]
    output_path = os.path.join(base_path, ldsc_output_folder, ldsc_output_location)
    print(output_path)
    ld_scores_folder = config["reference_genomes"]["reference_genomes_folder"]
    ld_scores = config["reference_genomes"]["eur_w_ld_chr"]
    # ld_path = os.path.join(base_path, ld_scores_folder, ld_scores)
    ld_path = f"{base_path}{ld_scores_folder}{ld_scores}"


    run_ldsc_from_csv(input_csv, args.env, singularity_env_path, ldsc_script_path, ld_path, output_path)

def run_ldsc_from_csv(csv_file, env, singularity_env_path, ldsc_script_path, ld_path, output_path):
    data = pd.read_csv(csv_file)

    for index, row in data.iterrows():
        ldsc_result = run_ldsc(row, env, singularity_env_path, ldsc_script_path, ld_path, output_path)
        data.at[index, "ldsc"] = ldsc_result  # Update LDSC column dynamically

    # Write back to the CSV file
    data.to_csv(csv_file, index=False)

def run_ldsc(row, env, singularity_env_path, ldsc_script_path, ld_path, output_path):
    try:
        id_1 = row["id_1"]
        munged_file_path_1 = row[f'{env}_munged_path_1']
        id_2 = row["id_2"]
        munged_file_path_2 = row[f'{env}_munged_path_2']
        ldsc = row["ldsc"]
    except ValueError as e:
        print(f"Error unpacking row: {row}")
        return 'Error'

    out_file = os.path.join(output_path, f"{row['id_1']}_{row['label_1']}_{row['id_2']}_{row['label_2']}")

    if pd.isna(row[f'{env}_munged_path_1']) or pd.isna(row[f'{env}_munged_path_2']):
        print(f"One of the munged file paths is empty, skipping LDSC for row: {row}")
        return 'Error'
    
    if str(ldsc).strip().lower() == 'true':
        print(f"Skipping {row['id_1']}_{row['label_1']}_{row['id_2']}_{row['label_2']} analysis, already done.")
        return ldsc
    else:
        print(f"Starting command for {row['id_1']}_{row['label_1']}_{row['id_2']}_{row['label_2']} analysis.")
        try:
            subprocess.run([
                'singularity', 'exec', singularity_env_path, 'python2',
                ldsc_script_path,
                '--rg', f"{munged_file_path_1},{munged_file_path_2}",
                '--ref-ld-chr', ld_path,
                '--w-ld-chr', ld_path,
                '--out', out_file
            ], check=True)
            return 'True'
        except subprocess.CalledProcessError:
            print(f"Error running LDSC for row: {row}")
            return 'Error'



if __name__ == "__main__":
    main()


