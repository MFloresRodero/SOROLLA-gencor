import pandas as pd
import yaml
import argparse


def main():
	parser = argparse.ArgumentParser(description= 
								  "This script takes the results from ldsc correlations and create the paired_datasets.csv for supergnova and MR.")
	
	parser.add_argument("--env", choices=["local", "remote"], required = True)
	parser.add_argument("--type", choices=["MR", "supergnova"],
					 help="This argument refers to whether I want to create the file for MR or supergnova")
	args = parser.parse_args()

	if args.env == "local":
		config_file = "/home/maria/git/SOROLLA/config/config.yaml"
	elif args.env == "remote":
		config_file = "/gpfs/projects/bsc02/mflores/gencor/config/config.yaml"
	else:
		raise ValueError("Environment not found, check config file.")
	
	try:
		with open(config_file) as f:
			config = yaml.safe_load(f)
	except FileNotFoundError:
		print(f"Error: Configuration file not found: {config_file}")
		exit(1)
	except yaml.YAMLError as e:
		print(f"Error: Invalid YAML configuration: {e}")
		exit(1)

	
	# Configuration
	base_path = config[args.env]["base_path"]
	sumstats_folder = config["SumStats"]["sumstats_folder"]
	final_description = config["SumStats"]["description_csv"]
	results_folder = config["Results"]["results_folder"]
	ldsc_results = config["Results"]["ldsc_results_corrected_csv"]
	
	if args.type == "MR":
		output_folder = config["SumStats"]["MR_folder"]
	elif args.type == "supergnova":
		output_folder = config["SumStats"]["supergnova_folder"]
	
	
	ldsc_results_path = f"{base_path}{results_folder}{ldsc_results}"
	final_description_path = f"{base_path}{sumstats_folder}{final_description}"

	cancer_csv = config["SumStats"]["cancer_paired"]
	psy_csv = config["SumStats"]["psychiatric_paired"]
	neuro_csv = config["SumStats"]["neuro_paired"]
	cancer_psy_csv = config["SumStats"]["cancer_psy_paired"]
	psy_neuro_csv = config["SumStats"]["psychiatric_neuro_paired"]
	cancer_neuro_csv = config["SumStats"]["cancer_neuro_paired"]

	cancer_csv_path = f"{base_path}{sumstats_folder}{output_folder}{cancer_csv}"
	psy_csv_path = f"{base_path}{sumstats_folder}{output_folder}{psy_csv}"
	neuro_csv_path = f"{base_path}{sumstats_folder}{output_folder}{neuro_csv}"
	cancer_psy_csv_path = f"{base_path}{sumstats_folder}{output_folder}{cancer_psy_csv}"
	psy_neuro_csv_path = f"{base_path}{sumstats_folder}{output_folder}{psy_neuro_csv}"
	cancer_neuro_csv_path = f"{base_path}{sumstats_folder}{output_folder}{cancer_neuro_csv}"


	## Extract relevant result 
	df_results_ldsc = pd.read_csv(ldsc_results_path)
	df_results_ldsc = df_results_ldsc[df_results_ldsc["p_FDR_rejected"]==True]
	df_results_ldsc = df_results_ldsc[[
		'id_1', 
		'label_1', 
		'id_2', 
		'label_2', 
		'type_1', 
		'disease_1', 
		'type_2',
		'disease_2'
	]]
	print(df_results_ldsc.columns)


	## Paired datasets, extract paths
	description = pd.read_csv(final_description_path)
	
	if args.type == "MR":
		wanted_columns = [
			"id",
			"local_preprocessed_path",
			"remote_preprocessed_path"
			]
		# rename_columns_1 = {"local_preprocessed_path":"local_preprocessed_path_1"}
		# rename_columns_2 = {"remote_preprocessed_path":"remote_preprocessed_path_2"}

	elif args.type == "supergnova":
		wanted_columns = [
			"id",
			"N_num",
			"local_munged_path",
			"remote_munged_path"
			]
		# rename_columns_1 = {"local_munged_path":"local_munged_path_1", "N_num":"N_num_1"}
		# rename_columns_2 = {"remote_munged_path":"remote_munged_path_2", "N_num":"N_num2"}

	else:
		raise ValueError("There was an issue getting the wanted columns for the description files")
	
	# Get the wanted columns depending on the type argument
	description = description[wanted_columns]


	# # # Create the subsets to save in different files.
	# # df_results_ldsc_diff = df_results_ldsc[df_results_ldsc["type_1"] == df_results_ldsc["type_2"]]
	# # df_results_ldsc_diff = df_results_ldsc_diff[["id_1", "type_1", "label_1", "disease_1", "id_2", "type_2", "label_2", "disease_2"]]
	# # df_results_ldsc_same = df_results_ldsc[df_results_ldsc["type_1"] != df_results_ldsc["type_2"]]
	# # df_results_ldsc_same = df_results_ldsc_same[["id_1", "type_1", "label_1", "disease_1", "id_2", "type_2", "label_2", "disease_2"]]

	# Merge with the original description file
	df_results_ldsc = df_results_ldsc.merge(description, left_on="id_1", right_on="id", how="left", suffixes=("", "_1")).drop(columns="id")
	df_results_ldsc = df_results_ldsc.merge(description, left_on="id_2", right_on="id", how="left", suffixes=("_1", "_2")).drop(columns="id")
	
	# # df_results_ldsc_same = df_results_ldsc_same.merge(description, left_on="id_1", right_on="id", how="left", suffixes=("", "_1")).drop(columns="id")
	# # df_results_ldsc_same = df_results_ldsc_same.merge(description, left_on="id_2", right_on="id", how="left", suffixes=("_1", "_2")).drop(columns="id")
	
	# Create column and save
	if args.type == "MR":
		df_results_ldsc["MR"] = "False"

	elif args.type =="supergnova":
		df_results_ldsc["supergnova"] = "False"


	# Same type
	df_cancer = df_results_ldsc[(df_results_ldsc["type_1"] == "CAN") & (df_results_ldsc["type_2"] == "CAN")]
	df_cancer.to_csv(cancer_csv_path, index=False)
	df_psychiatric = df_results_ldsc[(df_results_ldsc["type_1"] == "PSY") & (df_results_ldsc["type_2"] == "PSY")]
	df_psychiatric.to_csv(psy_csv_path, index=False)
	df_neurobiological = df_results_ldsc[(df_results_ldsc["type_1"] == "NEU") & (df_results_ldsc["type_2"] == "NEU")]
	df_neurobiological.to_csv(neuro_csv_path, index=False)

	# Different type
	df_can_psy = df_results_ldsc[((df_results_ldsc["type_1"] == "CAN") & (df_results_ldsc["type_2"] == "PSY") | (df_results_ldsc["type_1"] == "PSY") & (df_results_ldsc["type_2"] == "CAN"))]
	df_can_psy.to_csv(cancer_psy_csv_path, index=False)
	df_can_neu = df_results_ldsc[((df_results_ldsc["type_1"] == "CAN") & (df_results_ldsc["type_2"] == "NEU") | (df_results_ldsc["type_1"] == "NEU") & (df_results_ldsc["type_2"] == "CAN"))]
	df_can_neu.to_csv(cancer_neuro_csv_path, index=False)
	df_psy_neu = df_results_ldsc[((df_results_ldsc["type_1"] == "PSY") & (df_results_ldsc["type_2"] == "NEU") | (df_results_ldsc["type_1"] == "NEU") & (df_results_ldsc["type_2"] == "PSY"))]
	df_psy_neu.to_csv(psy_neuro_csv_path, index=False)


	# # df_can_psy_1 = df_results_ldsc[(df_results_ldsc["type_1"] == "CAN" & df_results_ldsc["type_2"] == "PSY")]
	# # df_can_psy_2 = df_results_ldsc[(df_results_ldsc["type_1"] == "PSY" & df_results_ldsc["type_2"] == "CAN")]
	# # df_can_psy = pd.concat(df_can_psy_1, df_can_psy_2)
	# # df_can_psy.to_csv(cancer_psy_csv_path, index=False)

	# # df_can_neu_1 = df_results_ldsc[(df_results_ldsc["type_1"] == "CAN" & df_results_ldsc["type_2"] == "NEU")]
	# # df_can_neu_2 = df_results_ldsc[(df_results_ldsc["type_1"] == "NEU" & df_results_ldsc["type_2"] == "CAN")]
	# # df_can_neu = pd.concat(df_can_neu_1, df_can_neu_2)
	# # df_can_neu.to_csv(cancer_neuro_csv_path, index=False)

	# # df_psy_neu_1 = df_results_ldsc[(df_results_ldsc["type_1"] == "PSY" & df_results_ldsc["type_2"] == "NEU")]
	# # df_psy_neu_2 = df_results_ldsc[(df_results_ldsc["type_1"] == "NEU" & df_results_ldsc["type_2"] == "PSY")]
	# # df_can_neu = pd.concat(df_psy_neu_1, df_psy_neu_2)
	# # df_can_neu.to_csv(psy_neuro_csv_path, index=False)

if __name__ == "__main__":
    main()