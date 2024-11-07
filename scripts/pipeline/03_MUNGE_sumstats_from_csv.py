import os
import yaml
import pandas as pd
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="This script automatises and runs munge_sumstats.py")
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
    print(f"Base path: {base_path}")

    sumstats_folder = config["SumStats"]["sumstats_folder"]
    description_csv = config["SumStats"]["description_csv"]
    output_folder = config["SumStats"]["munged_folder"]
    munge_script = config["Scripts"]["ldsc"]["ldsc_munge"]
    singularity_env = config[args.env]["environments_folder"]
    singularity_file = config[args.env]["singularity_ldsc"]
    merge_alleles = config["reference_genomes"]["reference_genomes_folder"]
    merge_alleles_map = config["reference_genomes"]["HapMap3"]

    # print(f"description_csv: {description_csv}")
    description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)
    # print(f"description_csv_path: {description_csv_path}")

    # print(f"munge_script: {munge_script}")
    munge_script_path = os.path.join(base_path, munge_script)
    # print(f"munge_script_path: {munge_script_path}")

    # print(f"singularity_env: {singularity_env}")
    # print(f"singularity_ldsc: {config[args.env]['singularity_ldsc']}")
    singularity_env_path = os.path.join(singularity_env, singularity_file)
    # print(f"Singularity_env_path: {singularity_env_path}")

    # print(f"merge_alleles: {merge_alleles}")
    # print(f"HapMap3: {config['reference_genomes']['HapMap3']}")
    merge_alleles_path = f"{base_path}{merge_alleles}{merge_alleles_map}"
    #merge_alleles_path = os.path.join(base_path, merge_alleles, merge_allele_map)
    # print(f"Merge allele path: {merge_alleles_path}")
    # raise

    # Call function to run munge_sumstats
    run_munge_sumstats(description_csv_path, args.env, singularity_env_path, munge_script_path, merge_alleles_path, output_folder)

def generate_munge_command(row, env, singularity_env_path, munge_script_path, merge_alleles_path, output_folder):
    print("Command is being generated")
    command = ["singularity", "exec", singularity_env_path, "python2", munge_script_path]
    raw_path_column = f"{env}_raw_path"
    command.extend(["--sumstats", str(row[raw_path_column])])

    if not pd.isna(row["snp"]):
        command.extend(["--snp", str(row["snp"])])

    if not pd.isna(row["a1"]):
        command.extend(["--a1", str(row["a1"])])

    if not pd.isna(row["a2"]):
        command.extend(["--a2", str(row["a2"])])

    if not pd.isna(row["frq"]):
        command.extend(["--frq", str(row["frq"])])

    if not pd.isna(row["b"]):
        command.extend(["--signed-sumstats", f"{str(row['b'])},0"])
    elif not pd.isna(row["OR"]):
        command.extend(["--signed-sumstats", f"{str(row['OR'])},1"])
    elif not pd.isna(row["z"]):
        command.extend(["--signed-sumstats", f"{str(row['z'])},0"])

    if pd.isna(row["b"]) and pd.isna(row["z"]) and pd.isna(row["OR"]):
        command.extend(["--a1-inc"])

    if not pd.isna(row["p"]):
        command.extend(["--p", str(row["p"])])

    command.extend(["--N", str(row["N_num"])])

    # Additional metrics
    print("Additional metrics")

    if not pd.isna(row["N_col"]):
        command.extend(["--N-col", str(row["N_col"])])

    if not pd.isna(row["Nca_val"]):
        command.extend(["--N-cas", str(row["Nca_val"])])

    if not pd.isna(row["Nca_col"]):
        command.extend(["--N-cas-col", str(row["Nca_col"])])

    if not pd.isna(row["Nco_val"]):
        command.extend(["--N-con", str(row["Nco_val"])])

    if not pd.isna(row["Nco_col"]):
        command.extend(["--N-con-col", str(row["Nco_col"])])

    if not pd.isna(row["INFO"]):
        command.extend(["--info", str(row["INFO"])])

    print("Generate output path")

    output_path = os.path.join(output_folder, f"{row['id']}_{row['label']}")
    command.extend(["--out", output_path])

    command.extend(["--chunksize", "500000"])
    command.extend(["--merge-alleles", merge_alleles_path])

    # # Additional ignore flags based on column presence
    # if not pd.isna(row["p"]):
    #     print(f"Ignoring z because p-value is present in the row.")
    #     command.append("--ignore")
    #     command.append("z")

    # if not pd.isna(row["ignore"]):
    #     ignore_values = row["ignore"].split(',')
    #     for ignore_value in ignore_values:
    #         command.append("--ignore")
    #         command.append(ignore_value.strip())  # Remove leading/trailing spaces

    # return command
    print("Start ignore command")
    ignore_columns = []

    if "p" in row and not pd.isna(row["p"]):
        print(f"Ignoring z because p-value is present in the row.")
        if not pd.isna(row["z"]):
            ignore_columns.append(str(row["z"]))

    # print("Error 1")

    if row["p"] == "P_noSPA":
        ignore_columns.append("p_value")
        
    # print("Error 2")
    
    if not pd.isna(row["ignore"]):
        ignore_columns.append(str(row["ignore"]).replace(" ", ""))
        
    # print("Error 3")

    if ignore_columns:
        ignore_argument = ",".join(ignore_columns)
        command.extend(["--ignore", ignore_argument])

    # # # return command
    # # print("Start ignore command")
    # # ignore_columns = ""

    # # if "p" in row and not pd.isna(row["p"]):
    # #     print(f"Ignoring z because p-value is present in the row.")
    # #     ignore_columns += str(row["z"])

    # # print("Error 1")

    # # if row["p"] == "P_noSPA":
    # #     # ignore_columns += ",p_value"
    # #     ignore_columns += ","
    # #     ignore_columns += "p_value"
        
    # # print("Error 2")
    
    # # if not pd.isna(row["ignore"]):
    # #     if ignore_columns:
    # #         ignore_columns += ","
        
    # # print("Error 3")

    # # if ignore_columns:
    # #     ignore_columns += str(row["ignore"]).replace(" ","")
    # #     command.extend(["--ignore", ignore_columns])

        # for ignore_value in ignore_values:
        #     ignore_columns.append(ignore_value.strip())  # Remove leading/trailing spaces

        # for ignore_column in ignore_columns:
        #     command.extend(["--ignore", ignore_column])
        #if ignore_columns:
        #     command.append("--ignore")
        # #command.append(",".join(ignore_columns))

            # command.append(ignore_column)
    print("These columns have been ignored:")
    print(ignore_columns) 
    return command

def run_munge_sumstats(csv_file, env, singularity_env_path, munge_script_path, merge_alleles_path, output_folder):
    data = pd.read_csv(csv_file)
    from shlex import join
    for index, row in data.iterrows():
        # Skip rows where 'munged' is already True
        if str(row["munged"]) != "True":
            try:
                command = generate_munge_command(row, env, singularity_env_path, munge_script_path, merge_alleles_path, output_folder)
                print("Command was generated")
                print(f"\tCommand: \n{command}")
                subprocess.run(command, check=True)

                data.at[index, "munged"] = True
                munged_path = os.path.join(output_folder, f"{row['id']}_{row['label']}.sumstats.gz")
                data.at[index, f"{env}_munged_path"] = munged_path

            except subprocess.CalledProcessError as e:
                print(f"Error processing row {index}: {e}")
                data.at[index, "munged"] = "Error"

            except Exception as e:
                print(f"Unexpected error processing row {index}: {e}")
                data.at[index, "munged"] = "Error"

            finally:
                data.to_csv(csv_file, index=False)

        else:
            print(f"{row['id']}_{row['label']} skipped, already munged")   


if __name__ == "__main__":
    main()

