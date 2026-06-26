import os
import pandas as pd
import argparse

def extract_genetic_correlation_results(file_path):
    # Parse the filename to extract id_1, label_1, id_2, and label_2
    file_name = os.path.basename(file_path)
    id_1, label_1, id_2, label_2 = file_name.replace(".log", "").split("_")

    result = {
        'id_1': id_1,
        'label_1': label_1,
        'id_2': id_2,
        'label_2': label_2
    }
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if "Summary of Genetic Correlation Results" in line:
                summary_lines = lines[i+2].split()
                # Assign the extracted values to the result dictionary
                result.update({
                    'rg': summary_lines[2],
                    'se': summary_lines[3],
                    'z': summary_lines[4],
                    'p': summary_lines[5],
                    # 'h2_1': summary_lines[6],
                    # 'h2_1_se': summary_lines[7],
                    # 'h2_2': summary_lines[8],
                    # 'h2_2_se': summary_lines[9],
                    'gcov_int': summary_lines[10],
                    'gcov_int_se': summary_lines[11]
                })
                break
        
        # There was an error, the intercept is not the heritability. Fix that extraction.        
        trait_count = 0
        for i, line in enumerate(lines):
            if "Total Observed scale h2:" in line:
                trait_count += 1
                parts = line.split()

                if trait_count == 1:
                    result["h2_1"] = parts[4]
                    result["h2_1_se"] = parts[5].strip("()")
                elif trait_count == 2:
                    result["h2_2"] = parts[4]
                    result["h2_2_se"] = parts[5].strip("()")
    
    return result

def extract_genetic_correlation_results_for_multiple_files(folder_path, output_csv_path, env):
    all_results = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".log"):
            file_path = os.path.join(folder_path, filename)
            result = extract_genetic_correlation_results(file_path)
            all_results.append(result)

    df = pd.DataFrame(all_results)
    df.to_csv(output_csv_path, index=False)
    print("Extracted results saved to:", output_csv_path)

def main():
    parser = argparse.ArgumentParser(description="This script extracts genetic correlation results from log files in a folder and saves them to a CSV file")
    parser.add_argument("--env", choices=["local", "remote", "shared"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    if args.env == "local":
        config_file = "/home/maria/git/SOROLLA/config/config.yaml"
        folder_path = "/home/maria/git/SOROLLA/Results/ldsc"
        output_csv_path = "/home/maria/git/SOROLLA/Results/ldsc_genetic_correlation.csv"

    elif args.env == "remote":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
        folder_path = "/gpfs/projects/bsc02/mflores/gencor/Results/ldsc"
        output_csv_path = "/gpfs/projects/bsc02/mflores/gencor/Results/ldsc_genetic_correlation.csv"
    elif args.env == "shared":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/JON/config.yaml"
        folder_path = "/gpfs/projects/bsc02/mflores/gencor/JON/results/ldsc"
        output_csv_path = "/gpfs/projects/bsc02/mflores/gencor/JON/results/ldsc_genetic_correlation.csv"
    else:
        raise ValueError("Environment not found, check if you specified the environment with --env or if the path is wrong")
    
    extract_genetic_correlation_results_for_multiple_files(folder_path, output_csv_path, args.env)

if __name__ == "__main__":
    main()




 # Function to extract data from ldsc .log
# import os
# import csv

# def extract_genetic_correlation_results(file_path):
#     result = {}
#     with open(file_path, 'r') as file:
#         lines = file.readlines()
#         # Iterate over the lines in the file
#         for i, line in enumerate(lines):
#             # Find the line containing "Summary of Genetic Correlation Results"
#             if "Summary of Genetic Correlation Results" in line:
#                 # Extract the relevant lines containing the summary
#                 summary_lines = lines[i+2:i+3]
#                 # Split the line to extract individual values
#                 values = summary_lines[0].split()
#                 # Assign the values to the result dictionary
#                 result['condition1'] = os.path.basename(file_path).split("_")[0]
#                 result['dataset1'] = os.path.basename(file_path).split("_")[1]
#                 result['condition2'] = os.path.basename(file_path).split("_")[2]
#                 result['dataset2'] = os.path.basename(file_path).split("_")[3].split(".")[0]
#                 result['rg'] = values[2]
#                 result['se'] = values[3]
#                 result['z'] = values[4]
#                 result['p'] = values[5]
#                 result['h2_obs'] = values[6]
#                 result['h2_obs_se'] = values[7]
#                 result['h2_int'] = values[8]
#                 result['h2_int_se'] = values[9]
#                 result['gcov_int'] = values[10]
#                 result['gcov_int_se'] = values[11]
#                 break
#     return result

# # Define the folder containing the log files
# folder_path = "/home/maria/git/SOROLLA/Results/ldsc"

# # Define the output CSV file path
# output_csv_path = "/home/maria/git/SOROLLA/Results/ldsc_genetic_correlation.csv"

# # Initialize a list to store extracted results
# all_results = []

# # Iterate over each file in the folder
# for filename in os.listdir(folder_path):
#     if filename.endswith(".log"):
#         file_path = os.path.join(folder_path, filename)
#         # Apply the extraction function to the file
#         result = extract_genetic_correlation_results(file_path)
#         # Append the extracted result to the list
#         all_results.append(result)

# # Write the extracted results to a CSV file with tab-separated values
# with open(output_csv_path, "w", newline="") as csvfile:
#     fieldnames = ['condition1', 'dataset1', 'condition2', 'dataset2', 'rg', 'se', 'z', 'p', 'h2_obs', 'h2_obs_se', 'h2_int', 'h2_int_se', 'gcov_int', 'gcov_int_se']
#     writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
#     writer.writeheader()
#     writer.writerows(all_results)

# print("Extracted results saved to:", output_csv_path)
