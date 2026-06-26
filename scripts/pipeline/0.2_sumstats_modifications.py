import pandas as pd
import csv

excell = pd.read_csv("/home/maria/git/SOROLLA/SumStats/excell_sumstats_description.csv")
description = pd.read_csv("/home/maria/git/SOROLLA/SumStats/final_sumstats_description.csv")

# excell.loc[excell.id == "GCST90012878", 'snp'] = "variant_id"
# excell.loc[excell.id == "GCST90012878", 'ignore'] = "SNP_ID"

# print(excell.loc[excell.id == "GCST90012878"])

# description.loc[description.id == "GCST90012878", 'snp'] = "variant_id"
# description.loc[description.id == "GCST90012878", 'ignore'] = "SNP_ID"

# file_to_detect_path = description.loc[description["id"] == "GCST007511", "local_raw_path"].values[0] 
# print(file_to_detect_path)

# with open(file_to_detect_path, 'r') as file_to_detect:
# 	sample = file_to_detect.read(4000)
# 	sniffer = csv.Sniffer()
# 	delimiter = sniffer.sniff(sample).delimiter

# print(f'The delimiter is: "{delimiter}"')


# df = pd.read_csv(file_to_detect_path, delimiter=' ') 
# print(df.head())


# description.loc[description.id == "PGC-ADHD-2022", 'N_col'] = " "
# excell.loc[excell.id == "PGC-ADHD-2022", 'N_col'] = " "

# description.loc[description.id == "GCST010514", 'b'] = "Effect"
# excell.loc[excell.id == "GCST010514", 'b'] = "Effect"

# description.loc[description.id == "GCST009158", 'b'] = "EFFECT"
# excell.loc[excell.id == "GCST009158", 'b'] = "EFFECT"

# excell.to_csv("/home/maria/git/SOROLLA/SumStats/excell_sumstats_description.csv", index=False)
# description.to_csv("/home/maria/git/SOROLLA/SumStats/final_sumstats_description.csv", index=False)


# datasets_to_transform = ["GCST90128471-all","GCST90128471-male","GCST90128471-females"]
# for dataset in datasets_to_transform:
#     for index, row in description.iterrows():
#         path = description.iloc(dataset, "local_raw_path")
#         with gzip.open(path, 'rt', encoding = 'utf-8') as file:
#                df = pd.read_csv(file, comment="#", delimiter="\t")
#                df.to_csv(path, sep="\t", index=False, compression="gzip")


# def create_rsID(path, col):
#     # Handle different file extensions and read the file
#     if path.endswith(".txt") or path.endswith(".tsv"):
#         df = pd.read_csv(path, sep="\t")
#         output_path = path
#     elif path.endswith(".tsv.gz"):
#         with gzip.open(path, "rt") as f:
#             df = pd.read_csv(f, sep="\t")
#         output_path = path
#     else:
#         print("Error, unsupported file extension")
#         return
    
#     # Extract rsID using a capturing group
#     df["rsID"] = df[col].str.extract(r'(rs\d+)')
#     print(head(df))
    
#     # Save the DataFrame with the same extension
#     if output_path.endswith(".tsv.gz"):
#         with gzip.open(output_path, "wt") as f:
#             df.to_csv(f, sep="\t", index=False)
#     else:
#         df.to_csv(output_path, sep="\t", index=False)
    
#     print(f"File saved to {output_path}")


# create_rsID("/home/maria/git/SOROLLA/SumStats/RAW/ASD/GCST010514.tsv", "MarkerName")

#### UPDATE THE DATA THAT WAS DOWNLOADED THE LATEST AND HAS DIFFERENT COLUMNS
# id = GCST004692, Nco_col = controls
# id = GCST90225527, N_col = None
# id = GCST90435863, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435864, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST010514, snp = rsID, frq = None, 
# id = GCST90435600, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id =GCST005902, INFO = ImputationAccuracy
# id = GCST90435859, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435657, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435926, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90044335, p = P_noSPA
# id = GCST90435919, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST004744, or = odds_ratio
# id = GCST004748, or = odds_ratio
# id = GCST004749, or = odds_ratio
# id = GCST90435631, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435857, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90436787, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435945, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435594, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435597, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435663, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435666, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90435667, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls
# id = GCST90436510, snp = variant_id, a1 = effect_allele, a2=other_allele, frq = effect_allele_frequency, se = standard_error, p = p_value, Nca_col = n_cases, Nco_col = n_controls



# updates = {
#     "GCST004692": {"Nco_col": "controls"},
#     "GCST90225527": {"N_col": "None"},
#     "GCST90435863": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435864": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST010514": {"snp": "rsID", "frq": "None"},
#     "GCST90435600": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST005902": {"INFO": "ImputationAccuracy"},
#     "GCST90435859": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435657": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435926": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90044335": {"p": "P_noSPA"},
#     "GCST90435919": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST004744": {"or": "odds_ratio"},
#     "GCST004748": {"or": "odds_ratio"},
#     "GCST004749": {"or": "odds_ratio"},
#     "GCST90435631": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435857": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90436787": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435945": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435594": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435597": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435601": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435602": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435663": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435666": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90435667": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90436510": {"snp": "variant_id", "a1": "effect_allele", "a2": "other_allele", 
#                      "frq": "effect_allele_frequency", "se": "standard_error", 
#                      "p": "p_value", "Nca_col": "n_cases", "Nco_col": "n_controls"},
#     "GCST90271611": {'standard_error':"None"},
#     "GCST90271612": {'standard_error':"None"},
#     "GCST90271613": {'standard_error':"None"},
#     "GCST90271619": {'standard_error':"None"},
# }



# # Apply updates
# for idx, row in excell.iterrows():
#     row_id = row["id"]
#     if row_id in updates:
#         for col, new_value in updates[row_id].items():
#             if col in excell.columns:
#                 excell.at[idx, col] = new_value

# Save updated CSV
# excell.to_csv("/home/maria/git/SOROLLA/SumStats/excell_sumstats_description.csv", index=False)



