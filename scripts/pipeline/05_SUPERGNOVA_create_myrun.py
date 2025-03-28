import pandas as pd
import yaml
import argparse


def main():
	parser = argparse.ArgumentParser(description= 
								  "This script takes the results from ldsc correlations and create the paired_datasets.csv for supergnova and MR.")
	
	parser.add_argument("--env", choices=["local", "remote"], required = True)
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
	supergnova_file = config["SumStats"]["supergnova_paired"]
	input_csv = f"{base_path}{sumstats_folder}{supergnova_file}"
	print("This is the input path:", input_csv)
	script = config["Scripts"]["pipeline"]["supergnova_genetic_correlation_batches"]
	script_path = f"{base_path}{script}"
	print("This is the SCRIPT path:", script_path)

	jobs_folder = config["Scripts"]["JOBS_MN"]["jobs_mn"]
	print("This is the output path:", jobs_folder)

	csv = pd.read_csv(input_csv)
	number_of_batches = list(csv["batch"].unique())
	maximum_number_of_batches = (csv["batch"].nunique())+1
	my_run_output = f"{base_path}{jobs_folder}supergnova_my_run.txt"

	with open(my_run_output, "w") as output_file:
		for batch in number_of_batches:
			if batch != maximum_number_of_batches:
				command = (
					f"python3 {script_path} --env {args.env} --batch {batch}\n"
					)
				output_file.write(command)
			elif batch == maximum_number_of_batches:
				print(f"Reached the end of the csv at batch number {maximum_number_of_batches}")

if __name__ == "__main__":
    main()