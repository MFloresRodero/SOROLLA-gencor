# Function to extract data from ldsc .log
import os
import csv

def extract_genetic_correlation_results(file_path):
    result = {}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        # Iterate over the lines in the file
        for i, line in enumerate(lines):
            # Find the line containing "Summary of Genetic Correlation Results"
            if "Summary of Genetic Correlation Results" in line:
                # Extract the relevant lines containing the summary
                summary_lines = lines[i+2:i+3]
                # Split the line to extract individual values
                values = summary_lines[0].split()
                # Assign the values to the result dictionary
                result['condition1'] = os.path.basename(file_path).split("_")[0]
                result['dataset1'] = os.path.basename(file_path).split("_")[1]
                result['condition2'] = os.path.basename(file_path).split("_")[2]
                result['dataset2'] = os.path.basename(file_path).split("_")[3].split(".")[0]
                result['rg'] = values[2]
                result['se'] = values[3]
                result['z'] = values[4]
                result['p'] = values[5]
                result['h2_obs'] = values[6]
                result['h2_obs_se'] = values[7]
                result['h2_int'] = values[8]
                result['h2_int_se'] = values[9]
                result['gcov_int'] = values[10]
                result['gcov_int_se'] = values[11]
                break
    return result

# Define the folder containing the log files
folder_path = "/home/maria/git/SOROLLA/Results/CONTROLS"

# Define the output CSV file path
output_csv_path = "/home/maria/git/SOROLLA/Results/CONTROLS/ldsc_genetic_correlation.csv"

# Initialize a list to store extracted results
all_results = []

# Iterate over each file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".log"):
        file_path = os.path.join(folder_path, filename)
        # Apply the extraction function to the file
        result = extract_genetic_correlation_results(file_path)
        # Append the extracted result to the list
        all_results.append(result)

# Write the extracted results to a CSV file with tab-separated values
with open(output_csv_path, "w", newline="") as csvfile:
    fieldnames = ['condition1', 'dataset1', 'condition2', 'dataset2', 'rg', 'se', 'z', 'p', 'h2_obs', 'h2_obs_se', 'h2_int', 'h2_int_se', 'gcov_int', 'gcov_int_se']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
    writer.writeheader()
    writer.writerows(all_results)

print("Extracted results saved to:", output_csv_path)
