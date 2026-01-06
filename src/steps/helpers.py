import os
import shutil
import logging
import subprocess
from typing import List, Union, Optional

def clean_dir(dir_path: str) -> None:
    """
    Delete contents of a directory (not the directory itself).
    Use carefully; intended for pipeline-managed output dirs.
    """
    if not dir_path or dir_path in ["/", "."]:
        raise ValueError(f"Refusing to clean unsafe directory: {dir_path}")

    if not os.path.exists(dir_path):
        return

    for root, dirs, files in os.walk(dir_path):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

def outputs_exist(paths: List[str]) -> bool:
    """True if all paths exist and are non-empty files (or existing dirs)."""
    for p in paths:
        if not os.path.exists(p):
            return False
        if os.path.isfile(p) and os.path.getsize(p) == 0:
            return False
    return True

def run_cmd(
    cmd: Union[List[str], str],
    *,
    shell: bool = False,
    check: bool = True,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    printable = " ".join(cmd) if isinstance(cmd, list) else cmd
    logging.info(f"CMD: {printable}")

    if shell:
        return subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            check=check,
            cwd=cwd,
            env=env,
        )

    return subprocess.run(cmd, shell=False, check=check, cwd=cwd, env=env)

def run_pipe(
    cmd1: List[str],
    cmd2: List[str],
    *,
    check: bool = True,
) -> None:
    """
    Run cmd1 | cmd2, and fail if either side fails.
    Ensures cmd1 stdout is closed on the parent side to avoid deadlocks.
    """
    logging.info(f"PIPE: {' '.join(cmd1)} | {' '.join(cmd2)}")
    p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout)
    if p1.stdout is not None:
        p1.stdout.close()

    p2_rc = p2.wait()
    p1_rc = p1.wait()

    if check and (p1_rc != 0 or p2_rc != 0):
        raise RuntimeError(f"Pipe failed: cmd1_rc={p1_rc}, cmd2_rc={p2_rc}")