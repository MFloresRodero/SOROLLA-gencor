import os
import yaml
import pandas as pd
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="This script automatises and runs munge_sumstats.py")
    parser.add_argument("--env", choices=["local", "remote", "shared"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    # Load data based on environment
    if args.env == "local":
        config_file = "/home/maria/git/SOROLLA/config/config.yaml"
    elif args.env == "remote":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
    elif args.env == "shared":
        config_file = "/gpfs/projects/hpcsharing/364592/config/config.yaml"
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
    print(f"Base path: {base_path}")

    # Configuration files
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    description_csv = config["SumStats"]["description_csv"]
    munged_folder = config["SumStats"]["munged_folder"]
    munge_script = config["Scripts"]["ldsc"]["ldsc_munge"]
    singularity_env = config[args.env]["environments_folder"]
    singularity_file = config[args.env]["singularity_ldsc"]
    merge_alleles = config["reference_genomes"]["reference_genomes_folder"]
    merge_alleles_map = config["reference_genomes"]["HapMap3"]
    matrix_description = config["SumStats"]["matrix_description"]

    # Build paths
    output_folder = os.path.join(base_path, munged_folder)
    description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)
    munge_script_path = os.path.join(base_path, munge_script)
    singularity_env_path = os.path.join(singularity_env, singularity_file)
    merge_alleles_path = f"{base_path}{merge_alleles}{merge_alleles_map}"
    matrix_csv_path = os.path.join(base_path, sumstats_folder, matrix_description)

    # Call function to run munge_sumstats
    run_munge_sumstats(description_csv_path, matrix_csv_path, args.env, singularity_env_path, munge_script_path, merge_alleles_path, output_folder)

def generate_munge_command(csv_row, matrix_row, env, singularity_env_path, munge_script_path, merge_alleles_path, output_folder):
    print("Command is being generated")
    command = ["singularity", "exec", singularity_env_path, "python2", munge_script_path]
    preprocessed_path_column = f"{env}_preprocessed_path"
    command.extend(["--sumstats", str(csv_row[preprocessed_path_column])])
    command.extend(["--snp", "rsID"])
    command.extend(["--a1", "A1"])
    command.extend(["--a2", "A2"])
    command.extend(["--N", str(csv_row["N_num"])])

    if matrix_row["A1_frequency"]:
        command.extend(["--frq", "A1_frequency"])

    if matrix_row["beta"] in [1, 2]:
        command.extend(["--signed-sumstats", f"beta,0"])
    elif matrix_row["odds_ratio"] in [1, 2]:
        command.extend(["--signed-sumstats", f"odds_ratio,1"])
    elif matrix_row["zscore"] in [1, 2]:
        command.extend(["--signed-sumstats", f"zscore,0"])
    else:
        command.extend(["--a1-inc"])
        
    if matrix_row["p_value"] in [1, 2]:
        command.extend(["--p", "p_value"])

    # Additional metrics
    print("Additional metrics")

    if matrix_row["Ncol"] in [1, 2]:
        command.extend(["--N-col", "Ncol"])
        
    if matrix_row["Nca_col"] in [1, 2]:
        command.extend(["--N-cas-col", "Nca_col"])
    if not pd.isna(csv_row["Nca_val"]):
        command.extend(["--N-cas", str(csv_row["Nca_val"])])
    
    if matrix_row["Nco_col"] in [1, 2]:
        command.extend(["--N-con-col", "Nco_col"])
    if not pd.isna(csv_row["Nco_val"]):
        command.extend(["--N-con", str(csv_row["Nco_val"])])

    if matrix_row["INFO"] in [1, 2]:
        command.extend(["--info", "INFO"])

    print("Generate output path")
    print(f"Output folder: {output_folder}")
    output_path = os.path.join(output_folder, f"{matrix_row['label']}_{matrix_row['id']}")
    print(f"Output path: {output_path}")
    command.extend(["--out", output_path])

    command.extend(["--chunksize", "500000"])
    command.extend(["--merge-alleles", merge_alleles_path])
    print(command)
    return command

def run_munge_sumstats(csv_file, matrix_csv, env, singularity_env_path, munge_script_path, merge_alleles_path, output_folder):

    description_csv = pd.read_csv(csv_file)
    matrix_data = pd.read_csv(matrix_csv)

    for index, row in description_csv.iterrows():
        if str(row["munged"]) != "True":
            try:
                matrix_row = matrix_data.loc[matrix_data["id"]==row["id"]].iloc[0]
                command = generate_munge_command(row, matrix_row, env, singularity_env_path, munge_script_path, merge_alleles_path, output_folder)
                print("Command was generated")
                print(f"\tCommand: \n{command}")
                subprocess.run(command, check=True)

                description_csv.at[index, "munged"] = True
                munged_path = os.path.join(output_folder, f"{row['label']}_{row['id']}.sumstats.gz")
                description_csv.at[index, f"{env}_munged_path"] = munged_path
                
            except subprocess.CalledProcessError as e:
                print(f"Error processing row {index}: {e}")
                description_csv.at[index, "munged"] = "Error"

            except Exception as e:
                print(f"Unexpected error processing row {index}: {e}")
                description_csv.at[index, "munged"] = "Error"

            finally:
                # Save updated CSV file
                description_csv.to_csv(csv_file, index=False)
            
        else:
            print(f"✅ {row['label']}_{row['label']} skipped, already munged.")

if __name__ == "__main__":
    main()

