import os
import logging
from steps.helpers import clean_dir, outputs_exist, run_cmd

def coverage(Configuration):
    logging.info("starting bamcoverage")

    sample = Configuration.file_to_process
    filtered_align_file = os.path.join(Configuration.cleaned_alignments_dir, sample, f"{sample}_align_dedup_filtered.bam")

    coverage_output_dir = os.path.join(Configuration.coverages_dir, sample)
    os.makedirs(coverage_output_dir, exist_ok=True)

    coverage_output_file = os.path.join(coverage_output_dir, f"{sample}_coverage.bw")

    if (not Configuration.force) and outputs_exist([coverage_output_file]):
        logging.info("coverage: output exists; skipping (use Configuration.force=True to overwrite)")
        return

    if Configuration.force:
        clean_dir(coverage_output_dir)

    threads = str(getattr(Configuration, "threads", 4))

    run_cmd(
        f"bamCoverage -p {threads} -b {filtered_align_file} -of bigwig -o {coverage_output_file} "
        f"--samFlagInclude 2 --samFlagExclude 1804 --minMappingQuality 30",
        shell=True,
        check=True,
    )