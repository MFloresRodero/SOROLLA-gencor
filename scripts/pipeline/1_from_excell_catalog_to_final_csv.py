import pandas as pd
import os
import yaml
import argparse

def main():
    parser = argparse.ArgumentParser(description="This script takes the data from the catalog and transform it into a data description file defining all the paths and whether the data has been run through certain softwares. It also adds an N column by default in case there is not one.")
    parser.add_argument("--env", choices=["local", "remote"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    # Load data based on environment
    if args.env == "local":
        config_file = "/home/maria/git/SOROLLA/config/config.yaml"
    else:
        config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"

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
    raw_catalog = config["SumStats"]["raw_catalog"]
    description_csv = config["SumStats"]["description_csv"]
    raw_folder = config["SumStats"]["raw_folder"]

    # Construct paths
    raw_catalog_path = os.path.join(base_path, sumstats_folder, raw_catalog)
    description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)

    desired_columns = ["id", "condition_label", "label", "filename", 
                   "ref_genome", "snp", "a1", "a2", "frq", "FRQ_U", "FRQ_A", 
                   "z", "b", "OR", "se", "p", "N_col", "N_num", "Nca_col", 
                   "Nca_val", "Nco_col", "Nco_val", "INFO", "ignore"]
    
    # Call create_and_append_dataframe function with appropriate arguments
    create_and_append_dataframe(raw_catalog_path, description_csv_path, desired_columns, config)


def create_and_append_dataframe(input_file, output_file, desired_columns, config, munged_default="False", wrangled_default="False", munged_path_default="NA", wrangled_path_default="NA"):
    """
    Creates and appends data to a pandas DataFrame.

    Args:
      input_file (str): Path to the input CSV file.
      output_file (str): Path to the output CSV file.
      desired_columns (list): List of column names to keep from the input CSV.
      munged_default (str, optional): Default value for the 'munged' column ("False" by default).
      wrangled_default (str, optional): Default value for the 'wrangled' column ("False" by default).
      munged_path_default (str, optional): Default value for the 'munged_path' column ("NA" by default).
      wrangled_path_default (str, optional): Default value for the 'wrangled_path' column ("NA" by default).
    """

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist.")
        return

    # Read input data using pandas
    try:
        df_in = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found.")
        return
    except pd.errors.ParserError as e:
        print(f"Error parsing input CSV: {e}")
        return

    # Select desired columns
    df = df_in[desired_columns]
    
    # Convert all columns to strings
    df['Nca_val'] = df['Nca_val'].apply(lambda x: str(int(float(x))) if pd.notna(x) else x)
    df['Nco_val'] = df['Nco_val'].apply(lambda x: str(int(float(x))) if pd.notna(x) else x)


    # Add new columns with defaults
    df['local_raw_path'] = df.apply(lambda row: os.path.join(config['local']['base_path'], config['SumStats']['raw_folder'], row['condition_label'], row['filename']), axis=1)
    df['remote_raw_path'] = df.apply(lambda row: os.path.join(config['remote']['base_path'], config['SumStats']['raw_folder'], row['condition_label'], row['filename']), axis=1)
    df['munged'] = munged_default
    df['local_munged_path'] = munged_path_default
    df['remote_munged_path'] = munged_path_default
    df['wrangled'] = wrangled_default
    df['local_wrangled_path'] = wrangled_path_default
    df['remote_wrangled_path'] = wrangled_path_default

    # Handle existing IDs (assuming 'id' is the unique identifier)
    if (os.path.exists(output_file)):
        try:
            df_existing = pd.read_csv(output_file)
            existing_ids = set(df_existing['id'])
            df = df.loc[~df['id'].isin(existing_ids)]  # Filter out existing IDs
        except FileNotFoundError:
            pass  # No existing file, proceed normally

    # Append data to output file (create if it doesn't exist)
    df.to_csv(output_file, mode='a', header=not os.path.exists(output_file), index=False)


if __name__ == "__main__":
    main()





# import pandas as pd
# import os
# import yaml
# import argparse

# def main():
#     parser = argparse.ArgumentParser(description="This script takes the data from the catalog and transform it into a data description file defining all the paths and whether the data has been run through certain softwares. It also adds an N column by default in case there is not one.")
#     parser.add_argument("--env", choices=["local", "remote"], required=True,
#                         help="Specify if you are running this file in local (local) or in the MN5 (remote)")
#     args = parser.parse_args()

#     # Load data based on environment
#     if args.env == "local":
#         config_file = "/home/maria/git/SOROLLA/config/config.yaml"
#     else:
#         config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"

#     # Load configuration file securely
#     try:
#         with open(config_file) as f:
#             config = yaml.safe_load(f)
#     except FileNotFoundError:
#         print(f"Error: Configuration file not found: {config_file}")
#         exit(1)
#     except yaml.YAMLError as e:
#         print(f"Error: Invalid YAML configuration: {e}")
#         exit(1)

#     # Access values from config
#     base_path = config[args.env]["base_path"]
#     sumstats_folder = config["SumStats"]["sumstats_folder"]
#     raw_catalog = config["SumStats"]["raw_catalog"]
#     description_csv = config["SumStats"]["description_csv"]
#     raw_folder = config["SumStats"]["raw_folder"]

#     # Construct paths
#     raw_catalog_path = os.path.join(base_path, sumstats_folder, raw_catalog)
#     description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)

#     desired_columns = ["id", "condition_label", "label", "filename", 
#                    "ref_genome", "snp", "a1", "a2", "frq", "FRQ_U", "FRQ_A", 
#                    "z", "b", "OR", "se", "p", "N_col", "N_num", "Nca_col", 
#                    "Nca_val", "Nco_col", "Nco_val", "INFO", "ignore"]
    
#     # Call create_and_append_dataframe function with appropriate arguments
#     create_and_append_dataframe(raw_catalog_path, description_csv_path, desired_columns, config)


# def create_and_append_dataframe(input_file, output_file, desired_columns, config, munged_default="False", wrangled_default="False", munged_path_default="NA", wrangled_path_default="NA"):
#     """
#     Creates and appends data to a pandas DataFrame.

#     Args:
#       input_file (str): Path to the input CSV file.
#       output_file (str): Path to the output CSV file.
#       desired_columns (list): List of column names to keep from the input CSV.
#       munged_default (str, optional): Default value for the 'munged' column ("False" by default).
#       wrangled_default (str, optional): Default value for the 'wrangled' column ("False" by default).
#       munged_path_default (str, optional): Default value for the 'munged_path' column ("NA" by default).
#       wrangled_path_default (str, optional): Default value for the 'wrangled_path' column ("NA" by default).
#     """

#     # Check if input file exists
#     if not os.path.exists(input_file):
#         print(f"Error: Input file {input_file} does not exist.")
#         return

#     # Read input data using pandas
#     try:
#         df_in = pd.read_csv(input_file)
#     except FileNotFoundError:
#         print(f"Error: Input file {input_file} not found.")
#         return
#     except pd.errors.ParserError as e:
#         print(f"Error parsing input CSV: {e}")
#         return

#     # Select desired columns
#     df = df_in[desired_columns]
#     df = df.astype(str)

#     # Add new columns with defaults
#     df['local_raw_path'] = df.apply(lambda row: os.path.join(config['local']['base_path'], config['SumStats']['raw_folder'], row['condition_label'], row['filename']), axis=1)
#     df['remote_raw_path'] = df.apply(lambda row: os.path.join(config['remote']['base_path'], config['SumStats']['raw_folder'], row['condition_label'], row['filename']), axis=1)
#     df['munged'] = munged_default
#     df['local_munged_path'] = munged_path_default
#     df['remote_munged_path'] = munged_path_default
#     df['wrangled'] = wrangled_default
#     df['local_wrangled_path'] = wrangled_path_default
#     df['remote_wrangled_path'] = wrangled_path_default

#     # Handle existing IDs (assuming 'id' is the unique identifier)
#     if os.path.exists(output_file):
#         try:
#             df_existing = pd.read_csv(output_file)
#             existing_ids = set(df_existing['id'])
#             df = df.loc[~df['id'].isin(existing_ids)]  # Filter out existing IDs
#         except FileNotFoundError:
#             pass  # No existing file, proceed normally

#     # Append data to output file (create if it doesn't exist)
#     df.to_csv(output_file, mode='a', header=not os.path.exists(output_file), index=False)


# if __name__ == "__main__":
#     main()