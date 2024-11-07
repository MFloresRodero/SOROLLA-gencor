import os
import pandas as pd
import yaml

def wrangle_sumstats(input_config_path, output_dir_path):
    try:
        with open(input_config_path) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {input_config_path}")
        return
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML configuration: {e}")
        return

    base_path = config["remote"]["base_path"]
    # base_path = config["local"]["base_path"]
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    output_folder = config["SumStats"]["wrangled_folder"]
    output_path = os.path.join(base_path, output_folder)
    description_csv = config["SumStats"]["description_csv"]
    description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)
    wrangle_script_path = os.path.join(base_path, config["Scripts"]["HDL"]["HDL_wrangler"])
    singularity_env_path = os.path.join(config["remote"]["environments_folder"], config["remote"]["HDL_environment"])
    # singularity_env_path = os.path.join(config["local"]["environments_folder"], config["local"]["HDL_environment"])
    ref_panel_folder = config["reference_genomes"]["reference_genomes_folder"]
    ref_panel = config["reference_genomes"]["UKB_imputed"]
    ref_panel_path = f"{base_path}{ref_panel_folder}{ref_panel}"

    def generate_wrangling_command(row, command_file_path):
        # raw_path_column = "local_raw_path"
        raw_path_column = "remote_raw_path"
        output_path_final = os.path.join(output_path, f"{row['id']}_{row['label']}")
        
        if not pd.isna(row["z"]):
            command = f"""Rscript {wrangle_script_path} \\
gwas.file={row[raw_path_column]} \\
LD.path={ref_panel_path} \\
SNP={row['snp']} A1={row['a1']} A2={row['a2']} N={row['N_col']} Z={row['z']} \\
output.file={output_path_final} \\
log.file={output_path_final}\n"""
        elif not pd.isna(row["b"]) and not pd.isna(row["se"]):
            command = f"""Rscript {wrangle_script_path} \\
gwas.file={row[raw_path_column]} \\
LD.path={ref_panel_path} \\
SNP={row['snp']} A1={row['a1']} A2={row['a2']} N={row['N_col']} b={row['b']} se={row['se']} \\
output.file={output_path_final} \\
log.file={output_path_final}\n"""
        else:
            print(f"Skipping row {row['condition_label']}_{row['id']} because neither 'z' nor 'b'/'se' columns are filled properly.")
            return "Error"  # Return "Error" when the row is skipped
        
        with open(command_file_path, 'w') as command_file:
            command_file.write(command)
        return "True"  # Return "True" when the command is successfully generated

    def generate_and_save_commands():
        print(f"{ref_panel_path}")
        data = pd.read_csv(description_csv_path)
        
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)
        
        for index, row in data.iterrows():
            if str(row["wrangled"]) != "True":
                command_file_path = os.path.join(output_dir_path, f"{row['condition_label']}_{row['id']}_command.sh")
                wrangled_status = generate_wrangling_command(row, command_file_path)
                data.at[index, "wrangled"] = wrangled_status  # Update to "True" or "Error" based on result
            else:
                print(f"{row['condition_label']}_{row['id']} skipped, already wrangled")
        
        data.to_csv(description_csv_path, index=False)

    generate_and_save_commands()


wrangle_sumstats("/gpfs/projects/bsc02/mflores/gencor/config/config.yaml", "/gpfs/projects/bsc02/mflores/gencor/SumStats/Wrangled/commands")
# wrangle_sumstats("/home/maria/git/SOROLLA/config/config.yaml", "/home/maria/git/SOROLLA/SumStats/Wrangled/commands")

