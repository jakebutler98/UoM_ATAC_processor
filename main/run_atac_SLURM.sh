#!/bin/bash --login
#SBATCH -J chondrocytes_fastqc_trim                 # Job name
#SBATCH -p multicore                     # Partition
#SBATCH -n 1                             # Number of tasks (usually 1 for array jobs)
#SBATCH -c 8                             # CPUs per task
#SBATCH -t 6:00:00                            # Time (minutes)
#SBATCH -a 1-4                          # Array range
#SBATCH -o /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/chondrocytes/data/logs/%x-%A_%a.log
#SBATCH -e /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/chondrocytes/data/logs/%x-%A_%a.log

INDEX=$SLURM_ARRAY_TASK_ID
# CD to directory
cd /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/chondrocytes/scripts

# Inform the app how many cores we requested for our job. The app can use this many cores.
# The special $NSLOTS keyword is automatically set to the number used on the -pe line above.
export OMP_NUM_THREADS=$NSLOTS

# activate all neeeded modules and packages
# source activate personal_software
activate_project /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq

#Patch because of permission issues
module load functional_genomics/qc/fastqc/0.12.1
#module load functional_genomics/peak/macs2/2.2.9.1


module load functional_genomics/utils/java/17.0.7
module load functional_genomics/tools/deeptools/3.5.2
# module load tools/java/17 #not the same

# this contains fastp, bedtools, etc

#module load tools/java/1.8.0

SAMPLE=$(awk "NR==$INDEX" samples.txt)

sleep $(($INDEX*20))

python ./main_ATAC.py -i ${SAMPLE} -s align -s align_qc -s filter -s coverage -s macs3