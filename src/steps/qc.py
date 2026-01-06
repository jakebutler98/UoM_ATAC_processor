import os
import glob
import logging
import subprocess
import pandas as pd
import pybedtools as pbed
import matplotlib.pyplot as plt

os.makedirs("/mnt/iusers01/jw01/x25633jb/scratch/temp_pybedtools/", exist_ok=True)
pbed.helpers.set_tempdir("/mnt/iusers01/jw01/x25633jb/scratch/temp_pybedtools/")
bed_genome_file = "/mnt/jw01-aruk-home01/projects/functional_genomics/common_files/data/external/reference/Homo_sapiens/hg38/Sequence/WholeGenomeFasta/genome.genome"

def _samtools_count(bam_path: str) -> int:
    out = subprocess.check_output(["samtools", "view", "-c", bam_path])
    return int(out.decode().strip())

def _parse_picard_markdup(metrics_path: str):
    """
    Very lightweight Picard MarkDuplicates parser.
    Returns dict with keys like PERCENT_DUPLICATION if present.
    """
    if not os.path.exists(metrics_path):
        return {}

    with open(metrics_path) as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    # Find the header line that contains "PERCENT_DUPLICATION"
    header_idx = None
    for i, l in enumerate(lines):
        if "PERCENT_DUPLICATION" in l and "UNPAIRED_READS_EXAMINED" in l:
            header_idx = i
            break
    if header_idx is None or header_idx + 1 >= len(lines):
        return {}

    header = lines[header_idx].split("\t")
    values = lines[header_idx + 1].split("\t")
    d = dict(zip(header, values))
    return d

def _read_idxstats(idxstats_path: str):
    """
    samtools idxstats columns:
    rname, length, mapped, unmapped
    """
    if not os.path.exists(idxstats_path):
        return None
    df = pd.read_csv(idxstats_path, sep="\t", header=None, names=["rname", "length", "mapped", "unmapped"])
    return df

def run_qc(Configuration):
    sample = Configuration.file_to_process

    # Paths
    filtered_bam = os.path.join(Configuration.cleaned_alignments_dir, sample, f"{sample}_align_dedup_filtered.bam")
    peaks_narrow = os.path.join(Configuration.macs3_dir, sample, f"{sample}_peaks.narrowPeak")

    qc_dir = os.path.join(Configuration.other_qc_dir, sample)
    os.makedirs(qc_dir, exist_ok=True)

    idxstats_path = os.path.join(qc_dir, f"{sample}_idxstats.txt")
    markdup_path = os.path.join(qc_dir, f"{sample}_markdup_qc.txt")

    if not os.path.exists(filtered_bam):
        raise FileNotFoundError(f"Filtered BAM not found: {filtered_bam}")
    if not os.path.exists(peaks_narrow):
        raise FileNotFoundError(f"MACS3 peaks not found: {peaks_narrow}")

    # TSS for FRiP(TSS)
    tss_sites = "/mnt/jw01-aruk-home01/projects/psa_functional_genomics/NEW_references/genes/gencode.v29.TSS_sites_protein_coding_sorted.bed"
    tss_bed = pbed.BedTool(tss_sites).slop(b=2000, g=bed_genome_file)

    def wccount(filename):
        out = subprocess.check_output(["wc", "-l", filename])
        return int(out.split()[0])

    def calculate_frip(tss_bed, peak_bed, bam_file):
        bam_bed = pbed.BedTool(bam_file)
        reads_in_tss = wccount(bam_bed.intersect(tss_bed, bed=True, u=True).fn)
        reads_in_peaks = wccount(bam_bed.intersect(peak_bed, bed=True, u=True).fn)
        total_reads = _samtools_count(bam_bed.fn)
        return reads_in_tss / total_reads, reads_in_peaks / total_reads, total_reads

    frip_tss, frip_peaks, total_reads = calculate_frip(
        tss_bed,
        pbed.BedTool(peaks_narrow),
        filtered_bam
    )

    # Mito fraction from idxstats (produced in dedup_QC_alignments)
    mito_fraction = None
    idx_df = _read_idxstats(idxstats_path)
    if idx_df is not None:
        total_mapped = idx_df["mapped"].sum()
        mito_mapped = idx_df.loc[idx_df["rname"].isin(["chrM", "MT", "M"]), "mapped"].sum()
        if total_mapped > 0:
            mito_fraction = mito_mapped / total_mapped

    # Duplicate rate from Picard metrics (if present)
    md = _parse_picard_markdup(markdup_path)
    dup_rate = None
    if "PERCENT_DUPLICATION" in md:
        try:
            dup_rate = float(md["PERCENT_DUPLICATION"])
        except Exception:
            dup_rate = None

    # Write per-sample metrics
    metrics = {
        "sample": sample,
        "total_reads_filtered_bam": total_reads,
        "frip_tss_2kb": frip_tss,
        "frip_peaks_macs3": frip_peaks,
        "mito_fraction_mapped": mito_fraction,
        "picard_percent_duplication": dup_rate,
    }

    out_path = os.path.join(qc_dir, f"{sample}_qc_metrics.tsv")
    pd.DataFrame([metrics]).to_csv(out_path, sep="\t", index=False)
    logging.info(f"Wrote QC metrics: {out_path}")

    # Update combined metrics table across all samples (scan qc dirs)
    sample_dirs = [os.path.basename(x) for x in glob.glob(os.path.join(Configuration.other_qc_dir, "*"))]
    rows = []
    for s in sample_dirs:
        p = os.path.join(Configuration.other_qc_dir, s, f"{s}_qc_metrics.tsv")
        if os.path.exists(p):
            rows.append(pd.read_csv(p, sep="\t"))
    if rows:
        combined = pd.concat(rows, ignore_index=True)
        combined_out = os.path.join(Configuration.other_qc_dir, "qc_metrics_all_samples.tsv")
        combined.to_csv(combined_out, sep="\t", index=False)
        logging.info(f"Updated combined QC metrics: {combined_out}")

    # Fragment length plot across all samples (as you had)
    raw_samples = [os.path.basename(x) for x in glob.glob(os.path.join(Configuration.RAW_input_dir, "*"))]
    plt.figure()
    for s in raw_samples:
        frag_file = os.path.join(Configuration.other_qc_dir, s, f"{s}_fragment_length_count.txt")
        if not os.path.exists(frag_file):
            continue
        data = pd.read_csv(frag_file, sep=" ", header=None)
        plt.plot(data[1].to_numpy(), (data[0] / sum(data[0])).to_numpy(), label=s)

    plt.xlim(1, 1000)
    plt.ylim(1e-5, 1e-1)
    plt.yscale("log")
    plt.legend()
    plt.savefig(os.path.join(Configuration.other_qc_dir, "fraglength_fig.png"))
    plt.close()