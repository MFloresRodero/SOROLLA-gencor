import os
import csv
import argparse

def extract_snp_info(log_file_path):
    snp_info = {}
    with open(log_file_path, 'r') as log_file:
        lines = log_file.readlines()

    for line in lines:
        if "Read reference panel LD Scores for" in line:
            num_snps = int(line.split()[-2])
            snp_info['initial_RP'] = num_snps
        elif "Read regression weight LD Scores for" in line:
            num_snps = int(line.split()[-2])
            snp_info['regr_weight'] = num_snps
        elif "After merging with reference panel LD" in line:
            num_snps = int(line.split()[-3])
            snp_info['merg_RP'] = num_snps
        elif "After merging with regression SNP LD" in line:
            num_snps = int(line.split()[-3])
            snp_info['merge_regr'] = num_snps
        elif "Read summary statistics for" in line:
            num_snps = int(line.split()[-2])
            snp_info['sumstats'] = num_snps
        elif "After merging with summary statistics" in line:
            num_snps = int(line.split()[-3])
            snp_info['merge_sumstats'] = num_snps
        elif "SNPs with valid alleles" in line:
            num_snps = int(line.split()[0])
            snp_info['valid_alleles_SNP'] = num_snps

    snp_info['File'] = os.path.basename(log_file_path)  # Extract filename

    return snp_info

def extract_snp_info_for_multiple_files(log_folder_path, output_csv_path, env):
    with open(output_csv_path, "w", newline="") as csvfile:
        fieldnames = ['File', 'initial_RP', 'regr_weight', 'merg_RP', 'merge_regr', 'sumstats', 'merge_sumstats', 'valid_alleles_SNP']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        
        for filename in os.listdir(log_folder_path):
            if filename.endswith(".log"):
                log_file_path = os.path.join(log_folder_path, filename)
                snp_info = extract_snp_info(log_file_path)
                writer.writerow(snp_info)
                print(f"SNPs for {filename} have been saved to output file.")

def main():
    parser = argparse.ArgumentParser(description="This script extracts SNP info from log files in a folder and saves it to a CSV file")
    parser.add_argument("--env", choices=["local", "remote"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    # Load configuration based on environment
    log_folder_path = "/home/maria/git/SOROLLA/Results/ldsc" if args.env == "local" else "/gpfs/projects/bsc02/mflores/gencor/Results/ldsc"
    output_csv_path = "/home/maria/git/SOROLLA/Results/ldsc_SNP_merge_remain_all.csv" if args.env == "local" else "/gpfs/projects/bsc02/mflores/gencor/Results/ldsc_SNP_merge_remain_all.csv"

    extract_snp_info_for_multiple_files(log_folder_path, output_csv_path, args.env)

if __name__ == "__main__":
    main()



# import os
# import csv

# def extract_snp_info(log_file_path):
#     snp_info = {}
#     with open(log_file_path, 'r') as log_file:
#         lines = log_file.readlines()

#     for line in lines:
#         if "Read reference panel LD Scores for" in line:
#             num_snps = int(line.split()[-2])
#             snp_info['initial_RP'] = num_snps
#         elif "Read regression weight LD Scores for" in line:
#             num_snps = int(line.split()[-2])
#             snp_info['regr_weight'] = num_snps
#         elif "After merging with reference panel LD" in line:
#             num_snps = int(line.split()[-3])
#             snp_info['merg_RP'] = num_snps
#         elif "After merging with regression SNP LD" in line:
#             num_snps = int(line.split()[-3])
#             snp_info['merge_regr'] = num_snps
#         elif "Read summary statistics for" in line:
#             num_snps = int(line.split()[-2])
#             snp_info['sumstats'] = num_snps
#         elif "After merging with summary statistics" in line:
#             num_snps = int(line.split()[-3])
#             snp_info['merge_sumstats'] = num_snps
#         elif "SNPs with valid alleles" in line:
#             num_snps = int(line.split()[0])
#             snp_info['valid_alleles_SNP'] = num_snps

#     snp_info['File'] = os.path.basename(log_file_path)  # Extract filename

#     return snp_info

# def extract_snp_info_for_multiple_files(log_folder_path, output_csv_path):
#     with open(output_csv_path, "w", newline="") as csvfile:
#         fieldnames = ['File', 'initial_RP', 'regr_weight', 'merg_RP', 'merge_regr', 'sumstats', 'merge_sumstats', 'valid_alleles_SNP']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
#         writer.writeheader()
        
#         for filename in os.listdir(log_folder_path):
#             if filename.endswith(".log"):
#                 log_file_path = os.path.join(log_folder_path, filename)
#                 snp_info = extract_snp_info(log_file_path)
#                 writer.writerow(snp_info)
#                 print(f"SNPs for {filename} have been saved to output file.")

# # Example usage:
# log_folder_path = "/home/maria/git/SOROLLA/Results/ldsc"
# output_csv_path = "/home/maria/git/SOROLLA/Results/ldsc_SNP_merge_remain_all.csv"
# extract_snp_info_for_multiple_files(log_folder_path, output_csv_path)