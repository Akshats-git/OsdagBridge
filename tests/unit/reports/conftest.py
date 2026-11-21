import os
import shutil
import subprocess

import pytest


def _find_pdflatex():
    exe = shutil.which("pdflatex")
    if exe:
        return exe
    try:
        from osdag_latex_env import OsdagLatexEnv  # type: ignore
        p = OsdagLatexEnv().pdflatex
        return str(p) if p else None
    except Exception:
        return None


@pytest.fixture(scope="session")
def pdflatex():
    exe = _find_pdflatex()
    if not exe:
        pytest.skip("pdflatex not available")
    return exe


@pytest.fixture
def compile_tex(pdflatex, tmp_path):
    """Compile a LaTeX body inside the real report preamble; return (rc, log, pdf_path)."""
    from osdagbridge.core.reports.preamble import build_preamble

    def _compile(body: str, passes: int = 2):
        tex = build_preamble("Test", "J-1", "2026-01-01") + body + "\n\\end{document}\n"
        (tmp_path / "t.tex").write_text(tex, encoding="utf-8")
        env = dict(os.environ)
        rc = 0
        for _ in range(passes):
            rc = subprocess.run([pdflatex, "-interaction=nonstopmode", "t.tex"], cwd=tmp_path,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).returncode
        log = (tmp_path / "t.log").read_text(encoding="utf-8", errors="ignore")
        return rc, log, tmp_path / "t.pdf"

    return _compile
