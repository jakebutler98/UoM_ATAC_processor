########################################
# script for running bowtie2
########################################

import os
import glob
import logging
from steps.helpers import clean_dir, outputs_exist, run_cmd, run_pipe

def _require_single_glob(pattern: str, label: str) -> str:
    matches = sorted(glob.glob(pattern))
    if len(matches) == 0:
        raise FileNotFoundError(f"[{label}] No files matched pattern: {pattern}")
    if len(matches) > 1:
        raise RuntimeError(f"[{label}] Expected 1 file, found {len(matches)}: {matches}")
    return matches[0]

def align_bowtie(Configuration):
    """
    Align trimmed FASTQs with bowtie2 -> sort BAM.
    Skips if output exists (unless Configuration.force).
    """
    sample = Configuration.file_to_process
    logging.info("starting bowtie2 mapping")

    trimmed_dir = os.path.join(Configuration.Trimmed_dir, sample)
    R1_file = _require_single_glob(os.path.join(trimmed_dir, "*trimmed_R1.fastq.gz"), "Trimmed R1")
    R2_file = _require_single_glob(os.path.join(trimmed_dir, "*trimmed_R2.fastq.gz"), "Trimmed R2")

    align_output_dir = os.path.join(Configuration.aligned_dir, sample)
    os.makedirs(align_output_dir, exist_ok=True)

    bam_out = os.path.join(align_output_dir, f"{sample}_align.bam")
    bai_out = bam_out + ".bai"

    if (not Configuration.force) and outputs_exist([bam_out, bai_out]):
        logging.info("align_bowtie: outputs exist; skipping (use --force to overwrite)")
        return

    if Configuration.force:
        clean_dir(align_output_dir)

    threads = str(getattr(Configuration, "threads", 6))

    run_pipe(
        ["bowtie2", "--very-sensitive", "-k", "1", "-X", "2000",
         "-x", Configuration.bowtie2_index,
         "-1", R1_file, "-2", R2_file,
         "-p", threads],
        ["samtools", "sort", "-@", threads, "-o", bam_out, "-"]
    )

    run_cmd(["samtools", "index", bam_out], check=True)

def dedup_QC_alignments(Configuration):
    """
    Runs Picard MarkDuplicates (REMOVE_DUPLICATES=true) and alignment QC.
    Skips if outputs exist (unless Configuration.force).
    """
    import os
    import logging
    from steps.helpers import clean_dir, outputs_exist, run_cmd

    sample = Configuration.file_to_process

    align_output_dir = os.path.join(Configuration.aligned_dir, sample)
    alignment_file = os.path.join(align_output_dir, f"{sample}_align.bam")
    if not os.path.exists(alignment_file):
        raise FileNotFoundError(f"Aligned BAM not found: {alignment_file}")

    dedup_dir = os.path.join(Configuration.dedup_alignments_dir, sample)
    os.makedirs(dedup_dir, exist_ok=True)
    dedup_bam = os.path.join(dedup_dir, f"{sample}_align_dedup.bam")
    dedup_bai = dedup_bam + ".bai"

    qc_dir = os.path.join(Configuration.other_qc_dir, sample)
    os.makedirs(qc_dir, exist_ok=True)

    markdup_metrics = os.path.join(qc_dir, f"{sample}_markdup_qc.txt")
    align_metrics = os.path.join(qc_dir, f"{sample}_alignment_metrics_qc.txt")
    idxstats_out = os.path.join(qc_dir, f"{sample}_idxstats.txt")
    fraglen_out = os.path.join(qc_dir, f"{sample}_fragment_length_count.txt")

    expected = [dedup_bam, dedup_bai, markdup_metrics, align_metrics, idxstats_out, fraglen_out]
    if (not Configuration.force) and outputs_exist(expected):
        logging.info("dedup_QC_alignments: outputs exist; skipping (use --force to overwrite)")
        return

    if Configuration.force:
        clean_dir(dedup_dir)
        clean_dir(qc_dir)

    # Picard threads: keep conservative
    picard_gc_threads = str(min(4, int(getattr(Configuration, "threads", 8))))

    logging.info("running Picard MarkDuplicates")
    run_cmd(
        f"java -XX:ParallelGCThreads={picard_gc_threads} -Xmx8G -jar {Configuration.picard} "
        f"MarkDuplicates QUIET=true REMOVE_DUPLICATES=true CREATE_INDEX=true "
        f"I={alignment_file} O={dedup_bam} M={markdup_metrics}",
        shell=True,
        check=True
    )

    logging.info("running Picard CollectAlignmentSummaryMetrics")
    run_cmd(
        f"java -XX:ParallelGCThreads={picard_gc_threads} -Xmx8G -jar {Configuration.picard} "
        f"CollectAlignmentSummaryMetrics R={Configuration.genome_fasta} I={dedup_bam} O={align_metrics}",
        shell=True,
        check=True
    )

    logging.info("running samtools idxstats")
    run_cmd(f"samtools idxstats {dedup_bam} > {idxstats_out}", shell=True, check=True)

    logging.info("computing fragment length counts")
    run_cmd(
        f"samtools view {dedup_bam} | awk '$9>0' | cut -f 9 | sort | uniq -c | "
        f"sort -b -k2,2n | sed -e 's/^[ \\t]*//' > {fraglen_out}",
        shell=True,
        check=True
    )

def filter_alignments(Configuration):
    """
    Create filtered BAM suitable for downstream ATAC (and peak calling).

    Filters:
      - remove chrM
      - MAPQ >= 30
      - proper pairs (-f 2)
      - exclude flags 1804
      - OPTIONAL: remove ENCODE blacklist regions (Configuration.blacklist_bed)
    """
    import os
    import logging
    from steps.helpers import clean_dir, outputs_exist, run_cmd

    sample = Configuration.file_to_process
    logging.info("creating filtered bam file")

    dedup_dir = os.path.join(Configuration.dedup_alignments_dir, sample)
    dedup_bam = os.path.join(dedup_dir, f"{sample}_align_dedup.bam")
    if not os.path.exists(dedup_bam):
        raise FileNotFoundError(f"Dedup BAM not found: {dedup_bam}")

    out_dir = os.path.join(Configuration.cleaned_alignments_dir, sample)
    os.makedirs(out_dir, exist_ok=True)

    filtered_bam = os.path.join(out_dir, f"{sample}_align_dedup_filtered.bam")
    filtered_bai = filtered_bam + ".bai"

    if (not Configuration.force) and outputs_exist([filtered_bam, filtered_bai]):
        logging.info("filter_alignments: outputs exist; skipping (use --force to overwrite)")
        return

    if Configuration.force:
        clean_dir(out_dir)

    # Base filtering command (chrM removal + mapq + flags)
    base_cmd = (
        f"samtools view -h {dedup_bam} | "
        f"grep -v chrM | "
        f"samtools view -h -q 30 - | "
        f"samtools view -h -b -F 1804 -f 2"
    )

    # Optional blacklist removal (BED or BED.GZ)
    bl = getattr(Configuration, "blacklist_bed", None)
    threads = str(getattr(Configuration, "threads", 8))

    if bl:
        logging.info(f"Applying blacklist filter: {bl}")
        if bl.endswith(".gz"):
            cmd = (
                base_cmd + " | "
                f"bedtools intersect -v -abam - -b <(zcat '{bl}') | "
                f"samtools sort -@ {threads} -O bam -o '{filtered_bam}'"
            )
            run_cmd(cmd, shell=True, check=True, env=None)  # needs bash for process substitution
        else:
            cmd = (
                base_cmd + " | "
                f"bedtools intersect -v -abam - -b '{bl}' | "
                f"samtools sort -@ {threads} -O bam -o '{filtered_bam}'"
            )
            run_cmd(cmd, shell=True, check=True)
    else:
        cmd = base_cmd + f" | samtools sort -@ {threads} -O bam -o '{filtered_bam}'"
        run_cmd(cmd, shell=True, check=True)

    logging.info("indexing filtered bam")
    run_cmd(["samtools", "index", filtered_bam], check=True)