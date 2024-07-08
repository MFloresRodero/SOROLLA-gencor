List of files and download links:

* The w_hm3.snplist can also be found inside the eur_w_ld_chr folder. 
* However, I used the data downloaded into the HapMap3.
* They are the same, but the pipeline is set that way.

############## FOR MUNGE

HapMap3 SNP-list
# https://zenodo.org/records/7773502
# File Name: w_hm3.snplist.gz

HOW TO DOWNLOAD
# [inside Ref_Genomes]
# mkdir HapMap3
# [inside Ref_Genomes/Hapmap/]
# wget https://zenodo.org/records/7773502/files/w_hm3.snplist.gz?download=1



############## FOR LDSC

Reference LD score files
# https://ibg.colorado.edu/cdrom2021/Day06-nivard/GenomicSEM_practical/eur_w_ld_chr/

HOW TO DOWNLOAD
# [inside Ref_Genomes/]
# A folder named eur_w_ld_chr/ will be created
# wget -r -np -nH --cut-dirs=3 -R "index.html*" https://ibg.colorado.edu/cdrom2021/Day06-nivard/GenomicSEM_practical/eur_w_ld_chr/



************************************************************************************************
************************************************************************************************
USEFUL REFERENCE DATA BUT NOT USED AT THE MOMENT
************************************************************************************************
### SNP genotype data
#### https://www.broadinstitute.org/medical-and-population-genetics/hapmap-3
#### File Name: hapmap3_r1_b36_fwd.qc.poly.tar.bz2 
#### File Description:  tarball of QC+ polymorphic genotype data per population, formatted as PLINK PED and MAP files [833 MB]
************************************************************************************************
************************************************************************************************