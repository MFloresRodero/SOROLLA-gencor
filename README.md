# Finding out genetic correlations between psychiatric disorders and cancer.
This repository is part of a PhD project meant to analyse inverse comorbidities between disorders of the CNS and the incidence of cancer.

## Objectives
Using summary statistics from the [GWAS catalog](https://www.ebi.ac.uk/gwas), and the [Psychiatric Genomics Consortium ](https://pgc.unc.edu/) we aim to develop an automatised pipeline that wil take a csv file as initial input and use the [ldsc](https://github.com/bulik/ldsc) and [HDL](https://github.com/zhenin/HDL) softwares to calculate the correlation between diferent conditions.

## Folders and files

* **config** > contains the yaml file and the ldsc.def file to create the singularity environment used to run munge_sumstats.py and ldsc_sumstats.py
* **Ref_Genomes** > contains the genome of reference used for the ldsc sofware. 
	* For the use of munge_sumstats.py > HapMap3/w_hm3.snplist
	* For the use of ldsc.py > eur_w_ld_chr/*
* **Results** > once the scripts are run it will contain csv files with the results from the sotware. It also contains the results in csv form from the test done with the datasets obtained from the [bulik paper](https://www.nature.com/articles/ng.3406#additional-information). The *"ldsc_genetic_correlation.csv"* can be obtained running the scripts from the CONTROLS folder inside scripts.
* **scripts** > Contains copies of the [ldsc](https://github.com/bulik/ldsc) and [HDL](https://github.com/zhenin/HDL) git repositories _[please download the repositories into this folder for the correct functioning_].
	* CONTROLS > contains the scripts and csv to obtain the test from bulik. 
	* **pipeline** > contains all the scripts to run the entire pipeline with ldsc. The HDL pipeline needs to be tested. 
* **SumStats** 
	* This folder is empty. The folders will be created by running *"scripts/create_sumstats_folders.py"*
	* **RAW** > Contains the raw files.
	* **Munged** > Contains the munged files.
	* **Wrangled** > Contains the wrangled files [empty for now].
	* **csv datasets**.



## Scripts
* scripts/create_sumstats_folders.py > Create folders to store the data inside SumStats.

### Pipeline
0. **pipeline/0_gwas_catalog_cleaning.Rmd** > only works for cleaning and selecting relevant datasets from the GWAS catalog. Is only used once.
1. **pipeline/1_from_excell_catalog_to_final_csv.py** > Takes *SumStats/excell_sumstats_description.csv* and transforms it into *SumStats/final_sumstats_description.csv*.
2. **pipeline/2_add_Ncol.py** > If the N_col column from the *final_sumstats_description.csv* is empty it will take the value from the column N_num for that row and create a N-col. [~~Needs fixing, the N column is necessary for the HDL software.~~ *NOT USED AT THE MOMENT*]
3. **pipeline/3_munge_sumstats_from_csv.py** > Automatises the munge_sumstats.py from the ldsc software that homogeneises the data.
4. **pipeline/4_create_pairs_diseases.py** > Takes the filepaths from the munged and wrangled files and whether ldsc an HDL have been performed.
5. Correlation softwares.
	* **pipeline/5A_ldsc_run_pairs_automatised.py** > automatises the use of ldsc from the paired_datasets.csv paths.
	* **pipeline/5B_HDL_run_pairs_automatised.r** > automatises the use of ldsc from the paired_datasets.csv paths.
6. Extract results into a csv from the results/{software} folder and creates a csv with the results.
	* **scripts/pipeline/6A_ldsc_read_results_extract_gencor.py**
	* **scripts/pipeline/6B_HDL_read_results_extract_gencor.py**
7. **scripts/pipeline/7-1_p_correction.ipynb** > Script to correct the p-value.
8. **scripts/pipeline/8_gwaslab.ipynb** > Script to visualize heatmap [*at the moment only for the results from ldsc*]


*************************************************************************************************

### Datasets
The csv datasets inside the SumStats folder are (in order of creation and use):
1. **SumStats/excell_sumstats_description.csv** > This file comes from an excell containing the datasets used and manually annotated to contain the following columns:
	1. title > title of paper where dataset is published.
	2. pubmedID 
	3. efoTraits
	4. label > given label to recognise the dataset.
	5. condition_label > given name to the condition to create the folder where the data will b saved.
	6. summaryStatistics > download link
	7. id > id of reference to the catalog of origin
	8. filename > id with extension
	9. Ancestry
	10. ref_genome
	11. snp
	12. a1 (effect allele)
	13. a2 (other allele)
	14. frq (effect allele frequency)
	15. FRQ_U
	16. FRQ_A
	17. z (z-score)
	18. beta
	19. OR (odds ration)
	20. se (standard error)
	21. p (p-value)
	22. N_col (column containing the sample size)
	23. N_num (sample size)
	24. Nca_col (column with cases for each snp)
	25. Nca_val (column with cases size)
	26. Nco_col (column with control for each snp)
	27. Nco_val (column with control size)
	28. INFO 
	29. ignore > this column is manually annotated when it's observed that the dataset contains duplicated columns.

2. **SumStats/final_sumstats_description.csv** > This file is created from the scripts/pipeline/1_from_excell_catalog_to_final_csv.py
3. **SumStats/paired_datasets.csv** > This file is generated from the scripts/pipeline/4_create_pairs_diseases.py






## How to run

1. Change the config file to match the local paths. Not all scripts have been automatised.

2. Follow the pipeline 
[Pipeline]()

