import os
import logging
from steps.helpers import outputs_exist, run_cmd

def _fastqc_expected_outputs(input_files, output_dir):
    """
    FastQC outputs: <basename>_fastqc.html and <basename>_fastqc.zip
    where basename strips .fastq.gz / .fq.gz
    """
    expected = []
    for f in input_files:
        base = os.path.basename(f)
        for ext in [".fastq.gz", ".fq.gz", ".fastq", ".fq"]:
            if base.endswith(ext):
                base = base[: -len(ext)]
                break
        expected.append(os.path.join(output_dir, f"{base}_fastqc.html"))
        expected.append(os.path.join(output_dir, f"{base}_fastqc.zip"))
    return expected

def run_fastqc(Configuration, input_files, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    expected = _fastqc_expected_outputs(input_files, output_dir)
    if (not Configuration.force) and outputs_exist(expected):
        logging.info(f"fastqc: outputs exist in {output_dir}; skipping (use --force to overwrite)")
        return

    threads = str(getattr(Configuration, "threads", 8))
    cmd = ["fastqc", "-o", output_dir, "-t", threads] + input_files
    run_cmd(cmd, check=True)

def qc_before_trimming(Configuration):
    sample = Configuration.file_to_process
    raw_dir = os.path.join(Configuration.RAW_input_dir, sample)
    output_dir = os.path.join(Configuration.fastqc_untrimmed_dir, sample)

    raw_files = [
        os.path.join(raw_dir, f)
        for f in os.listdir(raw_dir)
        if f.endswith(".fastq.gz") or f.endswith(".fq.gz")
    ]
    if len(raw_files) == 0:
        raise FileNotFoundError(f"No raw FASTQs found in {raw_dir}")

    run_fastqc(Configuration, raw_files, output_dir)

def qc_after_trimming(Configuration):
    sample = Configuration.file_to_process
    trimmed_dir = os.path.join(Configuration.Trimmed_dir, sample)
    output_dir = os.path.join(Configuration.fastqc_trimmed_dir, sample)

    trimmed_files = [
        os.path.join(trimmed_dir, f)
        for f in os.listdir(trimmed_dir)
        if f.endswith("_trimmed_R1.fastq.gz") or f.endswith("_trimmed_R2.fastq.gz")
    ]
    if len(trimmed_files) == 0:
        raise FileNotFoundError(f"No trimmed FASTQs found in {trimmed_dir}")

    run_fastqc(Configuration, trimmed_files, output_dir)