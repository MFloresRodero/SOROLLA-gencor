import pandas as pd
import subprocess

# Replace this file with your own path
csv_file = "/home/maria/git/SOROLLA/scripts/CONTROLS/test_ldsc_paired_datasets.csv"

# Replace this file with your own path
def generate_munge_command(row):
    command = ["singularity", "exec", "/home/maria/singularity/munge_stats/ldsc", 
               "python2", "/home/maria/git/SOROLLA/scripts/ldsc/munge_sumstats.py"]

    command.extend(["--sumstats", row["raw_path"]])

    if not pd.isna(row["snp"]):
        command.extend(["--snp", row["snp"]])

    if not pd.isna(row["a1"]):
        command.extend(["--a1", row["a1"]])

    if not pd.isna(row["a2"]):
        command.extend(["--a2", row["a2"]])

    if not pd.isna(row["frq"]):
        command.extend(["--frq", row["frq"]])

    if not pd.isna(row["p"]):
        command.extend(["--p", row["p"]])

    command.extend(["--N", str(row["N_num"])])

    if not pd.isna(row["N_col"]):
        command.extend(["--N-col", row["N_col"]])

    if not pd.isna(row["Nca_val"]) and not pd.isna(row["Nca_col"]):
        command.extend(["--N-cas", str(row["Nca_val"]), "--N-cas-col", row["Nca_col"]])

    if not pd.isna(row["Nco_val"]) and not pd.isna(row["Nco_col"]):
        command.extend(["--N-con", str(row["Nco_val"]), "--N-con-col", row["Nco_col"]])

    if not pd.isna(row["b"]):
        command.extend(["--signed-sumstats", f"{str(row['b'])},0"])
    elif not pd.isna(row["z"]):
        command.extend(["--signed-sumstats", f"{str(row['z'])},0"])
    elif not pd.isna(row["OR"]):
        command.extend(["--signed-sumstats", f"{str(row['OR'])},1"])

# Replace this file with your own path
    command.extend(["--out", f"/home/maria/git/SOROLLA/SumStats/Munged/CONTROLS/{row['condition']}_{row['dataset']}"])

    command.extend(["--chunksize", "500000"])
# Replace this file with your own path
    command.extend(["--merge-alleles", "/home/maria/git/SOROLLA/Ref_Genomes/HapMap3/w_hm3.snplist"])

    # Additional ignore flags based on column presence
    if not pd.isna(row["p"]):
        command.append("--ignore")
        command.append("z")
    if not pd.isna(row["ignore"]):
        # Split the ignore column value by comma and append each part separately
        ignore_values = row["ignore"].split(',')
        for ignore_value in ignore_values:
            command.append("--ignore")
            command.append(ignore_value.strip())  # Remove leading/trailing spaces

    return command

def run_munge_sumstats(csv_file):
    data = pd.read_csv(csv_file)

    for index, row in data.iterrows():
        # Skip rows where 'munged' is already True
        if str(row["munged"]) != "True":
        #if row["munged"] == "False" or row["munged"] == "Error":

            command = generate_munge_command(row)
            print(command)
            try:
                subprocess.run(command, check=True)
                # Mark the row as successfully munged
                data.at[index, "munged"] = "True"
                
                # Update the 'munged_path' column
                # Replace this file with your own path
                munged_path = f"/home/maria/git/SOROLLA/SumStats/Munged/CONTROLS/{row['condition']}_{row['dataset']}.sumstats.gz"
                data.at[index, "munged_path"] = munged_path
            except subprocess.CalledProcessError as e:
                data.at[index, "munged"] = "Error"

        else:
            print(f"{row['condition']}_{row['dataset']} skipped, already munged")

    # Save the modified dataframe back to the CSV file
    data.to_csv(csv_file, index=False)

if __name__ == "__main__":
    run_munge_sumstats(csv_file)




#### ADD RE-RUN IF ERROR TO RUN WITH THE --IGNORE, NORMALLY THE ERROR WILL BE IF THERE IS Z IS PRESENT WHEN ALSO B,SE AND OR IS PRESENT, MEANING WHEN THEY ARE NOT NAS, SO PLEASE ADD A PART WHERE IF Z IS PRESENT ALONG WITH THE REST, THE --IGNORE IS ADDED.