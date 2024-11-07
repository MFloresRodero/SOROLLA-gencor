# Script to generate the beta from the odds ratio
## The beta will be named beta_added and will be in another column specifically for HDL and MR to consider.
## Further script modifications will be needed to avoid this because we are also going to calculate the se from beta_added.

import pandas as pd
import numpy as np
import yaml
import os
import argparse

def main():
     parser = argparse.ArgumentParser(description="calculate beta and standar error of beta when OR is present")
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
     print(f"Base path: {base_path}")

     sumstats_folder = config["SumStats"]["sumstats_folder"]
     description_csv = config["SumStats"]["description_csv"]
     description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)
     
	 #Call the function 
     write_beta_and_se(description_csv_path, args.env)



def calculate_beta_and_se(row, env):
    """
    beta = log(OR)
    Calculate the beta coefficient and the standard error for each SNP
    SE_beta = (SE.OddsRatio)/OddsRatio 
    or
    upperboundOR = OR + 1.96 * SE.OddsRatio >> upperboundbeta = log(upperboundOR)
    lowerboundOR = OR - 1.96 * SE.OddsRatio >> lowerboundbeta = log(lowerboundOR)
    SE_beta = (upperboundbeta - lowerboundbeta) / (2 * 1.96)
    """

    # Load the file path
    print("Loading path")
    file_path = row[f'{env}_raw_path']
    
    # Check file format
    if file_path.endswith('.gz'):
        compression = 'gzip'
    elif file_path.endswith('.tsv') or file_path.endswith('.txt'):
        compression = None
    else:
        print(f"Warning: Unsupported file format for file {file_path}.")
        return row

    # Read the file
    try:
        data = pd.read_csv(file_path, sep='\t', compression=compression)  # Assume tab-separated values for .tsv and .txt
    except EOFError:
        print(f"Warning: File {file_path} is corrupted or incomplete.")
        return row
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return row

    # Calculate beta and SE_beta
    print(f"Starting calculation for",row["id"]," ", row["label"])
    if pd.isna(row["b"]) and pd.notna(row["OR"]) and pd.notna(row["se"]):
        beta_added = np.log(row["OR"])
        data["beta_added"] = beta_added

        upperboundOR = row["OR"] + 1.96 * row["se"]
        lowerboundOR = row["OR"] - 1.96 * row["se"]
        
        upperboundbeta = np.log(upperboundOR)
        lowerboundbeta = np.log(lowerboundOR)
        
        sebeta = (upperboundbeta - lowerboundbeta) / (2 * 1.96)
        data["sebeta"] = sebeta

        # Save the updated DataFrame
        print("Saving the updated datafile")
        try:
            if compression == 'gzip':
                data.to_csv(file_path, sep='\t', index=False, compression='gzip')
            else:
                data.to_csv(file_path, sep='\t', index=False)
            print(f"Dataset {file_path} has been modified with beta and SE columns.")
            
            # Update the row with 'beta_added'
            print("updating the csv")
            row['b'] = 'beta_added'
            print(f"Finished with", row["label"])
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
    else:
        print(f"{row['id']} already contains a beta column")
    return row


def write_beta_and_se(csv_file_path, env):
    df = pd.read_csv(csv_file_path)
    df = df.apply(lambda row: calculate_beta_and_se(row, env), axis=1)
    df.to_csv(csv_file_path, index=False, sep='\t')  # Ensure using tab separator for consistency


if __name__ == "__main__":
    main()