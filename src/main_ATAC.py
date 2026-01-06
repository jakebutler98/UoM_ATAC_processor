########################################
# main script that calls all functions

# naming system:
# within the folder name needs to be id+lane_R1.fastq.gz and R2

# protocols needs to be either CHIP or ATAC

# designed to work specifically for our library preperation methods
# only usable with paired end reads

########################################

from configuration import Config
import os
import glob
import argparse
import logging
from steps import fastqc, trimming, align, coverage, genrich, macs3, qc, ATACseqQC, multiqc


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Wrapper function for all steps of ATAC-seq analysis')

    parser.add_argument("-i",'--input', dest='infile', action='store', required=False,
                        help='input folder to force. Will overwrite all ouputs')
    parser.add_argument("-s",'--steps', dest='step', action='append', required=False,
                        help='chose steps instead of running everything')
    parser.add_argument("--force", action="store_true", help="Overwrite outputs if they already exist")
    parser.add_argument("--config", default=None, help="Path to YAML config file")
    parser.add_argument("--threads", type=int, default=None, help="Override threads in config")

    # parse arguments
    args = parser.parse_args()

    # set up configuration object for all steps
    Configuration = Config(config_path=args.config)
    Configuration.force = bool(args.force)
    Configuration.analysis_type = "ATAC"

    # CLI threads overrides config
    if args.threads is not None:
        Configuration.threads = int(args.threads)

    if args.infile == None:
        all_raws_present = [os.path.basename(x) for x in glob.glob(Configuration.RAW_input_dir + "/*ATAC")]

        all_processed = [os.path.basename(x) for x in glob.glob(Configuration.cleaned_alignments_dir + "/*ATAC")]
        # chose the first one of the ones that are still not processed and run 
        for i in all_raws_present:
            if i not in all_processed:
                os.makedirs(os.path.join(Configuration.cleaned_alignments_dir,i),exist_ok=True)
                Configuration.file_to_process = i
                break

        if Configuration.file_to_process == None:
            logging.error("There were no new files to process")
            raise Exception
        
    else:
        Configuration.file_to_process = args.infile
        os.makedirs(os.path.join(Configuration.cleaned_alignments_dir,Configuration.file_to_process),exist_ok=True)
    
    logging.info(f"This script will run the file : {Configuration.file_to_process}")

    if args.step == None:
            

        # call trimming
        trimming.run_fastp(Configuration)

        # run bowtie2 alignment
        align.align_bowtie(Configuration)

        # run QC and dedup
        align.dedup_QC_alignments(Configuration)
	
        # run filter on alignment
        align.filter_alignments(Configuration)
	
        # run coverage
        coverage.coverage(Configuration)
        
        # run genrich
        genrich.create_bam_for_genrich(Configuration)
        genrich.run_genrich_ATAC(Configuration)

        # run macs3
        macs3.run_macs3_ATAC(Configuration)

        # qc
        qc.run_qc(Configuration)
        
        # ATACseqQC
        ATACseqQC.run_ATACseqQC(Configuration)

        # multiqc
        multiqc.run_multiqc(Configuration)

    else:
        if "fastqc_before_trimming" in args.step:
            fastqc.qc_before_trimming(Configuration)
        if "trimming" in args.step:
            trimming.run_fastp(Configuration)
        if "fastqc_after_trimming" in args.step:
            fastqc.qc_after_trimming(Configuration)
        if "align" in args.step:
            align.align_bowtie(Configuration)
        if "align_qc" in args.step:
            align.dedup_QC_alignments(Configuration)
        if "filter" in args.step:
            align.filter_alignments(Configuration)
        if "coverage" in args.step:
            coverage.coverage(Configuration)
        if "genrich" in args.step:
            genrich.create_bam_for_genrich(Configuration)
            genrich.run_genrich_ATAC(Configuration)
        if "macs3" in args.step:
            macs3.run_macs3_ATAC(Configuration)
        if "qc" in args.step:
            qc.run_qc(Configuration)
        if "ATACseqQC" in args.step:
            ATACseqQC.run_ATACseqQC(Configuration)
        if "multiqc" in args.step:
            multiqc.run_multiqc(Configuration)
