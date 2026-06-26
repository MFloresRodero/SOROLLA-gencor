import csv
import os
import yaml
import argparse

def main():
    parser = argparse.ArgumentParser(description="This script generates paired datasets from the catalog and saves them to an output CSV file.")
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
    print(f"Input CSV path: {input_csv_path}")

    output_csv_path = os.path.join(base_path, sumstats_folder, output_csv)
    print(f"Output CSV path: {output_csv_path}")

    datasets = []
    with open(input_csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            datasets.append({
                'id': row['id'],
                'disease': row['disease'],
                'label': row['label'],
                'N_num': row['N_num'],
                f'{args.env}_munged_path': row[f'{args.env}_munged_path'],
                f'{args.env}_wrangled_path': row[f'{args.env}_wrangled_path']
            })

    paired_datasets = []
    for i in range(len(datasets)):
        for j in range(i, len(datasets)):  # Start from i to include self-pairing
            paired_datasets.append((datasets[i], datasets[j]))

    #Updated: added batches here
    existing_pairs = set()
    max_batch = 0
    existing_pairs = set()

    if os.path.exists(output_csv_path):
        with open(output_csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_pairs.add((row['id_1'], row['id_2']))
                #Add the updating batch number in case 
                if 'batch' in row and row['batch'] != '':
                    try:
                        max_batch = max(max_batch, int(row['batch']))
                    except ValueError:
                        pass

    # CHANGED:
    # Old: rows were written directly inside the final loop.
    # New: first collect only the NEW rows in a list.
    # Batch numbers depend on the position among only the newly added rows, not among all possible pairs.
    new_rows = []
    
    for pair in paired_datasets:
        dataset_1, dataset_2 = pair
        if (dataset_1['id'], dataset_2['id']) not in existing_pairs:
            row_data = {
                'id_1': dataset_1['id'],
                'disease_1': dataset_1['disease'],
                'label_1': dataset_1['label'],
                'N_num_1': dataset_1['N_num'],
                f'{args.env}_munged_path_1': dataset_1[f'{args.env}_munged_path'],
                f'{args.env}_wrangled_path_1': dataset_1[f'{args.env}_wrangled_path'],
                'id_2': dataset_2['id'],
                'disease_2': dataset_2['disease'],
                'label_2': dataset_2['label'],
                'N_num_2': dataset_2['N_num'],
                f'{args.env}_munged_path_2': dataset_2[f'{args.env}_munged_path'],
                f'{args.env}_wrangled_path_2': dataset_2[f'{args.env}_wrangled_path'],
                'ldsc': "False",
                'hdl': "False",
                'supergnova': "False",
            }
            new_rows.append(row_data)

    # CHANGED:
    # New: assign one batch number every 50 new rows.
    for idx, row_data in enumerate(new_rows):
        row_data['batch'] = max_batch + (idx // 50) + 1
    
    with open(output_csv_path, 'a', newline='') as csvfile:
        fieldnames = [
            'id_1', 'disease_1', 'label_1', 'N_num_1', f'{args.env}_munged_path_1', f'{args.env}_wrangled_path_1',
            'id_2', 'disease_2', 'label_2', 'N_num_2', f'{args.env}_munged_path_2', f'{args.env}_wrangled_path_2',
            'ldsc', 'hdl', 'supergnova', 'batch']
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if os.path.getsize(output_csv_path) == 0:
            writer.writeheader()

     # CHANGED:
        # Old: rows were written directly inside the pair loop.
        # New: write the already prepared new_rows list.
        for row_data in new_rows:
            writer.writerow(row_data)
            existing_pairs.add((row_data['id_1'], row_data['id_2']))

    print("Paired datasets generated and saved to", output_csv_path)

        # for pair in paired_datasets:
        #     dataset_1, dataset_2 = pair
        #     if (dataset_1['id'], dataset_2['id']) not in existing_pairs:
        #         row_data = {
        #             'id_1': dataset_1['id'],
        #             'disease_1': dataset_1['disease'],
        #             'label_1': dataset_1['label'],
        #             'N_num_1': dataset_1['N_num'],
        #             f'{args.env}_munged_path_1': dataset_1[f'{args.env}_munged_path'],
        #             f'{args.env}_wrangled_path_1': dataset_1[f'{args.env}_wrangled_path'],
        #             'id_2': dataset_2['id'],
        #             'disease_2': dataset_2['disease'],
        #             'label_2': dataset_2['label'],
        #             'N_num_2': dataset_2['N_num'],
        #             f'{args.env}_munged_path_2': dataset_2[f'{args.env}_munged_path'],
        #             f'{args.env}_wrangled_path_2': dataset_2[f'{args.env}_wrangled_path'],
        #             'ldsc': "False",
        #             'hdl': "False",
        #             'supergnova': "False",
        #                             #add batch number here.               
        #                              }

        #         writer.writerow(row_data)
        #         existing_pairs.add((dataset_1['id'], dataset_2['id']))


if __name__ == "__main__":
    main()
