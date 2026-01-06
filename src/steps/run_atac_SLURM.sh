#!/bin/bash --login
#SBATCH -J test_V2_pipeline               # Job name
#SBATCH -p multicore                     # Partition
#SBATCH -n 1                             # Number of tasks (usually 1 for array jobs)
#SBATCH -c 8                             # CPUs per task
#SBATCH -t 6:00:00                            # Time (minutes)
#SBATCH -a 1-1                          # Array range
#SBATCH -o /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/chondrocytes/data/logs/%x-%A_%a.log
#SBATCH -e /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/chondrocytes/data/logs/%x-%A_%a.log

INDEX=$SLURM_ARRAY_TASK_ID
# CD to directory
cd /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/chondrocytes/scripts

# Thread env for tools that respect it
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK}

# activate all neeeded modules and packages
# source activate personal_software
activate_project /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq

#Patch because of permission issues
module load functional_genomics/qc/fastqc/0.12.1

SAMPLE=$(awk "NR==$INDEX" samples.txt)

sleep $(($INDEX*20))

python ./main_ATAC.py -i "${SAMPLE}" --config ./configs/config.yaml --threads "${SLURM_CPUS_PER_TASK}" \
    -s fastqc_before_trimming -s trimming -s fastqc_after_trimming \-s align -s align_qc -s filter -s coverage -s macs3 -s qc -s ATACseqQC -s multiqc