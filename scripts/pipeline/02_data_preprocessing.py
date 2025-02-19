## Script to transform RAW data into pre-processed data.
### The data is in different formats. The aim is to keep only the columns that will be needed for processing the data with the genetic correlation softwares.
### All datasets should contain the same number of columns, so a matrix is created to track these changes. 

import pandas as pd
import os
import yaml
import argparse
import gzip
import csv
import re
import numpy as np
import scipy.stats as stats


def main():
    parser = argparse.ArgumentParser(description=
                                     "This script is meant to take the RAW data, and pre-process it. We want all the datasets to contain the same number of columns")
    parser.add_argument("--env", choices=["local", "remote", "shared"], required=True,
                        help="Specify if you are running this file in local (local) or in the MN5 (remote)")
    args = parser.parse_args()

    # Load data based on environment
    if args.env == "local":
        config_file = "/home/maria/git/SOROLLA/config/config.yaml"
    elif args.env == "remote":
        config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
    elif args.env == "shared":
        config_file = "/gpfs/projects/hpcsharing/364592/config/config.yaml"
    else:
        raise ValueError("Environment not found, check if you specified the environment with --env or if the path is wrong")

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

	# Configuration files from config/config.yaml
    base_path = config[args.env]["base_path"]
    # print(base_path)
    sumstats_folder = config["SumStats"]["sumstats_folder"]
    # print(sumstats_folder)
    description_csv = config["SumStats"]["description_csv"]
    # print(description_csv)
    matrix_description = config["SumStats"]["matrix_description"]
    # print(matrix_description)
    preprocessed_folder = config["SumStats"]["preprocessed_folder"]
    print(preprocessed_folder)
    preprocessed_checkpoint = config["SumStats"]["preprocessed_saving_process"]

    # Construct paths
    description_csv_path = os.path.join(base_path, sumstats_folder, description_csv)
    print(description_csv_path)
    matrix_description_path = os.path.join(base_path, sumstats_folder, matrix_description)
    print(matrix_description_path)
    preprocessed_folder_path = os.path.join(base_path, preprocessed_folder)
    print(preprocessed_folder_path)
    preprocessed_folder_files_saving_path = os.path.join(base_path, preprocessed_folder, preprocessed_checkpoint)
    print(preprocessed_folder_files_saving_path)


	# Display options:
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)

	# Call function that iterates through the rows.
    create_matrix_description(description_csv_path, matrix_description_path)
    reference = pd.read_csv(description_csv_path, sep=",")
    print(reference.columns)
    reference.apply(lambda row: transform_dataset(row, args.env, preprocessed_folder_path, matrix_description_path, preprocessed_folder_files_saving_path), axis=1)


def create_matrix_description(description_csv_path, matrix_description_path): 
	""" A description matrix will be generated in order to track whether the changes are needed or are made. 
	0 = Column does not exist, create column and if it's not needed i.e. z-score, fill with NAs.
	1 = Column exists and can be used for calculations and modifications.
	2 = Will be the number used to identify added columns in later functions."""

	# Load dataframe
	reference_file = pd.read_csv(description_csv_path, sep = ",")

	# Define columns needed for the matrix
	wanted_for_matrix = ["id", "label", "disease","snp", "a1", "a2", "frq","z", "b", 
					  "OR", "se_beta", "se_OR", "p", "N_col", "Nca_col", "Nco_col", "INFO"]

	# Create the matrix
	matrix = reference_file[wanted_for_matrix].copy()
	matrix = matrix.notna().astype(int)
	matrix[['id', 'label', 'disease']] = reference_file[['id', 'label', 'disease']]

	matrix = matrix.rename(columns={"snp": "rsID",
                        "a1": "A1", 
                        "a2": "A2",
						"frq": "A1_frequency",
                        "z":"zscore",
                        "b": "beta",
                        "OR": "odds_ratio",
                		"se_beta": "beta_standard_error",
						"se_OR": "odds_ratio_standard_error",
						"p":"p_value",
						"N_col": "Ncol",
						"Nca_col": "Nca_col",
						"Nco_col": "Nco_col",
						"INFO": "INFO"})

	# Iterate every row in the matrix, so if it's NA it'll be 0 and if not it'll be 1
	if (os.path.exists(matrix_description_path)):
		try:
			matrix_already_created = pd.read_csv(matrix_description_path)
			existing_ids = set(matrix_already_created['id'])
			matrix = matrix.loc[~matrix['id'].isin(existing_ids)]
		except FileNotFoundError:
			pass

	# Save the matrix back
	matrix.to_csv(matrix_description_path, mode='a', header=not os.path.exists(matrix_description_path), index=False)
	print(f"Matrix saved to {matrix_description_path}")



def detect_delimiter(filepath, compression):
    """
    Detects the delimiter in a file, handling gzip compression if necessary.
    """
    open_func = gzip.open if compression == 'gzip' else open
    with open_func(filepath, 'rt', encoding='utf-8', errors='replace') as file_to_detect:
        sample = file_to_detect.read(4000)
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter
    return delimiter



def update_matrix_Ncol(sample_id, matrix_description_path, column_name):
    """
    Update the matrix description file by setting the Ncol field to 2 for the given sample ID.
    """
    try:
        matrix = pd.read_csv(matrix_description_path)

        # Locate the row with the given ID and update the value
        matrix.loc[matrix['id'] == sample_id, column_name] = 2

        # Save the updated matrix back
        matrix.to_csv(matrix_description_path, index=False)
        print(f"Matrix description updated for ID {sample_id}: {column_name} set to 2.")
    except Exception as e:
        print(f"Error updating matrix description: {e}")




def transform_dataset(row, env, preprocessed_folder_path, matrix_description_path, preprocessed_folder_files_saving_path):
    # Open log
	log_checkpoint = []
	
	# Variables
	tsv_new_name = f"{row['label']}_{row['id']}.tsv"
	tsv_new_path = os.path.join(preprocessed_folder_path, tsv_new_name)

	# Check if dataset already exists to avoid overwriting and wasting time.
	if os.path.exists(tsv_new_path):
		log_checkpoint.append(f"Dataset {tsv_new_name} already exists. Skipping processing for this dataset.")
		print(f"Dataset {tsv_new_name} already exists. Skipping processing for this dataset.")
		return

	# Load 
	try: 
		filepath = row[f"{env}_raw_path"] 
		log_checkpoint.append(f"filepath : {filepath}")
		print(f"filepath : {filepath}")
	except KeyError as e: 
		log_checkpoint.append(f"KeyError: {e}. The column '{env}_raw_path' is not found in the row.")
		print(f"KeyError: {e}. The column '{env}_raw_path' is not found in the row.") 
		return
	
	comp = 'gzip' if filepath.endswith('.gz') else None
	

	# Check the delimiter to avoid errors instead of assuming it's tsv.
	## Function added above to avoid UnicodeDecodeError utf-8
	try:
		delimiter = detect_delimiter(filepath, comp)
		log_checkpoint.append(f'The delimiter is: "{delimiter}"')
		print(f'The delimiter is: "{delimiter}"')
	except Exception as e:
		log_checkpoint.append(f'Error detecting delimiter for file:"{filepath}: {e})"')
		print(f'Error detecting delimiter for file:"{filepath}: {e})"')
		return
	

	# Open dataset
	try:
		df = pd.read_csv(filepath, compression=comp, sep=delimiter)
	except Exception as e:
		log_checkpoint.append(f"Error reading file '{env}_raw_path': {e}")
		print(f"Error reading file '{env}_raw_path': {e}")

	print(df.head())

	# Determine the columns of the names
	variables_columns_matrix = {
		"rsID": row["snp"] if pd.notna(row["snp"]) else None,
		"A1": row["a1"] if pd.notna(row["a1"]) else None,
		"A2": row["a2"] if pd.notna(row["a2"]) else None,
		"frq": row["frq"] if pd.notna(row["frq"]) else None,
		"zscore": row["z"] if pd.notna(row["z"]) else None,
		"beta": row["b"] if pd.notna(row["b"]) else None,
		"odds_ratio": row["OR"] if pd.notna(row["OR"]) else None,
		"beta_standard_error": row["se_beta"] if pd.notna(row["se_beta"]) else None,
		"odds_ratio_standard_error": row["se_OR"] if pd.notna(row["se_OR"]) else None,
		"p_value": row["p"] if pd.notna(row["p"]) else None,
		"Ncol": row["N_col"] if pd.notna(row["N_col"]) else None,
		"Nca_col": row["Nca_col"] if pd.notna(row["Nca_col"]) else None,
		"Nco_col": row["Nco_col"] if pd.notna(row["Nco_col"]) else None,
		"INFO": row["INFO"] if pd.notna(row["INFO"]) else None
		}
	


	# Loop to create an empty column if the columns does not exist
	for colname, original_name in variables_columns_matrix.items():
		if original_name in df.columns:
			df.rename(columns={original_name: colname}, inplace=True)
		elif original_name is None:
			log_checkpoint.append(f"Column '{colname}' has no mapping in the description.")
			print(f"Column '{colname}' has no mapping in the description. ")
			df[colname] = "NotAvailable"
			log_checkpoint.append(f"Column '{colname}' being created as placeholder.")
			print(f"Column '{colname}' being created as placeholder. ")
	
	log_checkpoint.append(df.head())
	print(df.head())
	log_checkpoint.append(df.dtypes)
	print(df.dtypes)


	# Avoid duplicates
	df = df.loc[:, ~df.columns.duplicated()]

	log_checkpoint.append(df.head())
	print(df.head())
	log_checkpoint.append(df.dtypes)
	print(df.dtypes)

	# Filter out rows where the SNP is missing.
	len_before_snp_removal = len(df)
	log_checkpoint.append(f"The initial length of the df before removing rows with missing rsID: {len_before_snp_removal}")
	print(f"The initial length of the df before removing rows with missing rsID:{len_before_snp_removal}")
	df = df.dropna(subset="rsID")
	len_after_snp_removal = len(df)
	log_checkpoint.append(f"The final length of the df after removing rows with missing rsID: {len_after_snp_removal}. The number of removed rows is {len_before_snp_removal - len_after_snp_removal}")
	print(f"The final length of the df after removing rows with missing rsID:{len_after_snp_removal}. The number of removed rows is {len_before_snp_removal - len_after_snp_removal}")
	


	# Filter out rows where the A1 or A2 have more than 2 letters.
	df['A1'] = df['A1'].astype(object)
	df['A2'] = df['A2'].astype(object)
	alleles = ["A1", "A2"]
	for a in alleles:
		remove_from_alleles = df[a].apply(lambda x: len(re.findall(r'[a-zA-Z]', str(x))) > 2)
		# We want to know how many alleles are removed.
		log_checkpoint.append(f"The initial length of the df before removing rows with more than two letters in the alleles columns is: {len_after_snp_removal}")
		print(f"The initial length of the df before removing rows with more than two letters in the alleles columns is:{len_after_snp_removal}")
		df = df[~remove_from_alleles]
		len_after_allele_removal = len(df)
		log_checkpoint.append(f"The final length of the df after removing rows with more than two letters in the alleles columns is: {len_after_allele_removal}. The number of removed rows is {len_after_snp_removal - len_after_allele_removal}")
		print(f"The final length of the df after removing rows with more than two letters in the alleles columns is: {len_after_allele_removal}. The number of removed rows is {len_after_snp_removal - len_after_allele_removal}")



	# Add the Ncol from the N_num value.
	if pd.isna(row["N_col"]):
		log_checkpoint.append("Ncol is missing. Creating Ncol with N_num values")
		print("Ncol is missing. Creating Ncol with N_num values")
		total_sample_size = row["N_num"]
		df["Ncol"] = total_sample_size
		# row["N_col"] = "N_added"
		# print(row["N_col"])
		update_matrix_Ncol(row["id"], matrix_description_path, "Ncol")
	else:
		log_checkpoint.append(f"{row['id']} already contains an N column.")
		print(f"{row['id']} already contains an N column.")

	log_checkpoint.append(df.head())
	print(df.head())



	## Calculate beta and standard error.
	if pd.isna(row["b"]) and pd.notna(row["OR"]):
		log_checkpoint.append(f"Column '{row['b']}' (mapped to beta) found in dataset. Skipping unnecessary calculations. Calculating beta (log(OR))")
		print(f"Column '{row['b']}' (mapped to beta) found in dataset. Skipping unnecessary calculations.")
		print("Calculating beta (log(OR))")
		df = df.dropna(subset=["odds_ratio"])
		df["odds_ratio"] = pd.to_numeric(df["odds_ratio"], errors="coerce")
		
		#Calculate beta
		df["beta"] = np.log(df["odds_ratio"])
		df["beta"] = pd.to_numeric(df["beta"], errors="coerce")
		update_matrix_Ncol(row["id"], matrix_description_path, "beta")
	
		
	elif pd.isna(row["OR"]) and pd.isna(row["b"]):
		log_checkpoint.append(f"Error: B missing and column '{row['OR']}' (mapped to OR) not found in dataset {row['id']}. Skipping this dataset, b could not be imputed.")
		print(f"Error: B missing and column '{row['OR']}' (mapped to OR) not found in dataset {row['id']}. Skipping this dataset, b could not be imputed.")
	
	else:
		log_checkpoint.append(f"{row['id']} already contains a beta column.")
		print(f"{row['id']} already contains a beta column.")

	print(df.head())

	# Calculate zscore with beta column
	if pd.isna(row["z"]) and not (df["beta"].astype(str) == "NotAvailable").all():
		try:
			df["beta"] = pd.to_numeric(df["beta"], errors="coerce")
			df["p_value"] = pd.to_numeric(df["p_value"], errors="coerce")
			df["zscore"] = np.sign(df['beta']) * stats.norm.ppf(1 - df['p_value'] / 2)
			update_matrix_Ncol(row["id"], matrix_description_path, "zscore")
			log_checkpoint.append("Zscore column was created from beta")
			print("Zscore column was created from beta")
		except KeyError:
				log_checkpoint.append("Something went wrong")
				print("Something went wrong")
		
	elif pd.isna(row["b"]) and pd.isna(row["OR"]):
		log_checkpoint.append("Can't calculate zscore, beta and OR missing")
		print("Can't calculate zscore, beta and OR missing")


	# If beta did not exist, calculate the new standard error. Otherwise, pass.
	if (df["beta_standard_error"].astype(str) == "NotAvailable").all() or pd.isna(row["se_beta"]):
		print("Starting beta_standard_error calculation...")
		if pd.notna(row["OR"]) and pd.notna(row["se_OR"]) and df["odds_ratio_standard_error"].notna().any():
			try:
				log_checkpoint.append("Calculating standard error (beta_standard_error) from odds_ratio and the odds_ratio_standard_error...")
				print("Calculating standard error (beta_standard_error) from odds_ratio and the odds_ratio_standard_error...")
				df = df.dropna(subset=["odds_ratio", "odds_ratio_standard_error"])

				upperboundOR = df["odds_ratio"] + 1.96 * df["odds_ratio_standard_error"]
				lowerboundOR = df["odds_ratio"] - 1.96 * df["odds_ratio_standard_error"]
				upperboundbeta = np.log(upperboundOR)
				lowerboundbeta = np.log(lowerboundOR)
				df["beta_standard_error"] = (upperboundbeta - lowerboundbeta) / (2 * 1.96)
				df["beta_standard_error"] = pd.to_numeric(df["beta_standard_error"], errors="coerce")
				update_matrix_Ncol(row["id"], matrix_description_path, "beta_standard_error")
				log_checkpoint.append("Calculated se_beta with se_OR")
				print("Calculated se_beta with se_OR.")
			
			except KeyError:
				log_checkpoint.append("se_OR column not available. Skipping beta_standard_error calculation with se_OR.")
				print("se_OR column not available. Skipping beta_standard_error calculation with se_OR.")
	
		elif not (df["zscore"].astype(str) == "NotAvailable").all() and not pd.isna(row["p"]):
			try:
				df["zscore"] = pd.to_numeric(df["zscore"], errors="coerce")
				df['beta_standard_error'] = df['beta'] / df['zscore']
				update_matrix_Ncol(row["id"], matrix_description_path, "beta_standard_error")
				log_checkpoint.append("Calculated se_beta with zscore")
				print("Calculated se_beta with zscore.")
			except KeyError:
				log_checkpoint.append("Error calculating the se_beta with zscore")
				print("Error calculating the se_beta with zscore")
		else:
			log_checkpoint.append("No method could calculate the se_beta")
			print("No method could calculate the se_beta")



	# Loop to transform the columns into numeric dtype
	numeric_columns = ["frq","zscore", "beta", "odds_ratio", "beta_standard_error", "odds_ratio_standard_error", "p_value", "Ncol", "Nca_col", "Nco_col", "INFO"]
	numeric_columns_list = []
	for col in numeric_columns:
		if "NotAvailable" not in df[col].values:
			numeric_columns_list.append(col)
		else:
			continue
	print(numeric_columns_list)


	for colname in numeric_columns_list:
		try:
			if colname in df.columns:
				if not pd.api.types.is_numeric_dtype(df[colname]):
					try:
						df[colname] = pd.to_numeric(df[colname], errors="coerce")
						print(f"{df[colname]} is numeric. Transformed to numeric dtype")
					except ValueError:
						log_checkpoint.append(f"COLUMN '{colname}' COULD NOT BE TRANSFORMED TO NUMERIC")
						print(f"COLUMN '{colname}' COULD NOT BE TRANSFORMED TO NUMERIC")
				else:
					print(f"{colname} is already numeric. Skipping conversion.")
			else:
				log_checkpoint.append(f"Numeric column '{colname}' does not exist in the dataset. Skipping conversion.")
				print(f"Numeric column '{colname}' does not exist in the dataset. Skipping conversion.")
		
		except TypeError as e:
			log_checkpoint.append(f"There was a TypeError while processing '{colname}': {e}")
			print(f"There was a TypeError while processing '{colname}': {e}")
	
	log_checkpoint.append(df.dtypes)
	print(df.dtypes)

	# Create a list of columns you want to keep if they exist in the DataFrame
	desired_columns = [col for col in variables_columns_matrix.keys() if variables_columns_matrix[col] is not None]
	
	# Keep only the columns that exist in the DataFrame
	# existing_columns = [col for col in desired_columns if col in df.columns]

	# log_checkpoint.append(f"The dataframe only contains the following columns:{existing_columns}")

	# Filter the DataFrame to keep only the desired existing columns
	# df = df[existing_columns]

		# # Remove if they are empty
	desired_columns = list(variables_columns_matrix.keys())
	df = df[desired_columns]
	columns_notavailable = df.columns[df.isin(['NotAvailable']).any()]
	columns_empty = df.columns[df.isna().all()]
	columns_to_remove = list(columns_notavailable) + list(columns_empty)
	columns_to_keep = [col for col in df.columns if col not in columns_to_remove]
	df = df[columns_to_keep]
	
	log_checkpoint.append(df.head())
	print(df.head())

	log_checkpoint.append(df.head())
	print(df.head())

	# # # # # # # # open a text file to save the results.
	# # # # # # # checkpoint_name_path = f"{preprocessed_folder_files_saving_path}{row['label']}_{row['id']}_checkpoint.txt"
	# # # # # # # saving_processes = open(checkpoint_name_path, 'w')
	checkpoint_name_path = f"{preprocessed_folder_files_saving_path}{row['label']}_{row['id']}_checkpoint.txt"
	with open(checkpoint_name_path, "w") as file:
		for item in log_checkpoint:
			file.write("%s\n" % str(item))


    # Save the dataset back as tsv
	df.to_csv(tsv_new_path, sep='\t', index=False)
	log_checkpoint.append(f"{tsv_new_name} have been converted and saved as TSV.")
	print(f"{tsv_new_name} have been converted and saved as TSV.")


if __name__ == "__main__":
    main()