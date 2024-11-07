import pandas as pd
import os
import subprocess

def main():
    csv_file_path = "/home/maria/git/SOROLLA/SumStats/excell_sumstats_description.csv"
    csv_excell = pd.read_csv(csv_file_path)
    download_summarystatistics(csv_excell)

def download_summarystatistics(df):
    """
    This is the function to download the Summary Statistics datasets.
    It needs a csv as input containing the columns FILENAME and SUMMARYSTATISTICS.
    row["filename"] == id + file extension
    row["summaryStatistics"] == direct link to dataset
    """

    for index, row in df.iterrows():
        print(f"Generating download command for {row['label']}")

        # Create the variable containing the final path where each row will be downloaded.
        # Change this path if not downloading in local.
        path_filename = f"/home/maria/git/SOROLLA/SumStats/RAW/{row['filename']}"

        # Check dir
        os.makedirs(os.path.dirname(path_filename), exist_ok=True)

        # Create the wget command
        sumstats = row["summaryStatistics"]
        command = ["wget", "-O", path_filename, sumstats]
        print(f"Executing command: {' '.join(command)}")

        # Execute
        subprocess.run(command)

if __name__ == "__main__":
    main()
