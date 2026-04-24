# ATAC-seq Processing Pipeline

A modular, reproducible ATAC-seq processing pipeline for paired-end sequencing data.

Designed for HPC (SLURM) environments but fully runnable per-sample via Python. 
All system-specific paths are externalised into a YAML config to ensure portability.

---

## Overview

For each sample, the pipeline performs:

1. FastQC on raw reads  
2. Adapter trimming and filtering (fastp)  
3. FastQC on trimmed reads  
4. Alignment to reference genome (Bowtie2)  
5. BAM sorting and indexing (samtools)  
6. Duplicate removal + alignment QC (Picard)  
7. Read filtering:
   - remove chrM
   - MAPQ ≥ 30
   - properly paired reads only
   - remove duplicates / secondary / supplementary reads
   - optional ENCODE blacklist filtering
8. Coverage track generation (deepTools → BigWig)  
9. Peak calling (MACS3, BAMPE mode)  
10. QC metrics:
    - FRiP (peaks and TSS)
    - mitochondrial fraction
    - duplication rate
    - fragment length distribution  
11. ATACseqQC:
    - TSS enrichment
    - shifted BAM generation  
12. MultiQC summary report  

---

## Pipeline Structure

UoM_ATAC_processor/
├── configs/
│   └── config.example.yaml
├── main/
│   ├── run_atac_SLURM.sh
│   └── sample.example.txt
├── r/
│   └── ATACseqQC_for_pipeline.r
├── src/
│   ├── configuration.py
│   ├── main_ATAC.py
│   └── steps/
│       ├── align.py
│       ├── trimming.py
│       ├── fastqc.py
│       ├── coverage.py
│       ├── macs3.py
│       ├── qc.py
│       ├── ATACseqQC.py
│       ├── multiqc.py
│       └── helpers.py
├── environment.yml
├── README.md

---

## Input Format

RAW_input_dir/
└── SAMPLE_NAME/
    ├── sample_L001_R1.fastq.gz
    ├── sample_L001_R2.fastq.gz
    ├── sample_L002_R1.fastq.gz
    └── sample_L002_R2.fastq.gz

Multiple lanes are automatically merged. Single-lane samples are handled directly.

---

## Installation

Create environment:

conda env create -f environment.yml  
conda activate UoM_ATAC_processor  

---

## Configuration

cp configs/config.example.yaml configs/config.yaml  

Edit config.yaml:

Key sections:

paths:
  RAW_input_dir: "/path/to/raw"
  cleaned_alignments_dir: "/path/to/clean_bams"
  macs3_dir: "/path/to/macs3_output"
  coverages_dir: "/path/to/bigwigs"
  other_qc_dir: "/path/to/qc"

references:
  bowtie2_index: "/path/to/index"
  genome_fasta: "/path/to/genome.fa"
  picard: "/path/to/picard.jar"

options:
  threads: 8
  blacklist_bed: null

---

## Running the Pipeline

Run full pipeline:

python src/main_ATAC.py -i SAMPLE_NAME --config configs/config.yaml --threads 8

Run specific steps:

python src/main_ATAC.py -i SAMPLE_NAME --config configs/config.yaml \
  -s trimming -s align -s filter -s macs3

Available steps:

fastqc_before_trimming  
trimming  
fastqc_after_trimming  
align  
align_qc  
filter  
coverage  
macs3  
qc  
ATACseqQC  
multiqc  

Overwrite outputs:

--force

---

## SLURM Execution

Edit:

main/run_atac_SLURM.sh

Submit:

sbatch main/run_atac_SLURM.sh

Sample file format:

SAMPLE_1  
SAMPLE_2  
SAMPLE_3  

---

## Output Structure

output/
├── fastqc/
├── fastp/
├── temp_align/
├── clean_alignments/
├── coverages/
├── macs3/
└── qc/
    ├── SAMPLE_1/
    ├── multiqc/
    └── qc_metrics_all_samples.tsv

---

## Notes

- Do NOT commit config.yaml
- Designed for paired-end ATAC-seq only
- Requires standard bioinformatics tools installed or via modules

---

## .gitignore (recommended)

configs/config.yaml  
output/  
logs/  
*.bam  
*.bai  
*.bw  
__pycache__/  

---

## Author

Jake Butler
