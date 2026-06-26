import pandas as pd
import yaml
import argparse
import os


def main():
    parser = argparse.ArgumentParser(
        description="This script creates the my_run.txt file for supergnova."
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

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
            print(f"Successfully loaded config file: {config_file}")
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_file}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML configuration: {e}")
        exit(1)

    # Configuration
    base_path = config[args.env]["base_path"]
    print(f"Base path: {base_path}")

    sumstats_folder = config["SumStats"]["sumstats_folder"]
    print(f"Sumstats folder: {sumstats_folder}")

    supergnova_file = config["SumStats"]["paired_data"]
    print(f"Supergnova input CSV: {supergnova_file}")

    input_csv = os.path.join(base_path, sumstats_folder, supergnova_file)
    print(f"Input CSV path: {input_csv}")

    # Check if input CSV exists
    if os.path.exists(input_csv):
        print(f"FOUND: Input CSV file exists at {input_csv}")
    else:
        print(f"ERROR: Input CSV file not found at {input_csv}")
        exit(1)

    # Script path
    script = config["Scripts"]["pipeline"]["supergnova_genetic_correlation_batches"]

    if os.path.isabs(script):
        script_path = os.path.join(base_path, script.lstrip("/"))
    else:
        script_path = os.path.join(base_path, script)

    print(f"Script path: {script_path}")

    # Check if script exists
    if os.path.exists(script_path):
        print(f"FOUND: Script file exists at {script_path}")
    else:
        print(f"WARNING: Script file not found at {script_path}")

    # Jobs folder
    jobs_folder = config["Scripts"]["JOBS_MN"]["jobs_mn"]

    if os.path.isabs(jobs_folder):
        jobs_folder_path = os.path.join(base_path, jobs_folder.lstrip("/"))
    else:
        jobs_folder_path = os.path.join(base_path, jobs_folder)

    print(f"Jobs folder path: {jobs_folder_path}")

    # Create jobs folder if it does not exist
    os.makedirs(jobs_folder_path, exist_ok=True)
    print(f"ENSURED: Jobs folder exists at {jobs_folder_path}")

    # Batch output directory
    batch_output_dir = os.path.join(jobs_folder_path, "batch_files")

    # Create batch directory if it doesn't exist
    os.makedirs(batch_output_dir, exist_ok=True)
    print(f"ENSURED: Batch directory exists at {batch_output_dir}")

    # Main command output file path
    my_run_output = os.path.join(jobs_folder_path, "supergnova_my_run.txt")

    # Ensure parent folder exists
    os.makedirs(os.path.dirname(my_run_output), exist_ok=True)

    print(f"Main run file path: {my_run_output}")

    # Read the main CSV file
    csv_data = pd.read_csv(input_csv)

    if "batch" not in csv_data.columns:
        raise ValueError("The input CSV does not contain a 'batch' column.")

    csv_data["batch"] = csv_data["batch"].astype(int)

    batch_ids = sorted(csv_data["batch"].dropna().unique())
    print(f"Found {len(batch_ids)} batches in the input CSV")

    # Create/update batch files
    for batch in batch_ids:
        batch_file_path = os.path.join(batch_output_dir, f"batch_{batch}.csv")
        print(f"\nProcessing batch {batch}...")

        # Filter data for this batch
        batch_data = csv_data[csv_data["batch"] == batch]
        print(f"Batch {batch} contains {len(batch_data)} rows")

        if os.path.exists(batch_file_path):
            print(f"FOUND: Batch file exists at {batch_file_path}")
            existing_data = pd.read_csv(batch_file_path)
            print(f"Existing file contains {len(existing_data)} rows")

            identifying_columns = ["id_1", "id_2"]

            existing_rows = set(existing_data[identifying_columns].apply(tuple, axis=1))
            new_rows = set(batch_data[identifying_columns].apply(tuple, axis=1))

            rows_to_add = new_rows - existing_rows

            if rows_to_add:
                rows_to_add_df = batch_data[
                    batch_data[identifying_columns].apply(tuple, axis=1).isin(rows_to_add)
                ]

                updated_data = pd.concat([existing_data, rows_to_add_df], ignore_index=True)
                updated_data.to_csv(batch_file_path, index=False)

                print(f"UPDATED: Added {len(rows_to_add_df)} new rows to {batch_file_path}")
                print(f"File now contains {len(updated_data)} rows")
            else:
                print(f"NO CHANGE: No new rows to add to {batch_file_path}")

        else:
            print(f"NOT FOUND: Batch file doesn't exist at {batch_file_path}")
            print(f"CREATING: New batch file at {batch_file_path}")

            batch_data.to_csv(batch_file_path, index=False)

            print(f"CREATED: New batch file at {batch_file_path} with {len(batch_data)} rows")

    # Create/update the main run file
    print(f"\nProcessing main run file at {my_run_output}")

    existing_commands = set()

    if os.path.exists(my_run_output):
        print(f"FOUND: Run file exists at {my_run_output}")

        with open(my_run_output, "r") as file:
            existing_commands = set(line.strip() for line in file if line.strip())

        print(f"Run file contains {len(existing_commands)} existing commands")

    else:
        print(f"NOT FOUND: Run file doesn't exist at {my_run_output}")
        print("Will create new run file")

    commands_added = 0

    with open(my_run_output, "a") as output_file:
        for batch in batch_ids:
            command = f"python3 {script_path} --env {args.env} --batch {batch}"

            if command not in existing_commands:
                output_file.write(command + "\n")
                commands_added += 1
                print(f"ADDED: Command for batch {batch}")
            else:
                print(f"SKIPPED: Command for batch {batch} already exists")

    print(f"\nSummary: Added {commands_added} new commands to {my_run_output}")
    print("Script execution completed successfully")


if __name__ == "__main__":
    main()