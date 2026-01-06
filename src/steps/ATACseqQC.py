import os
import logging
import subprocess
from steps.helpers import outputs_exist, clean_dir

def run_ATACseqQC(Configuration):
    """
    Run ATACseqQC-based QC via an R script.

    Uses filtered+dedup BAM:
      {Configuration.cleaned_alignments_dir}/{sample}/{sample}_align_dedup_filtered.bam

    Outputs go to:
      {Configuration.other_qc_dir}/{sample}/ATACseqQC/
    """
    sample = Configuration.file_to_process

    bam_file = os.path.join(
        Configuration.cleaned_alignments_dir,
        sample,
        f"{sample}_align_dedup_filtered.bam"
    )
    if not os.path.exists(bam_file):
        raise FileNotFoundError(f"ATACseqQC input BAM not found: {bam_file}")

    base_qc_dir = getattr(Configuration, "atacseqqc_dir", None)
    if base_qc_dir is None:
        out_dir = os.path.join(Configuration.other_qc_dir, sample, "ATACseqQC")
    else:
        out_dir = os.path.join(base_qc_dir, sample)

    os.makedirs(out_dir, exist_ok=True)

    # Expected outputs from the cleaned R script
    expected = [
        os.path.join(out_dir, f"{sample}_Frag_sizes.png"),
        os.path.join(out_dir, f"{sample}_shifted.bam"),
        os.path.join(out_dir, f"{sample}_shifted.bam.bai"),
        os.path.join(out_dir, f"{sample}_TSSE_enrichment_plot.png"),
        os.path.join(out_dir, f"{sample}_TSSEscore.txt"),
    ]
    if (not Configuration.force) and outputs_exist(expected):
        logging.info("ATACseqQC: outputs exist; skipping (use --force to overwrite)")
        return

    if Configuration.force:
        clean_dir(out_dir)

    r_script = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/processing_pipeline/scripts/ATACseqQC_for_pipeline_clean.R"
    conda_activate = "/mnt/jw01-aruk-home01/projects/functional_genomics/common_files/bin/tools/miniforge/24.3.0-0/bin/activate"
    conda_env = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/env"

    cmd = f"""
    set -euo pipefail
    source "{conda_activate}" "{conda_env}"
    Rscript --vanilla "{r_script}" "{bam_file}" "{sample}" "{out_dir}"
    """

    logging.info(f"ATACseqQC: running for sample={sample}")
    subprocess.run(["bash", "-c", cmd], check=True)
    logging.info("ATACseqQC: finished")