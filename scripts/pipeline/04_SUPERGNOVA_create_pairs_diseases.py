import csv
import os
import yaml
import argparse


def main():
    parser = argparse.ArgumentParser(description="This script generates paired datasets from the catalog and saves them to an output CSV file.")
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
    input_csv = config["SumStats"]["description_csv"]
    output_csv = config["SumStats"]["supergnova_paired"]
    input_csv_path = os.path.join(base_path, sumstats_folder, input_csv)
    output_csv_path = os.path.join(base_path, sumstats_folder, output_csv)

    # Read input CSV and extract dataset information
    datasets = []
    with open(input_csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            datasets.append({
                'id': row['id'],
                'disease': row['disease'],
                'label': row['label'],
                'filename': row['filename'],
                'N_num': row['N_num'],
                f'{args.env}_raw_path': row[f'{args.env}_raw_path'],
                f'{args.env}_munged_path': row[f'{args.env}_munged_path'],
            })

    # Generate paired combinations of datasets
    paired_datasets = []
    for i in range(len(datasets)):
        for j in range(i + 1, len(datasets)):
            paired_datasets.append((datasets[i], datasets[j]))

    # Set to keep track of existing pairs
    existing_pairs = set()

    # Read existing pairs from the output CSV file if it exists
    if os.path.exists(output_csv_path):
        with open(output_csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_pairs.add((row['id_1'], row['id_2']))

    # Write paired datasets to output CSV file
    with open(output_csv_path, 'a', newline='') as csvfile:
        fieldnames = [
            'id_1', 'disease_1', 'label_1', 'filename_1', 'N_num_1', f'{args.env}_raw_path_1', f'{args.env}_munged_path_1',
            'id_2', 'disease_2', 'label_2', 'filename_2', 'N_num_2', f'{args.env}_raw_path_2', f'{args.env}_munged_path_2',
            'supergnova', 'supergnova_path' 
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header only if the file is empty
        if os.path.getsize(output_csv_path) == 0:
            writer.writeheader()

        for pair in paired_datasets:
            dataset_1, dataset_2 = pair
            row_data = {
                'id_1': dataset_1['id'],
                'disease_1': dataset_1['disease'],
                'label_1': dataset_1['label'],
                'filename_1': dataset_1['filename'],
                'N_num_1': dataset_1['N_num'],
                f'{args.env}_raw_path_1': dataset_1[f'{args.env}_raw_path'],
                f'{args.env}_munged_path_1': dataset_1[f'{args.env}_munged_path'],
                'id_2': dataset_2['id'],
                'disease_2': dataset_2['disease'],
                'label_2': dataset_2['label'],
                'filename_2': dataset_2['filename'],
                'N_num_2': dataset_2['N_num'],
                f'{args.env}_raw_path_2': dataset_2[f'{args.env}_raw_path'],
                f'{args.env}_munged_path_2': dataset_2[f'{args.env}_munged_path'],
                'supergnova': "False",
                'supergnova_path': 'NA'
            }
            
            # Debug print to check the keys
            print("Writing row:", row_data)

            if (dataset_1['id'], dataset_2['id']) not in existing_pairs:
                writer.writerow(row_data)
                existing_pairs.add((dataset_1['id'], dataset_2['id']))

    print("Paired datasets generated and saved to", output_csv_path)

if __name__ == "__main__":
    main()