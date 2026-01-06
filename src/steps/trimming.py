import os
import logging
from steps.helpers import outputs_exist, clean_dir, run_cmd

def run_fastp(Configuration):
    """
    UNIVERSAL trimming:
    - If multiple lanes: merge raw R1 and R2 files first
    - If only one lane: use raw R1 and R2 directly
    - Then run fastp once on the final R1/R2 pair
    """
    sample = Configuration.file_to_process

    input_dir = os.path.join(Configuration.RAW_input_dir, sample)
    output_dir = os.path.join(Configuration.Trimmed_dir, sample)
    quality_dir = os.path.join(Configuration.Reads_quality_dir, sample)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(quality_dir, exist_ok=True)

    trimmed_R1 = os.path.join(output_dir, f"{sample}_trimmed_R1.fastq.gz")
    trimmed_R2 = os.path.join(output_dir, f"{sample}_trimmed_R2.fastq.gz")
    html_out = os.path.join(quality_dir, f"{sample}.fastp.html")
    json_out = os.path.join(quality_dir, f"{sample}.fastp.json")

    if (not Configuration.force) and outputs_exist([trimmed_R1, trimmed_R2, html_out, json_out]):
        logging.info("trimming: outputs exist; skipping (use --force to overwrite)")
        return

    if Configuration.force:
        # Only clean the trimming output dir, not raw input
        clean_dir(output_dir)
        clean_dir(quality_dir)

    raw_files = sorted([f for f in os.listdir(input_dir) if f.endswith(".gz")])
    if len(raw_files) == 0:
        raise FileNotFoundError(f"No FASTQ files found in {input_dir}")

    R1_files = [f for f in raw_files if f.endswith("1.fq.gz") or f.endswith("1.fastq.gz")]
    R2_files = [f for f in raw_files if f.endswith("2.fq.gz") or f.endswith("2.fastq.gz")]

    if len(R1_files) == 0 or len(R2_files) == 0:
        raise FileNotFoundError(f"Could not find R1/R2 files for {sample}")

    if len(R1_files) != len(R2_files):
        raise RuntimeError(f"Mismatched number of R1 and R2 files in {input_dir}")

    logging.info(f"Found {len(R1_files)} raw lanes for sample {sample}")

    if len(R1_files) == 1:
        logging.info("Single lane detected – skipping merge step")
        input_R1 = os.path.join(input_dir, R1_files[0])
        input_R2 = os.path.join(input_dir, R2_files[0])
    else:
        input_R1 = os.path.join(output_dir, f"{sample}_merged_R1.fastq.gz")
        input_R2 = os.path.join(output_dir, f"{sample}_merged_R2.fastq.gz")

        logging.info("Merging raw R1 files...")
        run_cmd("cat " + " ".join([os.path.join(input_dir, f) for f in R1_files]) + f" > {input_R1}",
                shell=True, check=True)

        logging.info("Merging raw R2 files...")
        run_cmd("cat " + " ".join([os.path.join(input_dir, f) for f in R2_files]) + f" > {input_R2}",
                shell=True, check=True)

        logging.info("Finished merging raw FASTQs")

    threads = str(getattr(Configuration, "threads", 8))

    cmd = [
        "fastp",
        "-i", input_R1,
        "-I", input_R2,
        "-o", trimmed_R1,
        "-O", trimmed_R2,
        "-w", threads,
        "-h", html_out,
        "-j", json_out,
        "-R", sample,
        "-p",
        "--adapter_sequence=AGATGTGTATAAGAGACAG",
        "--adapter_sequence_r2=AGATGTGTATAAGAGACAG",
        "--trim_poly_g",
        "--trim_poly_x",
        "--length_required=30"
    ]

    logging.info("Running fastp...")
    run_cmd(cmd, check=True)
    logging.info(f"fastp complete for sample: {sample}")