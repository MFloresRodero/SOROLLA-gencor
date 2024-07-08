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
    output_csv = config["SumStats"]["paired_data"]
    input_csv_path = os.path.join(base_path, sumstats_folder, config["SumStats"]["description_csv"])
    output_csv_path = os.path.join(base_path, sumstats_folder, config["SumStats"]["paired_data"])

    # Read input CSV and extract dataset information
    datasets = []
    with open(input_csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            datasets.append({
                'id': row['id'],
                'condition_label': row['condition_label'],
                'label': row['label'],
                'filename': row['filename'],
                f'{args.env}_munged_path': row[f'{args.env}_munged_path'],
                f'{args.env}_wrangled_path': row[f'{args.env}_wrangled_path']
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
            'id_1', 'condition_label_1', 'label_1', 'filename_1', f'{args.env}_munged_path_1', f'{args.env}_wrangled_path_1',
            'id_2', 'condition_label_2', 'label_2', 'filename_2', f'{args.env}_munged_path_2', f'{args.env}_wrangled_path_2',
            'ldsc', 'ldsc_path', 'gnova', 'gnova_path', 'hdl', 'hdl_path'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header only if the file is empty
        if os.path.getsize(output_csv_path) == 0:
            writer.writeheader()

        for pair in paired_datasets:
            dataset_1, dataset_2 = pair
            if (dataset_1['id'], dataset_2['id']) not in existing_pairs:
                writer.writerow({
                    'id_1': dataset_1['id'],
                    'condition_label_1': dataset_1['condition_label'],
                    'label_1': dataset_1['label'],
                    'filename_1': dataset_1['filename'],
                    f'{args.env}_munged_path_1': dataset_1[f'{args.env}_munged_path'],
                    f'{args.env}_wrangled_path_1': dataset_1[f'{args.env}_wrangled_path'],
                    'id_2': dataset_2['id'],
                    'condition_label_2': dataset_2['condition_label'],
                    'label_2': dataset_2['label'],
                    'filename_2': dataset_2['filename'],
                    f'{args.env}_munged_path_2': dataset_2[f'{args.env}_munged_path'],
                    f'{args.env}_wrangled_path_2': dataset_2[f'{args.env}_wrangled_path'],
                    'ldsc': "False",
                    'ldsc_path': "NA",
                    'gnova': "False",
                    'gnova_path': "NA",
                    'hdl': "False",
                    'hdl_path': "NA"
                })
                existing_pairs.add((dataset_1['id'], dataset_2['id']))

    print("Paired datasets generated and saved to", output_csv_path)

if __name__ == "__main__":
    main()


# import csv
# import os

# # Path to your input CSV file
# input_csv = "/home/maria/git/SOROLLA/SumStats/final_sumstats_description.csv"

# # Path where you want to save the output CSV file
# output_csv = "/home/maria/git/SOROLLA/SumStats/paired_datasets.csv"

# # Read input CSV and extract dataset information
# datasets = []
# with open(input_csv, newline='') as csvfile:
#     reader = csv.DictReader(csvfile, delimiter=',')
#     for row in reader:
#         datasets.append({
#             'id': row['id'],
#             'condition_label': row['condition_label'],
#             'label': row['label'],
#             'filename': row['filename'],
#             'munged_file_path': row['munged_path'],
#             'wrangled_file_path': row['wrangled_path']
#         })

# # Generate paired combinations of datasets
# paired_datasets = []
# for i in range(len(datasets)):
#     for j in range(i + 1, len(datasets)):
#         paired_datasets.append((datasets[i], datasets[j]))

# # Set to keep track of existing pairs
# existing_pairs = set()

# # Read existing pairs from the output CSV file if it exists
# if os.path.exists(output_csv):
#     with open(output_csv, 'r', newline='') as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             existing_pairs.add((row['id_1'], row['id_2']))

# # Write paired datasets to output CSV file
# with open(output_csv, 'a', newline='') as csvfile:
#     fieldnames = [
#         'id_1', 'condition_label_1', 'label_1', 'filename_1', 'munged_file_path_1', 'wrangled_file_path_1',
#         'id_2', 'condition_label_2', 'label_2', 'filename_2', 'munged_file_path_2', 'wrangled_file_path_2',
#         'ldsc', 'ldsc_path', 'gnova', 'gnova_path', 'hdl', 'hdl_path'
#     ]
#     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#     # Write header only if the file is empty
#     if os.path.getsize(output_csv) == 0:
#         writer.writeheader()

#     for pair in paired_datasets:
#         dataset_1, dataset_2 = pair
#         if (dataset_1['id'], dataset_2['id']) not in existing_pairs:
#             writer.writerow({
#                 'id_1': dataset_1['id'],
#                 'condition_label_1': dataset_1['condition_label'],
#                 'label_1': dataset_1['label'],
#                 'filename_1': dataset_1['filename'],
#                 'munged_file_path_1': dataset_1['munged_file_path'],
#                 'wrangled_file_path_1': dataset_1['wrangled_file_path'],
#                 'id_2': dataset_2['id'],
#                 'condition_label_2': dataset_2['condition_label'],
#                 'label_2': dataset_2['label'],
#                 'filename_2': dataset_2['filename'],
#                 'munged_file_path_2': dataset_2['munged_file_path'],
#                 'wrangled_file_path_2': dataset_2['wrangled_file_path'],
#                 'ldsc': row.get('ldsc', "False"),
#                 'ldsc_path': row.get('ldsc_path', "NA"),
#                 'gnova': row.get('gnova', "False"),
#                 'gnova_path': row.get('gnova_path', "NA"),
#                 'hdl': row.get('hdl', "False"),
#                 'hdl_path': row.get('hdl_path', "NA")
#             })
#             existing_pairs.add((dataset_1['id'], dataset_2['id']))

# print("Paired datasets generated and saved to", output_csv)
