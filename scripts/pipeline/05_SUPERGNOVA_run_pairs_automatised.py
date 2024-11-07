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
    print("This is the base path:", base_path)
    # Input files
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    input_csv = os.path.join(base_path, sumstats_folder, config["SumStats"]["supergnova_paired"])
    # Supergnova files
    supergnova_script = config["Scripts"]["SUPERGNOVA"]["supergnova_software"]
    supergnova_script_path = os.path.join(base_path, supergnova_script)
    # Singularity files
    singularity_env = config[args.env]["environments_folder"]
    singularity_file = config[args.env]["singularity_ldsc"]
    singularity_env_path = os.path.join(singularity_env, singularity_file)
    # Supergnova output
    supergnova_output_folder = config["Results"]["results_folder"]
    supergnova_output_location = config["Results"]["folder_supergnova"]
    output_path = f"{base_path}{supergnova_output_folder}{supergnova_output_location}"
    print("This is the output_path", output_path)
    # Reference files
    reference_folder = config["reference_genomes"]["reference_genomes_folder"]
    plink_folder = config["reference_genomes"]["plink_folder"]
    print(f"This is the plink folder path", plink_folder)

    # Bfile
    supergnova_bfile = config["reference_genomes"]["supergnova_bfile"]
    print(f"This is the supergnova bfile path",supergnova_bfile)
    bfile_path = f"{base_path}{reference_folder}{plink_folder}{supergnova_bfile}"
    print(f"This is the bfile path",bfile_path)

    # Partition
    supergnova_partition = config["reference_genomes"]["supergnova_partition"]
    print(f"This is the partition path", supergnova_partition)
    partition_path = f"{base_path}{reference_folder}{plink_folder}{supergnova_partition}"
    print(f"This is the partition path",partition_path)

    run_supergnova_from_csv(input_csv, args.env, singularity_env_path, supergnova_script_path, bfile_path, partition_path, output_path)

def run_supergnova_from_csv(csv_file, env, singularity_env_path, supergnova_script_path, bfile_path, partition_path, output_path):
    data = pd.read_csv(csv_file)

    for index, row in data.iterrows():
        supergnova_result = run_supergnova(row, env, singularity_env_path, supergnova_script_path, bfile_path, partition_path, output_path)
        data.at[index, "supergnova"] = supergnova_result  # Update supergnova column
        
        data.to_csv(csv_file, index=False) # Save after each iteration

def run_supergnova(row, env, singularity_env_path, supergnova_script_path, bfile_path, partition_path, output_path):
    try:
        id_1 = row["id_1"]
        munged_file_path_1 = row.get(f'{env}_munged_path_1')
        id_2 = row["id_2"]
        munged_file_path_2 = row.get(f'{env}_munged_path_2')
        supergnova = row["supergnova"]
    except KeyError as e:
        print(f"Error unpacking row: {row}")
        return 'Error'

    # Ensure paths are valid and are not NaN
    if pd.isna(munged_file_path_1) or pd.isna(munged_file_path_2):
        print(f"One of the munged file paths is empty, skipping supergnova for row: {row}")
        return 'Error'

    # Ensure that supergnova should be run only if it is not already 'True'
    if supergnova != 'True':
        try:
            out_file = os.path.join(output_path, f"{id_1}_{row['label_1']}_{id_2}_{row['label_2']}")
            print("This is the path for --out command",out_file)

            # Convert numerical values to integers to avoid invalid input errors
            n1 = int(row.get("N_num_1", 0))
            n2 = int(row.get("N_num_2", 0))

            if n1 <= 0 or n2 <= 0:
                print(f"Invalid sample sizes for N1 or N2, skipping row: {row}")
                return 'Error'

            # Prepare the supergnova command and run it
            subprocess.run([
                'python3',
                supergnova_script_path, munged_file_path_1, munged_file_path_2,
                '--N1', str(n1),  # Convert integers to strings
                '--N2', str(n2),  # Convert integers to strings
                '--bfile', f"{bfile_path}",
                '--partition', f"{partition_path}",
                '--out', out_file
            ], check=True)
            return 'True'
        except subprocess.CalledProcessError:
            print(f"Error running supergnova for row: {row}")
            return 'Error'
    else:
        return supergnova

if __name__ == "__main__":
    main()
