#!/bin/bash --login
#SBATCH -J test_V2_pipeline               # Job name
#SBATCH -p multicore                     # Partition
#SBATCH -n 1                             # Number of tasks (usually 1 for array jobs)
#SBATCH -c 8                             # CPUs per task
#SBATCH -t 6:00:00                            # Time (minutes)
#SBATCH -a 2-4                          # Array range
#SBATCH -o /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/chondrocytes/data/logs/%x-%A_%a.log
#SBATCH -e /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/chondrocytes/data/logs/%x-%A_%a.log

INDEX=$SLURM_ARRAY_TASK_ID
# CD to directory
cd /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/chondrocytes/scripts

# Thread env for tools that respect it
export TOOL_THREADS=${SLURM_CPUS_PER_TASK}

# Cap numeric libs to avoid the abort
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

export PYTHONNOUSERSITE=1
unset PYTHONPATH
export MPLBACKEND=Agg
export MPLCONFIGDIR=/tmp/$USER/mpl
mkdir -p "$MPLCONFIGDIR"

# activate all neeeded modules and packages
# source activate personal_software
activate_project /mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq

# load certain modules that i didnt install personally
module load functional_genomics/qc/fastqc/0.12.1
module load functional_genomics/tools/deeptools/3.5.2

SAMPLE=$(awk "NR==$INDEX" samples.txt)

sleep $(($INDEX*20))

python -X faulthandler ./main_ATAC.py -i "${SAMPLE}" --config ./configs/config.yaml --threads "${TOOL_THREADS}" -s fastqc_before_trimming