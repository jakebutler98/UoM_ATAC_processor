# ATAC-seq Processing Pipeline

A modular, reproducible ATAC-seq processing pipeline for paired-end ATAC-seq data.

The pipeline is designed for HPC environments using SLURM, but the core workflow can also be run manually for individual samples using Python. All system-specific paths are defined in a local YAML configuration file so that the code can be reused across projects and computing environments.

---

## Quick Start

Clone the repository:

```bash
git clone https://github.com/jakebutler98/UoM_ATAC_processor.git
cd UoM_ATAC_processor
```

Create and activate the conda environment (if not internal user):
Almost all of the software requirements are contained within ATAC_seq. This is a conda env that is activated within the SLURM script. This requires you to be familiar with the 'project environment system' set up within DMDS. For further assistance please contact Jake Butler or Paul Martin.

```bash
conda env create -f environment.yml
conda activate UoM_ATAC_processor
```

Create a local configuration file:

```bash
cp configs/config.example.yaml configs/config.yaml
nano configs/config.yaml
```

Create a sample list:

```bash
nano samples.txt
```

Edit the SLURM submission script:

```bash
nano main/run_atac_SLURM.sh
```

Submit the pipeline:

```bash
sbatch main/run_atac_SLURM.sh
```

---

## Pipeline Overview

For each sample, the pipeline performs the following steps:

1. FastQC on raw FASTQ files
2. Adapter trimming and read filtering using fastp
3. FastQC on trimmed FASTQ files
4. Alignment to the reference genome using Bowtie2
5. BAM sorting and indexing using samtools
6. Duplicate removal and alignment QC using Picard
7. Filtering of aligned reads
   - removal of mitochondrial reads
   - MAPQ >= 30
   - properly paired reads only
   - removal of duplicate, secondary, supplementary and QC-failed reads
   - optional ENCODE blacklist removal
8. BigWig coverage generation using deepTools
9. Peak calling using MACS3 in BAMPE mode
10. Per-sample ATAC-seq QC metrics
    - FRiP in peaks
    - FRiP around TSS regions
    - mitochondrial fraction
    - duplicate rate
    - fragment length distribution
11. ATACseqQC-based TSS enrichment analysis
12. MultiQC summary report

---

## Repository Structure

```text
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
│       ├── ATACseqQC.py
│       ├── coverage.py
│       ├── fastqc.py
│       ├── helpers.py
│       ├── macs3.py
│       ├── multiqc.py
│       ├── qc.py
│       └── trimming.py
├── environment.yml
├── README.md
├── LICENSE
└── CITATION.cff
```

---

## Input Data Format

The pipeline expects one directory per sample inside the raw input directory.

Example:

```text
RAW_input_dir/
├── SAMPLE_1/
│   ├── SAMPLE_1_L001_R1.fastq.gz
│   ├── SAMPLE_1_L001_R2.fastq.gz
│   ├── SAMPLE_1_L002_R1.fastq.gz
│   └── SAMPLE_1_L002_R2.fastq.gz
└── SAMPLE_2/
    ├── SAMPLE_2_L001_R1.fastq.gz
    └── SAMPLE_2_L001_R2.fastq.gz
```

Requirements:

- Data must be paired-end.
- Each sample must have its own directory.
- Sample directory names must match the names used in `samples.txt`.
- Multiple lanes for the same sample are automatically merged before trimming.
- Single-lane samples are processed directly.

---

## Installation

Create the conda environment:

```bash
conda env create -f environment.yml
```

Activate the environment:

```bash
conda activate UoM_ATAC_processor
```

On some HPC systems, tools such as FastQC, deepTools, samtools or Java may be provided through environment modules rather than conda. If required, load these modules before running the pipeline.

Example:

```bash
module load functional_genomics/qc/fastqc/0.12.1
module load functional_genomics/tools/deeptools/3.5.2
```

---

## Configuration

All user-specific paths are stored in a local YAML file.

Copy the example configuration:

```bash
cp configs/config.example.yaml configs/config.yaml
```

Then edit:

```bash
nano configs/config.yaml
```

The local `configs/config.yaml` file should not be committed to GitHub because it contains project-specific paths.

### Required path settings

The `paths` section tells the pipeline where to find input data and where to write output files.

Example:

```yaml
paths:
  RAW_input_dir: "/path/to/raw_fastq"
  Trimmed_dir: "/path/to/output/temp_trimming"
  aligned_dir: "/path/to/output/temp_align"
  Reads_quality_dir: "/path/to/output/fastp"
  dedup_alignments_dir: "/path/to/output/temp_align_dedup"
  cleaned_alignments_dir: "/path/to/output/clean_alignments"
  macs3_dir: "/path/to/output/macs3"
  coverages_dir: "/path/to/output/coverages"
  other_qc_dir: "/path/to/output/qc"
  fastqc_untrimmed_dir: "/path/to/output/qc/fastqc_untrimmed"
  fastqc_trimmed_dir: "/path/to/output/qc/fastqc_trimmed"
  logs_dir: "/path/to/output/logs"
```

### Required reference settings

The `references` section should include all required reference files.

Example:

```yaml
references:
  bowtie2_index: "/path/to/bowtie2/index/genome"
  genome_fasta: "/path/to/genome.fa"
  picard: "/path/to/picard.jar"
  genome_file: "/path/to/genome.genome"
  tss_bed: "/path/to/TSS_sites.bed"
```

Where:

- `bowtie2_index` is the prefix of the Bowtie2 index.
- `genome_fasta` is the genome FASTA used by Picard.
- `picard` is the path to the Picard `.jar` file.
- `genome_file` is a chromosome sizes/genome file used by pybedtools.
- `tss_bed` is a BED file containing TSS positions used for FRiP around TSS regions.

### Options

Example:

```yaml
options:
  threads: 8
  blacklist_bed: null
  atacseqqc_dir: null
  pybedtools_tmp: "/scratch/tmp_pybedtools"
```

- `threads`: number of threads to use.
- `blacklist_bed`: optional BED file of regions to remove. Set to `null` to skip blacklist filtering.
- `atacseqqc_dir`: optional override for ATACseqQC output. If `null`, output is written inside `other_qc_dir`.
- `pybedtools_tmp`: temporary directory for pybedtools operations. This is best placed on scratch space.

---

## Sample List

For SLURM execution, create a file called `samples.txt` in the repository root.

You can start from the example:

```bash
nano samples.txt
```

The file should contain one sample name per line:

```text
SAMPLE_1
SAMPLE_2
SAMPLE_3
```

These names must exactly match the sample folder names inside `RAW_input_dir`.

For example, if your raw data are arranged as:

```text
RAW_input_dir/
├── C_1a/
├── C_1b/
└── C_1c/
```

then `samples.txt` should contain:

```text
C_1a
C_1b
C_1c
```

---

## Running the Pipeline Manually

Run the full pipeline for one sample:

```bash
python src/main_ATAC.py \
  -i SAMPLE_NAME \
  --config configs/config.yaml \
  --threads 8
```

Run selected steps only:

```bash
python src/main_ATAC.py \
  -i SAMPLE_NAME \
  --config configs/config.yaml \
  --threads 8 \
  -s trimming \
  -s align \
  -s filter \
  -s macs3
```

Use `--force` to overwrite existing outputs:

```bash
python src/main_ATAC.py \
  -i SAMPLE_NAME \
  --config configs/config.yaml \
  --threads 8 \
  --force
```

---

## Available Pipeline Steps

The following step names can be passed using `-s`:

```text
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
```

Examples:

Run only raw FastQC:

```bash
python src/main_ATAC.py \
  -i SAMPLE_NAME \
  --config configs/config.yaml \
  -s fastqc_before_trimming
```

Run trimming and post-trimming FastQC:

```bash
python src/main_ATAC.py \
  -i SAMPLE_NAME \
  --config configs/config.yaml \
  -s trimming \
  -s fastqc_after_trimming
```

Run alignment, deduplication and filtering:

```bash
python src/main_ATAC.py \
  -i SAMPLE_NAME \
  --config configs/config.yaml \
  -s align \
  -s align_qc \
  -s filter
```

Run downstream analysis only:

```bash
python src/main_ATAC.py \
  -i SAMPLE_NAME \
  --config configs/config.yaml \
  -s coverage \
  -s macs3 \
  -s qc \
  -s ATACseqQC \
  -s multiqc
```

---

## Running with SLURM

The SLURM submission script is located at:

```text
main/run_atac_SLURM.sh
```

Before submitting, edit the script:

```bash
nano main/run_atac_SLURM.sh
```

Check the following:

1. SLURM resources
   - job name
   - partition
   - CPUs
   - wall time
   - array range

2. Log paths
   - make sure `#SBATCH -o` points to a valid directory
   - make sure `#SBATCH -e` points to a valid directory

3. Repository location
   - make sure the script changes into the correct repository directory

4. Environment activation
   - activate the correct conda/project environment
   - load any required modules

5. Sample file
   - make sure the script reads the correct `samples.txt`

6. Pipeline steps
   - decide whether to run the full pipeline or selected steps

Submit the job:

```bash
sbatch main/run_atac_SLURM.sh
```

Check job status:

```bash
squeue -u $USER
```

Inspect logs:

```bash
less /path/to/logs/job_name-jobid_arrayid.log
```

---

## Example SLURM Workflow

A typical test workflow is:

1. Clone the repo into a fresh directory.
2. Copy and edit `configs/config.yaml`.
3. Create `samples.txt` with one test sample.
4. Edit `main/run_atac_SLURM.sh`.
5. Run one small step first, such as FastQC.
6. If that works, run trimming.
7. Then run alignment and downstream steps.

Example command for testing one step:

```bash
python src/main_ATAC.py \
  -i SAMPLE_NAME \
  --config configs/config.yaml \
  --threads 8 \
  -s fastqc_before_trimming
```

---

## Output Structure

The exact output paths depend on `configs/config.yaml`.

A typical structure is:

```text
output/
├── fastp/
├── fastqc_untrimmed/
├── fastqc_trimmed/
├── temp_align/
├── temp_align_dedup/
├── clean_alignments/
├── coverages/
├── macs3/
└── qc/
    ├── SAMPLE_1/
    │   ├── SAMPLE_1_qc_metrics.tsv
    │   ├── SAMPLE_1_fragment_length_count.txt
    │   ├── SAMPLE_1_markdup_qc.txt
    │   ├── SAMPLE_1_alignment_metrics_qc.txt
    │   └── ATACseqQC/
    ├── qc_metrics_all_samples.tsv
    ├── fraglength_fig.png
    └── multiqc/
```

---

## Main Outputs

### Trimmed FASTQs

```text
Trimmed_dir/SAMPLE/SAMPLE_trimmed_R1.fastq.gz
Trimmed_dir/SAMPLE/SAMPLE_trimmed_R2.fastq.gz
```

### Aligned BAM

```text
aligned_dir/SAMPLE/SAMPLE_align.bam
```

### Deduplicated BAM

```text
dedup_alignments_dir/SAMPLE/SAMPLE_align_dedup.bam
```

### Filtered BAM

```text
cleaned_alignments_dir/SAMPLE/SAMPLE_align_dedup_filtered.bam
```

### BigWig coverage

```text
coverages_dir/SAMPLE/SAMPLE_coverage.bw
```

### MACS3 peaks

```text
macs3_dir/SAMPLE/SAMPLE_peaks.narrowPeak
```

### QC metrics

```text
other_qc_dir/SAMPLE/SAMPLE_qc_metrics.tsv
other_qc_dir/qc_metrics_all_samples.tsv
```

### MultiQC report

```text
other_qc_dir/multiqc/multiqc_report.html
```

---

## Blacklist Filtering

Blacklist filtering is optional.

To enable blacklist filtering:

```yaml
options:
  blacklist_bed: "/path/to/hg38-blacklist.v2.bed"
```

To disable blacklist filtering:

```yaml
options:
  blacklist_bed: null
```

---

## Alignment Parameters

The Bowtie2 alignment step uses:

```text
--very-sensitive -k 1 -X 2000
```

Meaning:

- `--very-sensitive`: increases alignment sensitivity.
- `-k 1`: reports one best alignment per read.
- `-X 2000`: allows paired-end fragments up to 2000 bp, which is suitable for ATAC-seq nucleosomal fragments.

The filtering step then keeps high-confidence read pairs using MAPQ and SAM flag filters.

---

## Common Issues

### 1. `config.yaml` not found

Make sure you created it:

```bash
cp configs/config.example.yaml configs/config.yaml
```

Then run with:

```bash
--config configs/config.yaml
```

### 2. Sample not found

Check that the sample name matches the folder name in `RAW_input_dir`.

For example:

```text
RAW_input_dir/C_1a/
```

must be run as:

```bash
-i C_1a
```

### 3. No FASTQ files found

Check that files end in one of the expected patterns:

```text
.fastq.gz
.fq.gz
```

and that paired files contain R1/R2 or 1/2 naming consistent with the pipeline.

### 4. Bowtie2 index not found

Check the `bowtie2_index` prefix in `config.yaml`.

Do not include `.bt2` at the end. Use the shared prefix.

### 5. Picard fails

Check:

- Java is available.
- `picard` points to the correct `.jar`.
- `genome_fasta` exists.

### 6. pybedtools temporary directory error

Set a writable scratch directory:

```yaml
options:
  pybedtools_tmp: "/scratch/your_user/temp_pybedtools"
```

### 7. MultiQC report missing

This is still in development

---

## Notes

- This pipeline is designed for paired-end ATAC-seq data.
- It assumes a reference genome and Bowtie2 index have already been prepared.
- It assumes standard command-line bioinformatics tools are available either through conda or environment modules.
- The pipeline is intended to be portable by changing only `configs/config.yaml` and `samples.txt`.

---

## Author

Developed by Jake Butler for internal and collaborative ATAC-seq analyses.