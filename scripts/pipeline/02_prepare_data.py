## Create rsID column from MarkerName
import pandas as pd
import gzip
import re
import os


def create_rsID(path, col):
    # Handle different file extensions and read the file
    if path.endswith(".txt") or path.endswith(".tsv"):
        df = pd.read_csv(path, sep="\t")
        output_path = path
    elif path.endswith(".tsv.gz"):
        with gzip.open(path, "rt") as f:
            df = pd.read_csv(f, sep="\t")
        output_path = path
    else:
        print("Error, unsupported file extension")
        return
    
    # Extract rsID using a capturing group
    df["rsID"] = df[col].str.extract(r'(rs\d+)')
    print(head(df))
    
    # Save the DataFrame with the same extension
    if output_path.endswith(".tsv.gz"):
        with gzip.open(output_path, "wt") as f:
            df.to_csv(f, sep="\t", index=False)
    else:
        df.to_csv(output_path, sep="\t", index=False)
    
    print(f"File saved to {output_path}")


# create_rsID("/home/maria/git/SOROLLA/SumStats/RAW/ASD/GCST010514.tsv", "MarkerName")



def check_and_convert_numeric(path, col):
    # Handle different file extensions and read the file
    if path.endswith(".txt") or path.endswith(".tsv"):
        df = pd.read_csv(path, sep="\t")
    elif path.endswith(".tsv.gz"):
        with gzip.open(path, "rt") as f:
            df = pd.read_csv(f, sep="\t")
    else:
        print("Error, unsupported file extension")
        return
    
    # Check if the specified column is numeric
    if not pd.api.types.is_numeric_dtype(df[col]):
        print(f"The column '{col}' is of type: {df[col].dtype}")
        # Coerce the column to numeric, forcing non-numeric values to NaN
        df[col] = pd.to_numeric(df[col], errors='coerce')
        print(f"Column '{col}' has been converted to numeric.")

    # Save the DataFrame with the same extension
    if path.endswith(".tsv.gz"):
        with gzip.open(path, "wt") as f:
            df.to_csv(f, sep="\t", index=False)
    else:
        df.to_csv(path, sep="\t", index=False)
    
    print(f"File saved to {path}")


#Use the function to coerce the p-value into a numeric value
# check_and_convert_numeric("/home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST005362.tsv", "p_value")
# check_and_convert_numeric("/home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST012597.tsv.gz", "p_value")


def clean_rows_with_invalid_values(path, col):
    # Handle different file extensions and read the file
    if path.endswith(".txt") or path.endswith(".tsv"):
        df = pd.read_csv(path, sep="\t")
    elif path.endswith(".tsv.gz"):
        with gzip.open(path, "rt") as f:
            df = pd.read_csv(f, sep="\t")
    else:
        print("Error, unsupported file extension")
        return
    
    # Define a function to check if a value contains more than two letters
    def has_more_than_two_letters(value):
        # Use regex to find letters in the value
        return len(re.findall(r'[a-zA-Z]', str(value))) > 2
    
    # Filter out rows where the specified column has more than two letters
    original_shape = df.shape
    df = df[~df[col].apply(has_more_than_two_letters)]
    
    # Report the number of rows removed
    rows_removed = original_shape[0] - df.shape[0]
    print(f"Removed {rows_removed} rows with invalid values.")
    print(f"Rows remaining are: {df.shape}")
    
    # Save the DataFrame with the same extension
    if path.endswith(".tsv.gz"):
        with gzip.open(path, "wt") as f:
            df.to_csv(f, sep="\t", index=False)
    else:
        df.to_csv(path, sep="\t", index=False)
    
    print(f"File saved to {path}")


# clean_rows_with_invalid_values("/home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST005362.tsv", "effect_allele")
# # # Removed 0 rows with invalid values.
# # # Rows remaining are: (7215344, 10)
# # # File saved to /home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST005362.tsv

# clean_rows_with_invalid_values("/home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST005362.tsv", "other_allele")
# # # Removed 0 rows with invalid values.
# # # Rows remaining are: (7215344, 10)
# # # File saved to /home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST005362.tsv

# clean_rows_with_invalid_values("/home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST012597.tsv.gz", "effect_allele")
# # # Removed 116646 rows with invalid values.
# # # Rows remaining are: (7451112, 10)
# # # File saved to /home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST012597.tsv.gz

# clean_rows_with_invalid_values("/home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST012597.tsv.gz", "other_allele")
# # # Removed 260981 rows with invalid values.
# # # Rows remaining are: (7190131, 10)
# # # File saved to /home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST012597.tsv.gz



def modify_to_tsv(path):
    # Read the space-separated file using regex for whitespace
    df = pd.read_csv(path, sep=r"\s+")
    
    # Create a new file name by adding a .tsv extension
    tsv_path = path + '.tsv'
    
    # Save the DataFrame as a TSV file
    df.to_csv(tsv_path, sep='\t', index=False)
    
    print(f"File saved as {tsv_path}")

    

# Get the correct name on the columns of the csv final_description (only needs to be done once)
def add_column_type(csv_file_path):
    #Read csv
    df = pd.read_csv(csv_file_path)
    #Insert empty column for the type
    df.insert(0, "type", "")
    #Iterate over the column condition_label to assign type
    # Assign type based on condition_label
    df.loc[df["condition_label"].isin(["ADHD", "ANX", "ASD", "BIP", "DEP", "SCZ", "TCA", "PTSD"]), "type"] = "PSY"
    df.loc[df["condition_label"].isin(["ALZ", "SCLE", "EPI"]), "type"] = "NEU"
    df.loc[~df["condition_label"].isin(["ADHD", "ANX", "ASD", "BIP", "DEP", "SCZ", "TCA", "PTSD", "ALZ", "SCLE", "EPI"]), "type"] = "CAN"

    df.to_csv(csv_file_path, sep=",", index=False)
    print(df.head())
    print(f"File saved as {csv_file_path}")

#add_column_type("/home/maria/git/SOROLLA/SumStats/final_sumstats_description.csv")



def drop_na_rsid_rows(path, rsid_column):
    """
    Reads a .tsv, .txt, or .tsv.gz file, removes rows with missing values in a specified column,
    and writes the cleaned data back to the original file.

    Args:
    path (str): Path to the file (.txt, .tsv, or .tsv.gz).
    rsid_column (str): The column name where NA values should be checked and rows removed.
    """
    # Determine the file extension
    if path.endswith(".txt") or path.endswith(".tsv"):
        df = pd.read_csv(path, sep="\t")  # Read the file
    elif path.endswith(".tsv.gz"):
        with gzip.open(path, "rt") as f:
            df = pd.read_csv(f, sep="\t")  # Read compressed file
    else:
        print("Error: Unsupported file extension.")
        return

    # Drop rows where the specified column has NA values
    df_cleaned = df.dropna(subset=[rsid_column])

    # Save the cleaned data back to the file
    if path.endswith(".tsv.gz"):
        with gzip.open(path, "wt") as f:
            df_cleaned.to_csv(f, sep="\t", index=False)  # Write compressed file
    else:
        df_cleaned.to_csv(path, sep="\t", index=False)  # Write regular .tsv or .txt file

    print(f"File saved to {path}. Rows with NA in '{rsid_column}' have been removed.")


#drop_na_rsid_rows("/home/maria/git/SOROLLA/SumStats/RAW/PD/GCST90104087.tsv","variant_id")



import pandas as pd
import gzip
import os

def drop_large_p_values(path, p_column):
    """
    Reads a .tsv, .txt, or .tsv.gz file, removes rows where the p-value in the specified column is greater than 1e300,
    and writes the cleaned data back to the original file.

    Args:
    path (str): Path to the file (.txt, .tsv, or .tsv.gz).
    p_column (str): The column name where p-values are stored and checked.
    """
    # Determine the file extension and read the file accordingly
    if path.endswith(".txt") or path.endswith(".tsv"):
        df = pd.read_csv(path, sep="\t", low_memory=False)
    elif path.endswith(".tsv.gz"):
        with gzip.open(path, "rt") as f:
            df = pd.read_csv(f, sep="\t", low_memory=False)
    else:
        print("Error: Unsupported file extension.")
        return

    # Convert the p-value column to numeric, invalid parsing will be set as NaN
    df[p_column] = pd.to_numeric(df[p_column], errors='coerce')

    # Remove rows where the p-value exceeds 1e300 or is NaN
    df_cleaned = df[df[p_column] < 1e300]

    # Save the cleaned data back to the file
    if path.endswith(".tsv.gz"):
        with gzip.open(path, "wt") as f:
            df_cleaned.to_csv(f, sep="\t", index=False)  # Write compressed file
    else:
        df_cleaned.to_csv(path, sep="\t", index=False)  # Write regular .tsv or .txt file

    print(f"File saved to {path}. Rows with invalid p-values or p-values greater than 1e300 in '{p_column}' have been removed.")



# drop_large_p_values("/home/maria/git/SOROLLA/SumStats/RAW/PTSD/PTSD-PGC-2024.tsv", "P")
# drop_large_p_values("/home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST012597.tsv.gz","p_value")
# drop_large_p_values("/home/maria/git/SOROLLA/SumStats/RAW/ADHD/GCST005362.tsv","p_value")



def drop_nas(path):
    # Determine the file extension
    if path.endswith(".txt") or path.endswith(".tsv"):
        df = pd.read_csv(path, sep="\t")  # Read the file
    elif path.endswith(".tsv.gz"):
        with gzip.open(path, "rt") as f:
            df = pd.read_csv(f, sep="\t")  # Read compressed file
    else:
        print("Error: Unsupported file extension.")
        return

    # Drop rows where the specified column has NA values
    df_cleaned = df.dropna(axis = 0)

    # Save the cleaned data back to the file
    if path.endswith(".tsv.gz"):
        with gzip.open(path, "wt") as f:
            df_cleaned.to_csv(f, sep="\t", index=False)  # Write compressed file
    else:
        df_cleaned.to_csv(path, sep="\t", index=False)  # Write regular .tsv or .txt file

    print(f"File saved to {path}")

# drop_nas("/home/maria/git/SOROLLA/SumStats/RAW/PD/GCST90104087.tsv")

