import os
import yaml
import argparse
import subprocess
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="This script runs the ldsc software from the paired_datasets.csv file")
    parser.add_argument("--env", choices=["local", "remote", "shared"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    parser.add_argument("--batch", required=True,
                        help="Selects batch number to run")
    
    args = parser.parse_args()

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

    # Access values from config
    base_path = config[args.env]["base_path"]
    print("This is the base path:", base_path)

    # Input files
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    supergnova_paired_folder = config["SumStats"]["supergnova_folder"]
    supergnova_paired_file = config["SumStats"]["paired_data"]

    input_csv = os.path.join(base_path, sumstats_folder, supergnova_paired_file)
    print("This is the input path:", input_csv)

    supergnova_err_out_location = os.path.join(
        base_path,
        sumstats_folder,
        supergnova_paired_folder
    )
    print("This is the SuperGNOVA err/out folder:", supergnova_err_out_location)

    supergnova_file_output = os.path.join(
        supergnova_err_out_location,
        f"{args.batch}_batch.csv"
    )
    print("This is the SuperGNOVA batch output file:", supergnova_file_output)

    # SuperGNOVA script
    supergnova_script = config["Scripts"]["SUPERGNOVA"]["supergnova_software"]
    supergnova_script_path = os.path.join(base_path, supergnova_script)
    print("This is the SuperGNOVA script path:", supergnova_script_path)

    # Singularity files
    singularity_env = config[args.env]["environments_folder"]
    singularity_file = config[args.env]["singularity_ldsc"]

    singularity_env_path = os.path.join(singularity_env, singularity_file)
    print("This is the singularity environment path:", singularity_env_path)

    # SuperGNOVA output
    supergnova_output_folder = config["Results"]["results_folder"]
    supergnova_output_location = config["Results"]["folder_supergnova"]

    output_path = os.path.join(
        base_path,
        supergnova_output_folder,
        supergnova_output_location
    )
    print("This is the output_path:", output_path)

    # Reference files
    reference_folder = config["reference_genomes"]["reference_genomes_folder"]
    plink_folder = config["reference_genomes"]["plink_folder"]

    print("This is the reference folder:", reference_folder)
    print("This is the plink folder:", plink_folder)

    # Bfile
    supergnova_bfile = config["reference_genomes"]["supergnova_bfile"]
    print("This is the supergnova bfile from config:", supergnova_bfile)

    bfile_path = os.path.join(
        base_path,
        reference_folder,
        plink_folder,
        supergnova_bfile
    )
    print("This is the bfile path:", bfile_path)

    # Partition
    supergnova_partition = config["reference_genomes"]["supergnova_partition"]
    print("This is the supergnova partition from config:", supergnova_partition)

    partition_path = os.path.join(
        base_path,
        reference_folder,
        plink_folder,
        supergnova_partition
    )
    print("This is the partition path:", partition_path)

    # Ensure output directories exist before running
    os.makedirs(supergnova_err_out_location, exist_ok=True)
    os.makedirs(os.path.dirname(supergnova_file_output), exist_ok=True)
    os.makedirs(output_path, exist_ok=True)

    # Run supergnova for the selected batch
    run_supergnova_from_csv(
        args.batch,
        input_csv,
        args.env,
        singularity_env_path,
        supergnova_script_path,
        bfile_path,
        partition_path,
        output_path,
        supergnova_file_output,
        supergnova_err_out_location
    )

    
def run_supergnova_from_csv(batch_number, csv_file, env, singularity_env_path, supergnova_script_path, bfile_path, partition_path, output_path, supergnova_file_output, supergnova_err_out_location):
    data = pd.read_csv(csv_file)
    data = data[data["batch"] == int(batch_number)]
    data = data.reset_index(drop=True)

    if os.path.exists(supergnova_file_output):
        saving = pd.read_csv(supergnova_file_output)
        saving = saving.reset_index(drop=True)
    else:
        saving = data[["id_1", "id_2", "label_1", "label_2", "supergnova", "batch"]]
        saving = saving.reset_index(drop=True)
    
    for index, row in data.iterrows():
        supergnova_result = run_supergnova(
            row,
            env,
            singularity_env_path,
            supergnova_script_path,
            bfile_path,
            partition_path,
            output_path,
            supergnova_err_out_location
        )        
        
        # CHANGED:
        # saving.at[index, "supergnova"] = supergnova_result
        # update by pair identity first, fallback to index if needed.
        # matching by dataframe index is fragile and can create extra rows.
        # Matching by id_1/id_2 is much safer because these define the pair.
        # saving.at[index, "supergnova"] = supergnova_result

        pair_mask = (saving["id_1"] == row["id_1"]) & (saving["id_2"] == row["id_2"])

        if pair_mask.any():
            saving.loc[pair_mask, "supergnova"] = supergnova_result
        else:
            # CHANGED:
            # if the pair is not already present in saving, append it explicitly.
            # avoids accidental sparse index row creation.
            new_row = {
                "id_1": row["id_1"],
                "id_2": row["id_2"],
                "label_1": row["label_1"],
                "label_2": row["label_2"],
                "supergnova": supergnova_result,
                "batch": row["batch"]
            }
            saving = pd.concat([saving, pd.DataFrame([new_row])], ignore_index=True)

        # CHANGED:
        # saving.to_csv(supergnova_file_output, index=False)
        # keep it, but deduplicate before saving.
        # if older runs already created duplicated lines, this helps clean them.
        saving = saving.drop_duplicates(subset=["id_1", "id_2"], keep="last")
        saving.to_csv(supergnova_file_output, index=False)  # Save after each iteration


def run_supergnova(row, env, singularity_env_path, supergnova_script_path, bfile_path, partition_path, output_path, supergnova_err_out_location):
    try:
        id_1 = row["id_1"]
        munged_file_path_1 = row.get(f'{env}_munged_path_1')
        id_2 = row["id_2"]
        munged_file_path_2 = row.get(f'{env}_munged_path_2')
        supergnova = row["supergnova"]
    except KeyError as e:
        print(f"Error unpacking row: {row}")
        return 'Error'

    err_output = f"{supergnova_err_out_location}err.txt"
    print({err_output})
    out_output = f"{supergnova_err_out_location}out.txt"
    print({out_output})

    # Ensure paths are valid and are not NaN
    if pd.isna(munged_file_path_1) or pd.isna(munged_file_path_2):
        print(f"One of the munged file paths is empty, skipping supergnova for row: {row}")
        return 'Error'

    # Ensure that supergnova should be run only if it is not already 'True'
    if str(supergnova) != 'True':
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
            # subprocess.run([
            #     'python3',
            #     supergnova_script_path, munged_file_path_1, munged_file_path_2,
            #     '--N1', str(n1),  # Convert integers to strings
            #     '--N2', str(n2),  # Convert integers to strings
            #     '--bfile', f"{bfile_path}",
            #     '--partition', f"{partition_path}",
            #     '--out', out_file
            # ], check=True)
            proc = subprocess.Popen(
                [
                'python3',
                supergnova_script_path, munged_file_path_1, munged_file_path_2,
                '--N1', str(n1),  # Convert integers to strings
                '--N2', str(n2),  # Convert integers to strings
                '--bfile', f"{bfile_path}",
                '--partition', f"{partition_path}",
                '--out', out_file
                ], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
            stdout, stderr = proc.communicate()
            print("Output:", stdout.decode())
            print("Error:", stderr.decode())

            # Save stdout and stderr to files for debugging
            with open(err_output, "a") as f:
                f.write(f"\n\n===== {id_1}_{row['label_1']} vs {id_2}_{row['label_2']} =====\n")
                f.write(stderr.decode())

            with open(out_output, "a") as f:
                f.write(f"\n\n===== {id_1}_{row['label_1']} vs {id_2}_{row['label_2']} =====\n")
                f.write(stdout.decode())

            if proc.returncode != 0:
                print(f"SUPERGNOVA failed for row: {row}")
                return 'Error'

            return 'True'

        # CHANGED:
        except Exception as e:
            print(f"Unexpected error running supergnova for row: {row}")
            print(f"Exception: {e}")
            return 'Error'
    else:
        return str(supergnova)


if __name__ == "__main__":
    main()
