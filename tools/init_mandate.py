#!/usr/bin/env python3
"""Offline mandate initializer and profile validator. Standard library only.

The agent interview lives in prompts/onboard.md. This script copies a blank
mandate if one is missing, checks a saved profile, prints the workflow map,
and writes wiki starters only when the destination file is absent.

It does not ask questions, call a model, or connect to a service.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mandate

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize or check an investment mandate profile.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Copy the blank mandate into a vault if it is absent.")
    init.add_argument("--dest", type=Path, default=ROOT / "vault" / "profile")

    validate = sub.add_parser("validate", help="Check one profile directory.")
    validate.add_argument("profile", type=Path)
    validate.add_argument("--example", action="store_true")

    sub.add_parser(
        "validate-all",
        help="Check every fictional profile under examples/profiles with example rules.",
    )

    map_cmd = sub.add_parser("map", help="Print the workflow map for a profile. Does not write.")
    map_cmd.add_argument("profile", type=Path)

    scaffold = sub.add_parser("scaffold", help="Write missing wiki starters. Never overwrites.")
    scaffold.add_argument("profile", type=Path)
    scaffold.add_argument("--dest", type=Path, default=ROOT / "vault")

    check = sub.add_parser("check-new", help="Exit 1 if the path already exists.")
    check.add_argument("path", type=Path)

    args = parser.parse_args(argv)
    if args.command == "init":
        return _init(args.dest)
    if args.command == "validate":
        return _validate(args.profile, args.example)
    if args.command == "validate-all":
        profiles = mandate.example_profiles(ROOT)
        if not profiles:
            print("no example profiles found", file=sys.stderr)
            return 2
        failed = 0
        for profile in profiles:
            print(profile.relative_to(ROOT).as_posix())
            failed = max(failed, _validate(profile, True))
        return failed
    if args.command == "map":
        result = mandate.select_workflows(args.profile)
        sys.stdout.write(mandate.format_map(result))
        return 0
    if args.command == "scaffold":
        for line in mandate.scaffold_profile(args.profile, args.dest):
            print(line)
        return 0
    if args.command == "check-new":
        ok, message = mandate.check_new(args.path)
        print(message)
        return 0 if ok else 1
    parser.error(f"unknown command {args.command}")
    return 2


def _init(dest: Path) -> int:
    source = ROOT / "templates" / "mandate" / "mandate.md"
    if not source.is_file():
        print(f"template not found: {source}", file=sys.stderr)
        return 2
    for action, path in mandate.init_profile(dest, ROOT):
        print(f"{action} {path}")
    return 0


def _validate(profile: Path, example: bool) -> int:
    if not profile.exists():
        print(f"profile not found: {profile}", file=sys.stderr)
        return 2
    schema = mandate.load_schema()
    report = mandate.validate_profile(profile, schema, example=example)
    prefix = profile.as_posix().rstrip("/")
    for issue in report.issues:
        loc = f"{prefix}/{issue.path}" if issue.path else prefix
        print(f"{loc}: {issue.message}")
    if report.issues:
        print(f"{len(report.issues)} error(s)")
        return 1
    print(f"ok: {profile.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
