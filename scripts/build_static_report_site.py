#!/usr/bin/env python3
from __future__ import annotations

import base64
import mimetypes
import re
import shutil
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
REPORT_DIR = BASE / "reports" / "leaf_node"
SITE_DIR = BASE / "docs" / "final-report"


def inline_images(html: str, source_dir: Path) -> str:
    def repl(match: re.Match[str]) -> str:
        prefix, src, suffix = match.group(1), match.group(2), match.group(3)
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        path = source_dir / src
        if not path.exists():
            return match.group(0)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'{prefix}data:{mime};base64,{encoded}{suffix}'

    return re.sub(r'(<img\s+[^>]*src=")([^"]+)(")', repl, html)


def main() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    html_path = REPORT_DIR / "index.html"
    if not html_path.exists():
        raise FileNotFoundError(html_path)

    standalone = inline_images(html_path.read_text(encoding="utf-8"), REPORT_DIR)
    (REPORT_DIR / "ssg_final_report_standalone.html").write_text(standalone, encoding="utf-8")
    (SITE_DIR / "index.html").write_text(standalone, encoding="utf-8")

    for name in ["final_report.md", "executive_summary.md", "method_appendix.md"]:
        shutil.copy2(REPORT_DIR / name, SITE_DIR / name)

    table_src = BASE / "outputs" / "tables" / "final_candidate_board.csv"
    if table_src.exists():
        shutil.copy2(table_src, SITE_DIR / "final_candidate_board.csv")

    zip_path = REPORT_DIR / "ssg_final_report_site_bundle"
    shutil.make_archive(str(zip_path), "zip", SITE_DIR)
    print(SITE_DIR / "index.html")
    print(REPORT_DIR / "ssg_final_report_standalone.html")
    print(str(zip_path) + ".zip")


if __name__ == "__main__":
    main()
