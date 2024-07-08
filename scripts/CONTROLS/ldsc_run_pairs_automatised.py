import pandas as pd
import subprocess

csv_file = "/home/maria/git/SOROLLA/scripts/CONTROLS/test_ldsc_paired_datasets.csv"

def run_ldsc(row):
    try:
        condition_1 = row["condition_1"]
        munged_file_path_1 = row["munged_file_path_1"]
        condition_2 = row["condition_2"]
        munged_file_path_2 = row["munged_file_path_2"]
        ldsc = row["ldsc"]
    except ValueError as e:
        print(f"Error unpacking row: {row}")
        return 'Error'

    out_file = f"/home/maria/git/SOROLLA/Results/CONTROLS/{row['condition_1']}_{row['dataset_name_1']}_{row['condition_2']}_{row['dataset_name_2']}"
    
    if pd.isna(munged_file_path_1) or pd.isna(munged_file_path_2):
        print(f"One of the munged file paths is empty, skipping LDSC for row: {row}")
        return 'Error'
    
    if ldsc != 'True':
        try:
            subprocess.run([
                'singularity', 'exec', '/home/maria/singularity/munge_stats/ldsc', 'python2',
                '/home/maria/git/SOROLLA/scripts/ldsc/ldsc.py',
                '--rg', f"{munged_file_path_1},{munged_file_path_2}",
                '--ref-ld-chr', '/home/maria/git/SOROLLA/Ref_Genomes/1000G_Phase3_LD_scores/LDscore/LDscore.@',
                '--w-ld-chr', '/home/maria/git/SOROLLA/Ref_Genomes/1000G_Phase3_LD_scores/LDscore/LDscore.@',
                '--out', out_file
            ], check=True)
            return 'True'
        except subprocess.CalledProcessError:
            print(f"Error running LDSC for row: {row}")
            return 'Error'
    else:
        return ldsc

def update_csv(csv_file):
    data = pd.read_csv(csv_file)

    for index, row in data.iterrows():
        ldsc_result = run_ldsc(row)
        data.at[index, "ldsc"] = ldsc_result  # Update LDSC column dynamically
    
    # Write back to the CSV file
    data.to_csv(csv_file, index=False)

if __name__ == "__main__":
    update_csv(csv_file)

