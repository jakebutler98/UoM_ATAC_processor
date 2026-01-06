import logging
import sys
import os
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


class Config:
    """
    Configuration container.

    - Provides safe, repo-friendly defaults (relative paths under ./data by default)
    - Allows overriding via YAML config file
    """

    def __init__(self, config_path: Optional[str] = None):
        # -------- safe defaults (repo-friendly) --------
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))

        # Paths (default to ./data/* so repo can run anywhere)
        self.RAW_input_dir = os.path.join(repo_root, "data", "raw")
        self.Trimmed_dir = os.path.join(repo_root, "data", "temp_trimming")
        self.aligned_dir = os.path.join(repo_root, "data", "output", "temp_align")
        self.Reads_quality_dir = os.path.join(repo_root, "data", "output", "fastqc")
        self.dedup_alignments_dir = os.path.join(repo_root, "data", "output", "temp_align_dedup")
        self.cleaned_alignments_dir = os.path.join(repo_root, "data", "output", "clean_alignments")
        self.macs3_dir = os.path.join(repo_root, "data", "output", "macs3")
        self.genrich_dir = os.path.join(repo_root, "data", "output", "genrich")
        self.coverages_dir = os.path.join(repo_root, "data", "output", "coverages")
        self.other_qc_dir = os.path.join(repo_root, "data", "output", "qc")
        self.fastqc_untrimmed_dir = os.path.join(repo_root, "data", "output", "qc", "fastqc_untrimmed")
        self.fastqc_trimmed_dir = os.path.join(repo_root, "data", "output", "qc", "fastqc_trimmed")
        self.logs_dir = os.path.join(repo_root, "data", "logs")

        # References (left None by default; must be provided by config for real runs)
        self.bowtie2_index = None
        self.genome_fasta = None
        self.picard = None

        # Options
        self.force = False
        self.threads = 8
        self.blacklist_bed = None
        self.atacseqqc_dir = None

        # Runtime
        self.file_to_process = None
        self.analysis_type = None
        self.input_background = None

        # Apply YAML overrides
        if config_path:
            self._load_yaml(config_path)

        self._init_logging()

    def _load_yaml(self, config_path: str) -> None:
        if yaml is None:
            raise ImportError(
                "PyYAML is required for --config. Install with: conda install pyyaml (or add to env)."
            )

        # Resolve user-provided path robustly
        config_path = os.path.expanduser(config_path)
        if not os.path.isabs(config_path):
            config_path = os.path.abspath(os.path.join(os.getcwd(), config_path))

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f) or {}

        # Allow YAML-relative paths (relative to YAML location)
        base_dir = os.path.dirname(config_path)

        def _resolve(v):
            if isinstance(v, str):
                v = os.path.expanduser(v)
                if v.startswith("./") or v.startswith("../"):
                    return os.path.abspath(os.path.join(base_dir, v))
            return v

        # paths
        for k, v in (cfg.get("paths", {}) or {}).items():
            setattr(self, k, _resolve(v))

        # references
        for k, v in (cfg.get("references", {}) or {}).items():
            setattr(self, k, _resolve(v))

        # options
        opts = cfg.get("options", {}) or {}
        if "threads" in opts and opts["threads"] is not None:
            self.threads = int(opts["threads"])
        if "blacklist_bed" in opts:
            self.blacklist_bed = _resolve(opts["blacklist_bed"])
        if "atacseqqc_dir" in opts:
            self.atacseqqc_dir = _resolve(opts["atacseqqc_dir"])

    def _init_logging(self):
        handler = logging.StreamHandler()
        handler.flush = sys.stdout.flush

        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s - %(message)s",
            handlers=[handler],
            force=True
        )