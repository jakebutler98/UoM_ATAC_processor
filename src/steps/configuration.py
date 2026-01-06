########################################
# utility that contains a class that gets the configuration



########################################

import logging
import datetime

class Config:
    """
    Class containing the parameters 
    """
    
    def __init__(self):

        self.RAW_input_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/raw"
        self.Trimmed_dir = "/mnt/iusers01/jw01/x25633jb/scratch/FLS_MLS/temp_trimming"
        self.aligned_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/temp_align"
        self.Reads_quality_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/fastqc"
        self.dedup_alignments_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/temp_align_dedup"
        self.cleaned_alignments_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/clean_alignments"
        self.macs2_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/macs2"
        self.genrich_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/genrich"
        self.coverages_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/coverages"
        self.other_qc_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/qc"
        self.fastqc_untrimmed_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/qc/fastqc_untrimmed"
        self.fastqc_trimmed_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/FLS_MLS/data/output/qc/fastqc_trimmed"


        self.bowtie2_index = "/mnt/jw01-aruk-home01/projects/shared_resources/sequencing/data/Homo_sapiens/UCSC/hg38/Sequence/Bowtie2Index/genome"
        self.genome_fasta = "/mnt/jw01-aruk-home01/projects/shared_resources/sequencing/data/Homo_sapiens/UCSC/hg38/Sequence/hg38/fasta/genome.fa"
        self.picard = "/mnt/jw01-aruk-home01/projects/functional_genomics/bin/picard/picard.jar"
        self.logs_dir = "/mnt/jw01-aruk-home01/projects/oa_functional_genomics/projects/ATAC_seq/analyses/processing_pipeline/data/output/logs"

        self._init_logging()

        self.file_to_process = None
        self.analysis_type = None
        self.input_background = None
        
    def _init_logging(self):
        cur_date = datetime.datetime.now()
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s - %(message)s",
            handlers=[
                # logging.FileHandler("{0}/{1}.log".format(self.logs_dir, f"{cur_date.year}-{cur_date.month}-{cur_date.day}_{cur_date.hour}.{cur_date.minute}.{cur_date.second}"), mode="a"),
                logging.StreamHandler()]) 
