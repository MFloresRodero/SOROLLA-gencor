import csv

# Path to your input CSV file
input_csv = "/home/maria/git/SOROLLA/scripts/CONTROLS/sumstats_test_ldsc.csv"

# Path where you want to save the output CSV file
output_csv = "/home/maria/git/SOROLLA/scripts/CONTROLS/test_ldsc_paired_datasets.csv"

# Read input CSV and extract dataset information
datasets = []
with open(input_csv, newline='') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')  # Change delimiter to comma
    for row in reader:
        condition = row['condition']
        dataset_name = row['dataset']
        munged_file_path = row['munged_path']
        wrangled_file_path = row['wrangled_path']
        datasets.append({'condition': condition, 'dataset_name': dataset_name, 'munged_file_path': munged_file_path, 'wrangled_file_path': wrangled_file_path})

# Generate paired combinations of datasets
paired_datasets = []
for i in range(len(datasets)):
    for j in range(i + 1, len(datasets)):
        paired_datasets.append((datasets[i], datasets[j]))

# Write paired datasets to output CSV file
with open(output_csv, 'w', newline='') as csvfile:
    fieldnames = ['condition_1', 'dataset_name_1', 'munged_file_path_1', 'wrangled_file_path_1', 'condition_2', 'dataset_name_2', 'munged_file_path_2', 'wrangled_file_path_2','ldsc','gnova','hdl']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for pair in paired_datasets:
        dataset_1, dataset_2 = pair
        writer.writerow({
            'condition_1': dataset_1['condition'],
            'dataset_name_1': dataset_1['dataset_name'],
            'munged_file_path_1': dataset_1['munged_file_path'],
            'wrangled_file_path_1': dataset_1['wrangled_file_path'],
            'condition_2': dataset_2['condition'],
            'dataset_name_2': dataset_2['dataset_name'],
            'munged_file_path_2': dataset_2['munged_file_path'],
            'wrangled_file_path_2': dataset_2['wrangled_file_path'],
            'ldsc': "False",
            'gnova': "False",
            'hdl': "False"
        })

print("Paired datasets generated and saved to", output_csv)
