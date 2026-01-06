args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("Usage: Rscript ATACseqQC_for_pipeline_clean.R <bam> <sample_name> <outdir>")
}

bamfilename <- args[1]
sample_name <- args[2]
outPath <- args[3]

message("BAM: ", bamfilename)
message("Sample: ", sample_name)
message("Outdir: ", outPath)

if (!dir.exists(outPath)) {
  dir.create(outPath, recursive = TRUE, showWarnings = FALSE)
}

suppressPackageStartupMessages({
  library(ATACseqQC)
  library(Rsamtools)
  library(GenomicAlignments)
  library(TxDb.Hsapiens.UCSC.hg38.knownGene)
})

# ---- Fragment size distribution
frag_png <- file.path(outPath, paste0(sample_name, "_Frag_sizes.png"))
png(frag_png)
tryCatch({
  fragSizeDist(bamfilename, sample_name)
}, error=function(e) {
  dev.off()
  stop("fragSizeDist failed: ", e$message)
})
dev.off()

# ---- Prepare tags
possibleTag <- c(
  "AM","AS","CM","CP","FI","H0","H1","H2","HI","IH","MQ","NH","NM","OP","PQ","SM","TC","UQ",
  "BC","BQ","BZ","CB","CC","CO","CQ","CR","CS","CT","CY","E2","FS","LB","MC","MD","MI","OA",
  "OC","OQ","OX","PG","PT","PU","Q2","QT","QX","R2","RG","RX","SA","TS","U2"
)

bamTop <- scanBam(BamFile(bamfilename, yieldSize = 200),
                  param = ScanBamParam(tag = possibleTag))[[1]]$tag
tags <- names(bamTop)[lengths(bamTop) > 0]
message("Detected tags: ", paste(tags, collapse = ","))

# ---- Read and shift alignments (whole genome; can be slow, but correct)
txs <- transcripts(TxDb.Hsapiens.UCSC.hg38.knownGene)

gal <- readBamFile(bamfilename, tag = tags, asMates = TRUE, bigFile = TRUE)

shiftedBamfile <- file.path(outPath, paste0(sample_name, "_shifted.bam"))
Gal1 <- shiftGAlignmentsList(gal, outbam = shiftedBamfile)

# index shifted bam
indexBam(shiftedBamfile)

# ---- TSSE
tsse <- TSSEscore(Gal1, txs)

tsse_txt <- file.path(outPath, paste0(sample_name, "_TSSEscore.txt"))
writeLines(as.character(tsse$TSSEscore), con = tsse_txt)

tsse_png <- file.path(outPath, paste0(sample_name, "_TSSE_enrichment_plot.png"))
png(tsse_png)
plot(100 * (-9:10 - .5), tsse$values, type = "b",
     xlab = "distance to TSS", ylab = "aggregate TSS score",
     main = paste0(sample_name, " TSSE"))
dev.off()

message("Done.")