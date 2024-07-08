### CREATE FOLDERS ACCORDING TO THE EXCELL_SUMSTATS_DESCRIPTION.CSV FILE
##### DO NOT RUN SEVERAL TIMES TO AVOID OVERWRITING

import os
import pandas as pd

# Read the CSV file
csv_file_path = '/home/maria/git/SOROLLA/SumStats/excell_sumstats_description.csv' #Add  own file path
df = pd.read_csv(csv_file_path)

# Extract unique labels from 'condition_label' column
unique_labels = df['condition_label'].unique()

# Define the base directories
base_dirs = ['/home/maria/git/SOROLLA/SumStats/RAW/', '/home/maria/git/SOROLLA/SumStats/Munged/']# , '/SumStats/Munged2/']

# Create directories for each unique label
for label in unique_labels:
    for base_dir in base_dirs:
        folder_path = os.path.join(base_dir, label)
        os.makedirs(folder_path, exist_ok=True)
        print(f'Created directory: {folder_path}')