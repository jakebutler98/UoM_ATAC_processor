ATAC-seq Processing Pipeline
============================

This repository contains a modular, reproducible ATAC-seq processing pipeline
designed for paired-end sequencing data generated using in-house library
preparation protocols.

The pipeline is designed for HPC environments (SLURM) and focuses on:
- Robust alignment and filtering
- ATAC-specific QC metrics
- Reproducibility via configuration files
- Clean separation of code, configuration, and execution logic


Directory Structure
-------------------

.
├── configs/
│   ├── config.example.yaml      # Example configuration (commit to git)
│   └── config.yaml              # User-specific config (DO NOT COMMIT)
│
├── docs/
│   └── (future documentation, figures, notes)
│
├── environment.yml              # Conda environment specification
│
├── main/
│   ├── run_atac_SLURM.sh         # SLURM submission script
│   └── sample.example.txt        # Example sample list
│
├── r/
│   └── ATACseqQC_for_pipeline.r  # ATACseqQC R script
│
├── src/
│   ├── main_ATAC.py              # Pipeline entry point
│   ├── configuration.py          # Config loader (YAML + defaults)
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
│
└── README.md


Pipeline Overview
-----------------

For each sample, the pipeline performs:

1. Adapter trimming and QC (fastp)
2. Alignment to reference genome (bowtie2)
3. Duplicate removal and alignment QC (Picard + samtools)
4. Filtering:
   - MAPQ >= 30
   - Properly paired reads
   - Removal of chrM
   - Optional ENCODE blacklist removal
5. Coverage track generation (deepTools)
6. Peak calling (MACS3, BAMPE mode)
7. ATAC-specific QC:
   - FRiP (TSS and peaks)
   - Mitochondrial fraction
   - Duplicate rate
   - Fragment length distribution
8. ATACseqQC (TSS enrichment, shifted BAM)
9. Aggregated reporting (MultiQC)


Configuration
-------------

All user-specific paths and options are defined in a YAML configuration file.

Create your config file:

    cp configs/config.example.yaml configs/config.yaml

Edit config.yaml to match your environment.

IMPORTANT:
- config.yaml contains absolute paths and must NOT be committed to git
- Only config.example.yaml should be tracked


Running the Pipeline
--------------------

Single sample (example):

    python src/main_ATAC.py \
      -i SAMPLE_NAME \
      --config configs/config.yaml \
      --threads 8

Selective steps:

    python src/main_ATAC.py \
      -i SAMPLE_NAME \
      --config configs/config.yaml \
      -s align -s align_qc -s filter -s macs3


SLURM Execution
---------------

Use the provided SLURM script:

    sbatch main/run_atac_SLURM.sh

Samples are read from a text file (one sample per line).


Blacklist Filtering
-------------------

Blacklist filtering is enabled automatically if the following is set in
config.yaml:

    options:
      blacklist_bed: /path/to/hg38-blacklist.v2.bed

If unset or null, blacklist filtering is skipped.


Conda Environment
-----------------

Create the environment using:

    conda env create -f environment.yml

Activate it before running the pipeline.


GitHub Notes
------------

Recommended .gitignore entries:

- configs/config.yaml
- __pycache__/
- *.log
- *.bam
- *.bai
- *.bw
- output directories

This repository is intended to be portable across systems by modifying only
config.yaml.


Status
------

The pipeline has been tested end-to-end on representative ATAC-seq samples
and is considered production-ready.


Author
------

Developed by:
[Your Name]

Maintained for internal and collaborative ATAC-seq analyses.