import csv
import os
import yaml
import argparse

def main():
    parser = argparse.ArgumentParser(description="This script generates paired datasets from the catalog and saves them to an output CSV file.")
    parser.add_argument("--env", choices=["local", "remote"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    config_file = "/home/maria/git/SOROLLA/config/config.yaml" if args.env == "local" else "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_file}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML configuration: {e}")
        exit(1)

    base_path = config[args.env]["base_path"]
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    input_csv = config["SumStats"]["description_csv"]
    output_csv = config["SumStats"]["paired_data"]
    input_csv_path = os.path.join(base_path, sumstats_folder, input_csv)
    output_csv_path = os.path.join(base_path, sumstats_folder, output_csv)

    datasets = []
    with open(input_csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            datasets.append({
                'id': row['id'],
                'disease': row['disease'],
                'label': row['label'],
                'filename': row['filename'],
                f'{args.env}_raw_path': row[f'{args.env}_raw_path'],
                f'{args.env}_munged_path': row[f'{args.env}_munged_path'],
                f'{args.env}_wrangled_path': row[f'{args.env}_wrangled_path']
            })

    paired_datasets = []
    for i in range(len(datasets)):
        for j in range(i, len(datasets)):  # Start from i to include self-pairing
            paired_datasets.append((datasets[i], datasets[j]))

    existing_pairs = set()

    if os.path.exists(output_csv_path):
        with open(output_csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_pairs.add((row['id_1'], row['id_2']))

    with open(output_csv_path, 'a', newline='') as csvfile:
        fieldnames = [
            'id_1', 'disease_1', 'label_1', 'filename_1', f'{args.env}_raw_path_1', f'{args.env}_munged_path_1', f'{args.env}_wrangled_path_1',
            'id_2', 'disease_2', 'label_2', 'filename_2', f'{args.env}_raw_path_2', f'{args.env}_munged_path_2', f'{args.env}_wrangled_path_2',
            'ldsc', 'ldsc_path', 'hdl', 'hdl_path'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if os.path.getsize(output_csv_path) == 0:
            writer.writeheader()

        for pair in paired_datasets:
            dataset_1, dataset_2 = pair
            if (dataset_1['id'], dataset_2['id']) not in existing_pairs:
                row_data = {
                    'id_1': dataset_1['id'],
                    'disease_label_1': dataset_1['disease_label'],
                    'label_1': dataset_1['label'],
                    'filename_1': dataset_1['filename'],
                    f'{args.env}_raw_path_1': dataset_1[f'{args.env}_raw_path'],
                    f'{args.env}_munged_path_1': dataset_1[f'{args.env}_munged_path'],
                    f'{args.env}_wrangled_path_1': dataset_1[f'{args.env}_wrangled_path'],
                    'id_2': dataset_2['id'],
                    'disease_label_2': dataset_2['disease_label'],
                    'label_2': dataset_2['label'],
                    'filename_2': dataset_2['filename'],
                    f'{args.env}_raw_path_2': dataset_2[f'{args.env}_raw_path'],
                    f'{args.env}_munged_path_2': dataset_2[f'{args.env}_munged_path'],
                    f'{args.env}_wrangled_path_2': dataset_2[f'{args.env}_wrangled_path'],
                    'ldsc': "False",
                    'ldsc_path': "NA",
                    'hdl': "False",
                    'hdl_path': "NA"
                }

                writer.writerow(row_data)
                existing_pairs.add((dataset_1['id'], dataset_2['id']))

    print("Paired datasets generated and saved to", output_csv_path)


if __name__ == "__main__":
    main()
