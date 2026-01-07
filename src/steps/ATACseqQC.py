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

    r_script = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/master_pipeline/scripts/ATACseqQC_for_pipeline.r"
    conda_activate = "/mnt/jw01-aruk-home01/projects/functional_genomics/common_files/bin/tools/miniforge/24.3.0-0/bin/activate"
    conda_env = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/env"
    project_root = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq"

    if not os.path.exists(r_script):
        raise FileNotFoundError(f"ATACseqQC R script not found: {r_script}")
    if not os.path.exists(conda_activate):
        raise FileNotFoundError(f"Conda activate script not found: {conda_activate}")
    if not os.path.exists(conda_env):
        raise FileNotFoundError(f"Conda env not found: {conda_env}")

    # Quote arguments safely for bash
    r_script_q = shlex.quote(r_script)
    bam_q = shlex.quote(bam_file)
    sample_q = shlex.quote(sample)
    outdir_q = shlex.quote(out_dir)
    conda_activate_q = shlex.quote(conda_activate)
    conda_env_q = shlex.quote(conda_env)

    cmd = f"""
    set -eo pipefail
    set +u
    source {conda_activate_q} {conda_env_q}
    set -u

    cd {shlex.quote(project_root)}

    export ATAC_R_SCRIPT={r_script_q}

    Rscript --vanilla -e 'source("renv/activate.R"); source(Sys.getenv("ATAC_R_SCRIPT"))' {bam_q} {sample_q} {outdir_q}
    """

    logging.info(f"ATACseqQC: running for sample={sample}")
    logging.info(f"ATACseqQC: BAM={bam_file}")
    logging.info(f"ATACseqQC: OUTDIR={out_dir}")
    subprocess.run(["bash", "-c", cmd], check=True)
    logging.info("ATACseqQC: finished")