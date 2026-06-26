import os
import yaml
import argparse
import subprocess
import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="This script runs the LDSC software from the paired_datasets.csv file"
    )
    parser.add_argument(
        "--env",
        choices=["local", "remote", "shared"],
        required=True,
        help="Specify if you are running this file in local, remote or shared"
    )
    args = parser.parse_args()

    if args.env == "local":
        config_file = "/home/maria/git/SOROLLA/config/config.yaml"
    elif args.env == "remote":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
    elif args.env == "shared":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/JON/config.yaml"
    else:
        raise ValueError("Environment not found, check if you specified the environment with --env")

    # Load configuration file
    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_file}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML configuration: {e}")
        exit(1)

    print(f"Using config file: {config_file}")

    # Access values from config
    base_path = config[args.env]["base_path"]
    print(f"Base path: {base_path}")

    sumstats_folder = config["SumStats"]["sumstats_folder"]
    print(f"Sumstats folder: {sumstats_folder}")

    paired_data = config["SumStats"]["paired_data"]
    print(f"Paired data CSV: {paired_data}")

    input_csv = os.path.join(base_path, sumstats_folder, paired_data)
    print(f"Input CSV path: {input_csv}")

    ldsc_script = config["Scripts"]["ldsc"]["ldsc_software"]
    print(f"LDSC script: {ldsc_script}")

    ldsc_script_path = os.path.join(base_path, ldsc_script)
    print(f"LDSC script path: {ldsc_script_path}")

    singularity_env = config[args.env]["environments_folder"]
    print(f"Singularity environment folder: {singularity_env}")

    singularity_file = config[args.env]["singularity_ldsc"]
    print(f"Singularity file: {singularity_file}")

    singularity_env_path = os.path.join(singularity_env, singularity_file)
    print(f"Singularity environment path: {singularity_env_path}")

    ldsc_output_folder = config["Results"]["results_folder"]
    print(f"LDSC output folder: {ldsc_output_folder}")

    ldsc_output_location = config["Results"]["folder_ldsc"]
    print(f"LDSC output location: {ldsc_output_location}")

    output_path = os.path.join(base_path, ldsc_output_folder, ldsc_output_location)
    print(f"Full output path: {output_path}")

    ld_scores_folder = config["reference_genomes"]["reference_genomes_folder"]
    print(f"LD scores folder: {ld_scores_folder}")

    ld_scores = config["reference_genomes"]["eur_w_ld_chr"]
    print(f"LD scores: {ld_scores}")

    ld_path = os.path.join(base_path, ld_scores_folder, ld_scores)
    print(f"Full LD path: {ld_path}")

    # Create output folder if it does not exist
    os.makedirs(output_path, exist_ok=True)

    run_ldsc_from_csv(
        input_csv,
        args.env,
        singularity_env_path,
        ldsc_script_path,
        ld_path,
        output_path
    )


def run_ldsc_from_csv(csv_file, env, singularity_env_path, ldsc_script_path, ld_path, output_path):
    data = pd.read_csv(csv_file)

    # Make sure the ldsc column exists
    if "ldsc" not in data.columns:
        data["ldsc"] = "False"

    total_rows = len(data)

    for index, row in data.iterrows():
        print(f"\n========== Processing row {index + 1}/{total_rows} ==========")

        try:
            ldsc_result = run_ldsc(
                row,
                env,
                singularity_env_path,
                ldsc_script_path,
                ld_path,
                output_path
            )

            data.at[index, "ldsc"] = ldsc_result

        except Exception as e:
            print(f"Unexpected error in row {index}: {e}")
            data.at[index, "ldsc"] = "Error"

        finally:
            # Save after every iteration
            data.to_csv(csv_file, index=False)
            print(f"Progress saved after row {index + 1}: ldsc = {data.at[index, 'ldsc']}")

    print(f"\nFinished. Updated CSV saved to: {csv_file}")


def run_ldsc(row, env, singularity_env_path, ldsc_script_path, ld_path, output_path):
    try:
        id_1 = row["id_1"]
        label_1 = row["label_1"]
        munged_file_path_1 = row[f"{env}_munged_path_1"]

        id_2 = row["id_2"]
        label_2 = row["label_2"]
        munged_file_path_2 = row[f"{env}_munged_path_2"]

        ldsc = row["ldsc"]

    except Exception as e:
        print(f"Error unpacking row: {e}")
        print(row)
        return "Error"

    pair_name = f"{id_1}_{label_1}_{id_2}_{label_2}"
    out_file = os.path.join(output_path, pair_name)

    if pd.isna(munged_file_path_1) or pd.isna(munged_file_path_2):
        print(f"One of the munged file paths is empty, skipping LDSC for: {pair_name}")
        return "Error"

    if str(ldsc).strip().lower() == "true":
        print(f"Skipping {pair_name}, already done.")
        return "True"

    print(f"Starting LDSC for: {pair_name}")
    print(f"Munged file 1: {munged_file_path_1}")
    print(f"Munged file 2: {munged_file_path_2}")
    print(f"LD path: {ld_path}")
    print(f"Output file: {out_file}")

    command = [
        "singularity", "exec", singularity_env_path, "python2",
        ldsc_script_path,
        "--rg", f"{munged_file_path_1},{munged_file_path_2}",
        "--ref-ld-chr", ld_path,
        "--w-ld-chr", ld_path,
        "--out", out_file
    ]

    print("Running command:")
    print(" ".join(command))

    try:
        subprocess.run(command, check=True)
        print(f"LDSC finished correctly for: {pair_name}")
        return "True"

    except subprocess.CalledProcessError as e:
        print(f"Error running LDSC for: {pair_name}")
        print(e)
        return "Error"

    except FileNotFoundError as e:
        print(f"Command or file not found while running LDSC for: {pair_name}")
        print(e)
        return "Error"

    except Exception as e:
        print(f"Unexpected error running LDSC for: {pair_name}")
        print(e)
        return "Error"


if __name__ == "__main__":
    main()