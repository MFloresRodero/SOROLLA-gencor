import os
import yaml
import argparse
import subprocess
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="This script runs the heritability LDSC software on all the files")
    parser.add_argument("--env", choices=["local", "remote", "shared"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    if args.env == "local":
        config_file = "/home/maria/git/SOROLLA/config/config.yaml"
    elif args.env == "remote":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
    elif args.env == "shared":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/JON/config.yaml"
    else:
        raise ValueError("Environment not found, check if you specified the environment with --env or if the path is wrong")

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading configuration: {e}")
        exit(1)

    # Paths
    base_path = config[args.env]["base_path"]
    print(f"Base path: {base_path}")

    sumstats_folder = config["SumStats"]["sumstats_folder"]
    print(f"Sumstats folder: {sumstats_folder}")

    description_csv = config["SumStats"]["description_csv"]
    print(f"Description CSV: {description_csv}")

    input_csv = os.path.join(base_path, sumstats_folder, description_csv)
    print(f"Input CSV path: {input_csv}")

    heritability_checkpoint = config["SumStats"]["ldsc_heritability_checkpoint"]
    print(f"Heritability checkpoint: {heritability_checkpoint}")

    output_csv = os.path.join(base_path, sumstats_folder, heritability_checkpoint)
    print(f"Output CSV path: {output_csv}")

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

    ldsc_output_location = config["Results"]["folder_ldsc_heritability"]
    print(f"LDSC output location: {ldsc_output_location}")

    output_path = os.path.join(base_path, ldsc_output_folder, ldsc_output_location)
    print(f"Full output path: {output_path}")

    ld_scores_folder = config["reference_genomes"]["reference_genomes_folder"]
    print(f"LD scores folder: {ld_scores_folder}")

    ld_scores = config["reference_genomes"]["eur_w_ld_chr"]
    print(f"LD scores: {ld_scores}")

    ld_path = os.path.join(base_path, ld_scores_folder, ld_scores)
    print(f"Full LD path: {ld_path}")

    os.makedirs(output_path, exist_ok=True)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    # ✅ Crear carpeta si no existe
    os.makedirs(output_path, exist_ok=True)

    run_ldsc_from_csv(input_csv, output_csv, args.env, singularity_env_path, ldsc_script_path, ld_path, output_path)

def run_ldsc_from_csv(input_csv, output_csv, env, singularity_env_path, ldsc_script_path, ld_path, output_path):
    input_data = pd.read_csv(input_csv)

    # Load or initialize checkpoint
    if os.path.exists(output_csv):
        checkpoint = pd.read_csv(output_csv)
    else:
        checkpoint = pd.DataFrame(columns=["id", "label", "heritability_done"])

    for _, row in input_data.iterrows():
        id_val = row["id"]
        label_val = row["label"]

        result = run_ldsc(row, env, singularity_env_path, ldsc_script_path, ld_path, output_path)

        # Update or append result in checkpoint
        mask = (checkpoint["id"] == id_val) & (checkpoint["label"] == label_val)
        if mask.any():
            checkpoint.loc[mask, "heritability_done"] = result
        else:
            # ✅ Usar pd.concat en lugar de append
            new_row = pd.DataFrame([{
                "id": id_val,
                "label": label_val,
                "heritability_done": result
            }])
            checkpoint = pd.concat([checkpoint, new_row], ignore_index=True)

    # Save updated checkpoint
    checkpoint.to_csv(output_csv, index=False)

def run_ldsc(row, env, singularity_env_path, ldsc_script_path, ld_path, output_path):
    try:
        id = row["id"]
        label= row["label"]
        raw_file_path = row[f'{env}_munged_path']
        out_file = os.path.join(output_path, f"{row['id']}_{row['label']}")
    except Exception as e:
        print(f"Error unpacking row: {row} - {e}")
        return "Error"

    if pd.isna(row[f'{env}_munged_path']):
        print(f"One of the raw file paths is empty, skipping LDSC for row: {row}")
        return "False"

    print(f"Running LDSC for: {id} - {label}")
    try:
        subprocess.run([
            'singularity', 'exec', singularity_env_path, 'python2',
            ldsc_script_path,
            '--h2', f"{raw_file_path}",
            '--ref-ld-chr', ld_path,
            '--w-ld-chr', ld_path,
            '--out', out_file
        ], check=True)
        return "True"
    except subprocess.CalledProcessError:
        print(f"Error running LDSC for: {id} - {label}")
        return "Error"

if __name__ == "__main__":
    main()
