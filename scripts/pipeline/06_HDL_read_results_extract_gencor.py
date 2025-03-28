import os
import pandas as pd
import yaml
import argparse

def main():
    parser = argparse.ArgumentParser(description="This script extracts genetic correlation results from log files in a folder and saves them to a CSV file")
    parser.add_argument("--env", choices=["local", "remote"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    config_file = "/home/maria/git/SOROLLA/config/config.yaml" if args.env == "local" else "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
    
    # Load the configuration file
    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_file}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML configuration: {e}")
        exit(1)
    
    # Values from config
    base_path = config[args.env]["base_path"]
    results_folder = config["Results"]["results_folder"]
    hdl_output = config["Results"]["folder_hdl"]
    hdl_csv_output = config["Results"]["hdl_results_csv"]

    folder_path = f"{base_path}{results_folder}{hdl_output}"
    # output_csv_path = f"{base_path}{results_folder}{hdl_output}{hdl_csv_output}"
    output_csv_path = f"{base_path}{results_folder}{hdl_csv_output}"

    extract_all_HDL_genetic_correlation(folder_path, output_csv_path, args.env)


def extract_results_HDL(file_path):
    result = {}
    
    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        lines = file.readlines()
        # Iterate over the lines in the file
        for line in lines:
            if "Heritability of phenotype 1:" in line:
                h2_1 = line.split(':')[1].split('(')[0].strip()
                h2_1_se = line.split('(')[1].split(')')[0].strip()
                result['h2_1'] = h2_1
                result['h2_1_se'] = h2_1_se
            elif "Heritability of phenotype 2:" in line:
                h2_2 = line.split(':')[1].split('(')[0].strip()
                h2_2_se = line.split('(')[1].split(')')[0].strip()
                result['h2_2'] = h2_2
                result['h2_2_se'] = h2_2_se
            elif "Genetic Covariance:" in line:
                gcov = line.split(':')[1].split('(')[0].strip()
                gcov_se = line.split('(')[1].split(')')[0].strip()
                result['gcov'] = gcov
                result['gcov_se'] = gcov_se
            elif "Genetic Correlation:" in line:
                rg = line.split(':')[1].split('(')[0].strip()
                se = line.split('(')[1].split(')')[0].strip()
                result['rg'] = rg
                result['se'] = se
            elif line.startswith("P:"):
                p = line.split(':')[1].strip()
                result['p'] = p
            elif "SNPs in reference panel are available in GWAS" in line:
                if "GWAS 1" in line:
                    rp_gwas1_total = line.split()[0]
                    rp_gwas1_perc = line.split()[3].strip('()')
                    result['SNP_RP_GWAS1_TOTAL'] = rp_gwas1_total
                    result['SNP_RP_GWAS1_PERC'] = rp_gwas1_perc
                elif "GWAS 2" in line:
                    rp_gwas2_total = line.split()[0]
                    rp_gwas2_perc = line.split()[3].strip('()')
                    result['SNP_RP_GWAS2_TOTAL'] = rp_gwas2_total
                    result['SNP_RP_GWAS2_PERC'] = rp_gwas2_perc
            elif "SNPs were removed in GWAS" in line:
                if "GWAS 1" in line:
                    snp_rm_gwas1 = line.split()[0]
                    result['SNP_rm_GWAS1_Nmiss'] = snp_rm_gwas1
                elif "GWAS 2" in line:
                    snp_rm_gwas2 = line.split()[0]
                    result['SNP_rm_GWAS2_Nmiss'] = snp_rm_gwas2
            elif "The results were saved to" in line:
                result['output_file'] = os.path.basename(line.split('to')[1].strip())
                result['output_file_path'] = line.split('The results were saved to')[1].strip()

    return result


def extract_all_HDL_genetic_correlation(folder_path, output_csv_path, env):
    all_results = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".Rout"):
            file_path = os.path.join(folder_path, filename)
            result = extract_results_HDL(file_path)
            result['id_1'] = filename.split('_')[0]
            result['label_1'] = filename.split('_')[1]
            result['id_2'] = filename.split('_')[2]
            result['label_2'] = filename.split('_')[3].replace(".Rout","")
            all_results.append(result)
    
    df = pd.DataFrame(all_results)
    df.to_csv(output_csv_path, index = False)
    print("Extracted results saved to:", output_csv_path)




if __name__ == "__main__":
    main()
