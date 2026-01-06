import os
import logging
from steps.helpers import outputs_exist, clean_dir, run_cmd

def run_multiqc(Configuration):
    """
    Run MultiQC across relevant output directories.

    Output:
      {Configuration.other_qc_dir}/multiqc/multiqc_report.html
    """
    out_dir = os.path.join(Configuration.other_qc_dir, "multiqc")
    os.makedirs(out_dir, exist_ok=True)

    report_html = os.path.join(out_dir, "multiqc_report.html")
    if (not Configuration.force) and outputs_exist([report_html]):
        logging.info("multiqc: report exists; skipping (use --force to overwrite)")
        return

    if Configuration.force:
        clean_dir(out_dir)

    # Scan these directories (tweak as needed)
    scan_dirs = [
        Configuration.Reads_quality_dir,      # fastp html/json
        Configuration.fastqc_untrimmed_dir,   # fastqc
        Configuration.fastqc_trimmed_dir,     # fastqc
        Configuration.other_qc_dir,           # picard metrics, qc tables
        Configuration.macs3_dir,              # peaks logs (if any)
    ]

    # MultiQC can take multiple input dirs
    cmd = ["multiqc", "-o", out_dir]
    if Configuration.force:
        cmd.append("-f")
    cmd += scan_dirs
    run_cmd(cmd, check=True)