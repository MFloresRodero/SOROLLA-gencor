import os
import pandas as pd
import argparse

def extract_genetic_correlation_results(file_path):
    file_name = os.path.basename(file_path)
    file_stem = file_name.replace(".log", "")

    id, label = file_stem.rsplit("_", 1)

    result = {
        'id': id,
        'label': label
    }

    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if "Total Observed scale h2:" in line:
                parts = line.split()
                result["h2"] = parts[4]
                result["h2_se"] = parts[5].strip("()")
            elif "Lambda GC:" in line:
                parts = line.split()
                result["lambda_gc"] = parts[2]
            elif "Mean Chi^2:" in line:
                parts = line.split()
                result["mean_chi2"] = parts[2]
            elif "Intercept:" in line:
                parts = line.split()
                result["intercept"] = parts[1]
                result["intercept_se"] = parts[2].strip("()")
            elif "Ratio:" in line:
                parts = line.split()
                result["ratio"] = parts[1]
                result["ratio_se"] = parts[2].strip("()")

    return result

def extract_genetic_correlation_results_for_multiple_files(folder_path, output_csv_path, env):
    all_results = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".log"):
            file_path = os.path.join(folder_path, filename)
            result = extract_genetic_correlation_results(file_path)
            all_results.append(result)

    df = pd.DataFrame(all_results)
    df["zscore_heritability"] = df.apply(lambda x: (float(x["h2"])**2) / (float(x["h2_se"])**2), axis=1)
    df.to_csv(output_csv_path, index=False)
    print("Extracted results saved to:", output_csv_path)


def main():
    parser = argparse.ArgumentParser(description="This script extracts genetic correlation results from log files in a folder and saves them to a CSV file")
    parser.add_argument("--env", choices=["local", "remote", "shared"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    if args.env == "local":
        config_file = "/home/maria/git/SOROLLA/config/config.yaml"
        folder_path = "/home/maria/git/SOROLLA/Results/ldsc_heritability"
        output_csv_path = "/home/maria/git/SOROLLA/Results/ldsc_heritability.csv"

    elif args.env == "remote":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
        folder_path = "/gpfs/projects/bsc02/mflores/gencor/Results/ldsc_heritability"
        output_csv_path = "/gpfs/projects/bsc02/mflores/gencor/Results/ldsc_heritability.csv"
    elif args.env == "shared":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/JON/config.yaml"
        folder_path = "/gpfs/projects/bsc02/mflores/gencor/JON/results/ldsc_heritability"
        output_csv_path = "/gpfs/projects/bsc02/mflores/gencor/JON/results/ldsc_heritability.csv"
    else:
        raise ValueError("Environment not found, check if you specified the environment with --env or if the path is wrong")

    extract_genetic_correlation_results_for_multiple_files(folder_path, output_csv_path, args.env)

if __name__ == "__main__":
    main()

