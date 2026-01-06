########################################
# script for running macs3
########################################

import os
import logging
from steps.helpers import clean_dir, outputs_exist, run_cmd

def run_macs3_ATAC(Configuration):
    sample = Configuration.file_to_process
    logging.info("running macs3 (ATAC)")

    filtered_align_file = os.path.join(
        Configuration.cleaned_alignments_dir, sample, f"{sample}_align_dedup_filtered.bam"
    )

    macs3_output_dir = os.path.join(Configuration.macs3_dir, sample)
    os.makedirs(macs3_output_dir, exist_ok=True)

    expected_peak = os.path.join(macs3_output_dir, f"{sample}_peaks.narrowPeak")

    if (not Configuration.force) and outputs_exist([expected_peak]):
        logging.info("macs3: peaks exist; skipping (use --force to overwrite)")
        return

    if Configuration.force:
        clean_dir(macs3_output_dir)

    run_cmd([
        "macs3", "callpeak",
        "-f", "BAMPE",
        "-g", "hs",
        "--keep-dup", "all",
        "-n", sample,
        "-t", filtered_align_file,
        "--outdir", macs3_output_dir
    ], check=True)

def run_macs3_CHIP(Configuration):
    sample = Configuration.file_to_process
    logging.info("running macs3 (CHIP)")

    filtered_align_file = os.path.join(
        Configuration.cleaned_alignments_dir, sample, f"{sample}_align_filtered_macs3.bam"
    )

    macs3_output_dir = os.path.join(Configuration.macs3_dir, sample)
    os.makedirs(macs3_output_dir, exist_ok=True)

    expected_peak = os.path.join(macs3_output_dir, f"{sample}_peaks.narrowPeak")

    if (not Configuration.force) and outputs_exist([expected_peak]):
        logging.info("macs3: peaks exist; skipping (use --force to overwrite)")
        return

    if Configuration.force:
        clean_dir(macs3_output_dir)

    cmd = [
        "macs3", "callpeak",
        "-f", "BAMPE",
        "-g", "hs",
        "--keep-dup", "all",
        "-n", sample,
        "-t", filtered_align_file,
        "--outdir", macs3_output_dir
    ]

    if Configuration.input_background is not None:
        background_bam = os.path.join(
            Configuration.cleaned_alignments_dir,
            Configuration.input_background,
            f"{Configuration.input_background}_align_filtered_macs3.bam"
        )
        cmd.extend(["-c", background_bam])

    run_cmd(cmd, check=True)