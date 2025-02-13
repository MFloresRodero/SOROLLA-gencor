import os
import pandas as pd
import yaml
import subprocess
import argparse
import re

def main():
    parser = argparse.ArgumentParser(description="This script is run to create individual commands that are run later in a .sh file")
    parser.add_argument("--env", choices=["local", "remote", "shared"], 
                        required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    # Environment parameters
    if args.env == "local":
        config_file = "/home/maria/git/SOROLLA/config/config.yaml"
    elif args.env == "remote":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
    elif args.env == "shared":
        config_file = "/gpfs/projects/hpcsharing/364592/config/config.yaml"
    else:
        raise ValueError("Environment not found, check if you specified the environment with --env or if the path is wrong")


    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_file}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML configuration: {e}")
        exit(1)


    # Access values
    base_path = config[args.env]["base_path"]
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    wrangle_folder = config["SumStats"]["wrangled_folder"]
    command_output_folder = config["SumStats"]["wrangle_commands"]
    description_csv = config["SumStats"]["description_csv"]
    matrix_description = config["SumStats"]["matrix_description"]
    ref_panel_folder = config["reference_genomes"]["reference_genomes_folder"]
    ref_panel = config["reference_genomes"]["UKB_imputed"]

    # Build paths
    wrangle_output_path = os.path.join(base_path, wrangle_folder)
    command_output_path = os.path.join(base_path, command_output_folder)
    description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)
    wrangle_script_path = os.path.join(base_path, config["Scripts"]["HDL"]["HDL_wrangler"])
    ref_panel_path = f"{base_path}{ref_panel_folder}{ref_panel}"
    matrix_csv_path = os.path.join(base_path, sumstats_folder, matrix_description)

    generate_and_save_commands(args.env, description_csv_path, matrix_csv_path, wrangle_output_path, command_output_path, wrangle_script_path, ref_panel_path)
    run_wrangle_commands(description_csv_path, command_output_path)

def generate_wrangling_command(env, ref_row, matrix_row, wrangle_output_path, wrangle_script_path, ref_panel_path, command_file_path):
        processed_path_col = f"{env}_preprocessed_path"
        print(f"This is the processed path column from the description_csv: {processed_path_col}")
        wrangle_output_path_final = os.path.join(wrangle_output_path, f"{ref_row['label']}_{ref_row['id']}")
        print(f"This is the path where the wrangled file will be saved: {wrangle_output_path}")

        if matrix_row["zscore"] in [1, 2]:
            command = f"""Rscript {wrangle_script_path} \\
gwas.file={ref_row[processed_path_col]} \\
LD.path={ref_panel_path} \\
"SNP=rsID A1=A1 A2=A2 N=Ncol Z=zscore" \\
output.file={wrangle_output_path_final} \\
log.file={wrangle_output_path_final}\n"""
        elif matrix_row["beta"] in [1, 2] and matrix_row["beta_standard_error"] in [1, 2]:
            command = f"""Rscript {wrangle_script_path} \\
gwas.file={ref_row[processed_path_col]} \\
LD.path={ref_panel_path} \\
SNP=rsID A1=A1 A2=A2 N=Ncol b=beta se=beta_standard_error \\
output.file={wrangle_output_path_final} \\
log.file={wrangle_output_path_final}\n"""
        else:
            print(f"Skipping row {ref_row['label']}_{ref_row['id']} because neither 'z' nor 'b'/'se' columns are filled properly.")
            return "Error"  # Return "Error" when the row is skipped
        
        with open(command_file_path, 'w') as command_file:
            command_file.write(command)
        return "Generated"  # Return "Generated" when the command is successfully generated


def generate_and_save_commands(env, description_csv_path, matrix_csv_path, wrangle_output_path, command_output_path, wrangle_script_path, ref_panel_path):
    print(f"{ref_panel_path}")
    description_csv = pd.read_csv(description_csv_path)
    print(f"The description csv is located in {description_csv_path}")
    matrix_data = pd.read_csv(matrix_csv_path)
    print(f"The matrix csv is located in {matrix_csv_path}")
    print(f"Running on: {env}")
        
    if not os.path.exists(wrangle_output_path):
        os.makedirs(wrangle_output_path)
        
    for index, ref_row in description_csv.iterrows():
        if str(ref_row["wrangled"]) != "Generated":
            try:
                print("The command for this dataset has not being created so the command will be generated now.")
                matrix_row = matrix_data.loc[matrix_data["id"]==ref_row["id"]].iloc[0]
                print(f"This is the ref_row: {ref_row}")
                print(f"This is the matrix_row: {ref_row}")
                command_file_path = os.path.join(command_output_path, f"{ref_row['label']}_{ref_row['id']}_command.sh")
                print(f"This is where the command will be saved: {command_file_path}")
                wrangled_status = generate_wrangling_command(env, ref_row, matrix_row, wrangle_output_path, wrangle_script_path, ref_panel_path, command_file_path)
                print(f"Wrangled status is: {wrangled_status}")
                description_csv.at[index, "wrangled"] = wrangled_status  # Update to "True" or "Error" based on result

            except Exception as e:
                print(f"Error processing row {index}:{e}")
                description_csv.at[index, "wrangled"] = "CommandError"
            finally:
                description_csv.to_csv(description_csv_path, index=False)

        else:
            print(f"{ref_row['label']}_{ref_row['id']} skipped, command already generated")


def run_wrangle_commands(description_csv_path, command_output_path):
    description_csv = pd.read_csv(description_csv_path)

    for command in os.listdir(command_output_path):
        if command.endswith("_command.sh"):
            label, file_id = command.replace("_command.sh", "").split("_")
            print(f"This is the label: {label}")
            print(f"This is the id: {file_id}")
            
            if not label or not file_id:
                print("Could not find the label and id to match with the description_csv")
                continue

            command_file_path = os.path.join(command_output_path, command)
            match_row = description_csv[(description_csv["label"] == label) & (description_csv["id"] == file_id)]
            
            if match_row.empty:
                print("Could not match with CSV")
                continue

            index = match_row.index[0]
            wrangled_status = description_csv.at[index, "wrangled"]
            print(f"Wrangled status: {wrangled_status}")

            if wrangled_status in ["Generated", "RunningError"]:
                try:
                    print(f"Starting wrangling for {match_row}")
                    subprocess.run(["sh", command_file_path], check=True)
                    description_csv.at[index, "wrangled"] = "True"
                    description_csv.to_csv(description_csv_path, index=False)
                    print(f"Successfully run the wrangle command {command_file_path}")
                
                except subprocess.CalledProcessError:
                    description_csv.at[index, "wrangled"] = "RunningError"
                    description_csv.to_csv(description_csv_path, index=False)
                    print(f"There was an error running the wrangle command {command_file_path}")

            else:
                print(f"{command_file_path} was already wrangled")


if __name__ == "__main__":
    main()