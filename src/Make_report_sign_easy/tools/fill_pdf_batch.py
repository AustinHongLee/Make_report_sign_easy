from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ is None:
    here = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    src_root = os.path.join(repo_root, "src")
    if os.path.isdir(src_root):
        sys.path.insert(0, src_root)
    sys.path.insert(0, repo_root)

from Make_report_sign_easy.services import (  # noqa: E402
    BatchFillItem,
    BatchFillRequest,
    BatchFillService,
)


def _console_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def _resolve_relative(path_text: str, base: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return base / path


def _load_jobs(jobs_path: Path, output_dir: Path | None) -> tuple[BatchFillItem, ...]:
    with jobs_path.open("r", encoding="utf-8") as f:
        jobs = json.load(f)
    if not isinstance(jobs, list):
        raise ValueError("jobs JSON must be a list")

    job_base = jobs_path.parent
    output_base = output_dir or job_base
    items = []
    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            raise ValueError(f"job #{index} must be an object")
        if "output" not in job:
            raise ValueError(f"job #{index} missing required output")

        values = job.get("values")
        values_path_text = job.get("values_path")
        if (values is None) == (values_path_text is None):
            raise ValueError(
                f"job #{index} must provide exactly one of values or values_path"
            )
        if values is not None and not isinstance(values, dict):
            raise ValueError(f"job #{index} values must be an object")

        values_path = None
        if values_path_text is not None:
            values_path = _resolve_relative(str(values_path_text), job_base)

        output_path = _resolve_relative(str(job["output"]), output_base)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        items.append(
            BatchFillItem(
                output_path=output_path,
                values_path=values_path,
                values=values,
                seed=_optional_int(job.get("seed")),
                label=_optional_str(job.get("label")),
            )
        )

    return tuple(items)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch fill one PDF template with multiple value sets."
    )
    parser.add_argument("--template", required=True, help="Path to the PDF template")
    parser.add_argument("--jobs", required=True, help="Path to batch jobs JSON")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Base directory for relative job output paths",
    )
    parser.add_argument(
        "--clear-annots",
        action="store_true",
        help="Remove annotations after insertion",
    )
    parser.add_argument(
        "--random",
        action="store_true",
        help="Enable random jitter for each character",
    )
    parser.add_argument(
        "--seed-start",
        type=int,
        default=None,
        help="Base seed for jobs that do not specify an item seed",
    )
    args = parser.parse_args()

    jobs_path = Path(args.jobs)
    output_dir = Path(args.output_dir) if args.output_dir else None
    items = _load_jobs(jobs_path, output_dir)

    result = BatchFillService().run(
        BatchFillRequest(
            template_path=Path(args.template),
            items=items,
            clear_annots=args.clear_annots,
            random=args.random,
            seed_start=args.seed_start,
        )
    )

    print(f"Saved {len(result.results)} PDFs:")
    for output_path in result.output_paths:
        print(f"- {_console_text(output_path)}")


if __name__ == "__main__":
    main()
