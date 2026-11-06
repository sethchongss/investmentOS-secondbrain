#!/usr/bin/env python3
"""Validate a markdown research vault. Standard library only.

Checks required metadata, local citation links, the relation vocabulary,
and references that do not point at a real record. It does not check
whether a claim is true, and it does not write to the vault.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schema" / "vault.schema.json"

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PLACEHOLDER = "REPLACE_ME"


class FrontmatterError(Exception):
    pass


@dataclass
class Issue:
    path: str
    message: str


@dataclass
class Doc:
    path: str
    data: dict
    body: str
    absolute: Path


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)
    scanned: int = 0


def parse_scalar(raw: str):
    raw = raw.strip()
    if raw in {"null", "~"}:
        return None
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        inner = raw[1:-1]
        if raw[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\n", "\n")
        return inner
    if raw == "true":
        return True
    if raw == "false":
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in split_csv(inner)]
    return raw


def split_csv(inner: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    quote = None
    for char in inner:
        if quote:
            buf.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            buf.append(char)
            continue
        if char == ",":
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(char)
    parts.append("".join(buf))
    return parts


def parse_frontmatter(text: str) -> tuple[dict, str]:
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise FrontmatterError("missing opening ---")
    lines = text.split("\n")
    data: dict = {}
    index = 1
    while index < len(lines):
        line = lines[index]
        if line.strip() == "---":
            body = "\n".join(lines[index + 1 :])
            if body.startswith("\n"):
                body = body[1:]
            return data, body
        if line.strip() == "" or line.lstrip().startswith("#"):
            index += 1
            continue
        if line[0] in {" ", "\t"}:
            raise FrontmatterError(f"line {index + 1}: unexpected indent")
        if ":" not in line:
            raise FrontmatterError(f"line {index + 1}: expected key: value")
        key, rest = line.split(":", 1)
        key = key.strip()
        if not key:
            raise FrontmatterError(f"line {index + 1}: empty key")
        if key in data:
            raise FrontmatterError(f"duplicate key '{key}'")
        rest_stripped = rest.strip()
        if rest_stripped in {"|", ">"}:
            raise FrontmatterError(
                f"line {index + 1}: keep '{key}' on one line; multiline scalars are not used"
            )
        if rest_stripped == "":
            items = []
            index += 1
            while index < len(lines) and re.match(r"^[ \t]+-\s+", lines[index]):
                item = re.sub(r"^[ \t]+-\s+", "", lines[index])
                items.append(parse_scalar(item))
                index += 1
            data[key] = items
            continue
        data[key] = parse_scalar(rest_stripped)
        index += 1
    raise FrontmatterError("missing closing ---")


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def enum_values(schema: dict, spec) -> list:
    if isinstance(spec, str):
        return schema[spec]
    return spec


def is_blank(value) -> bool:
    return value is None or value == ""


def contains_placeholder(value) -> bool:
    if isinstance(value, str):
        return PLACEHOLDER in value
    if isinstance(value, list):
        return any(contains_placeholder(item) for item in value)
    return False


def placement_matches(rel: str, placement: str) -> bool:
    if not rel.startswith(placement):
        return False
    if rel.count("/") != placement.count("/"):
        return False
    if placement == "library/" and "/relations/" in rel:
        return False
    return True


def parse_date(value) -> dt.date | None:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def inside(vault: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(vault.resolve())
    except ValueError:
        return False
    return True


def resolve_vault_path(vault: Path, raw) -> Path | None:
    if not isinstance(raw, str) or is_blank(raw):
        return None
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        return None
    target = (vault / path).resolve()
    if not inside(vault, target):
        return None
    return target


def local_link_target(file_path: Path, vault: Path, dest: str) -> str | None:
    """Return 'skip', 'escape', or a missing/ok marker.

    None means the link is fine. A string is an error message.
    """
    dest = dest.strip()
    if dest.startswith("<") and dest.endswith(">"):
        dest = dest[1:-1].strip()
    if not dest or dest.startswith("#"):
        return None
    lower = dest.lower()
    if lower.startswith(("synthetic:", "http:", "https:", "mailto:")):
        return None
    if " " in dest:
        dest = dest.split()[0]
    dest = dest.split("#", 1)[0]
    if not dest:
        return None
    target = (file_path.parent / dest).resolve()
    if not inside(vault, target):
        return f"local link escapes the vault: {dest}"
    if not target.is_file():
        return f"local link target not found: {dest}"
    return None


def check_links(vault: Path, doc: Doc) -> list[str]:
    messages = []
    for match in LINK_RE.finditer(doc.body):
        problem = local_link_target(doc.absolute, vault, match.group(1))
        if problem:
            messages.append(problem)
    return messages


def heading_present(body: str, heading: str) -> bool:
    return any(line.strip() == heading for line in body.splitlines())


def validate_vault(vault: Path, schema: dict, example: bool = False) -> Report:
    report = Report()
    vault = vault.resolve()
    known = ("raw", "library", "wiki", "output", "proposals", "changelog")
    if not any((vault / name).is_dir() for name in known):
        report.issues.append(
            Issue(
                "",
                "not a vault root (expected raw/, library/, or wiki/). "
                "Pass examples/low-oriole-metering or vault/.",
            )
        )
        return report

    docs: list[Doc] = []
    id_owner: dict[str, str] = {}
    markdown_files = sorted(path for path in vault.rglob("*.md") if path.is_file())

    for absolute in markdown_files:
        rel = absolute.relative_to(vault).as_posix()
        if rel == "README.md":
            if example and re.search(r"https?://", absolute.read_text(encoding="utf-8"), re.I):
                report.issues.append(Issue(rel, "example vault must not contain http:// or https://"))
            continue
        report.scanned += 1
        text = absolute.read_text(encoding="utf-8")
        if example and re.search(r"https?://", text, re.I):
            report.issues.append(Issue(rel, "example vault must not contain http:// or https://"))
        try:
            data, body = parse_frontmatter(text)
        except FrontmatterError as exc:
            report.issues.append(Issue(rel, f"frontmatter: {exc}"))
            continue
        doc = Doc(rel, data, body, absolute)
        docs.append(doc)
        doc_id = data.get("id")
        if isinstance(doc_id, str) and doc_id:
            if doc_id in id_owner:
                report.issues.append(
                    Issue(rel, f"duplicate id '{doc_id}' also used by {id_owner[doc_id]}")
                )
            else:
                id_owner[doc_id] = rel

    by_id = {doc.data.get("id"): doc for doc in docs if isinstance(doc.data.get("id"), str)}

    seen_source_link: dict[str, str] = {}
    seen_source_post: dict[str, str] = {}
    seen_library_link: dict[str, str] = {}
    seen_library_post: dict[str, str] = {}

    for doc in docs:
        spec = schema["types"].get(doc.data.get("type"))
        if spec is None:
            report.issues.append(
                Issue(doc.path, f"unknown or missing type '{doc.data.get('type')}'")
            )
            continue
        if not placement_matches(doc.path, spec["placement"]):
            report.issues.append(
                Issue(doc.path, f"type '{doc.data.get('type')}' belongs under {spec['placement']}")
            )
        check_fields(report, schema, spec, doc)
        check_dates(report, schema, doc)
        check_conviction(report, doc)
        for message in check_links(vault, doc):
            report.issues.append(Issue(doc.path, message))
        for match in WIKI_LINK_RE.finditer(doc.body):
            token = match.group(1).strip()
            if token not in by_id:
                report.issues.append(Issue(doc.path, f"dangling wiki link [[{token}]]"))
        if example and doc.data.get("synthetic") is not True:
            report.issues.append(Issue(doc.path, "example vault requires synthetic: true"))
        if example and doc.data.get("type") == "source" and not re.search(
            r"synthetic", doc.body, re.I
        ):
            report.issues.append(
                Issue(doc.path, "example source body must say that it is synthetic")
            )
        track_identity(report, doc, seen_source_link, seen_source_post, seen_library_link, seen_library_post)

    for doc in docs:
        if doc.data.get("type") not in schema["types"]:
            continue
        check_refs(report, vault, schema, doc, by_id)
        check_semantics(report, schema, doc, by_id, example)

    report.issues.sort(key=lambda issue: (issue.path, issue.message))
    return report


def check_fields(report: Report, schema: dict, spec: dict, doc: Doc) -> None:
    allowed = set(spec["required"]) | set(spec["optional"]) | set(spec["lists"]) | set(spec["refs"])
    for key, value in doc.data.items():
        if key not in allowed:
            report.issues.append(Issue(doc.path, f"unknown field '{key}' for type {doc.data.get('type')}"))
        elif contains_placeholder(value):
            report.issues.append(Issue(doc.path, f"placeholder {PLACEHOLDER} in '{key}'"))
    for key in spec["required"]:
        if key not in doc.data or is_blank(doc.data.get(key)):
            report.issues.append(Issue(doc.path, f"missing required field '{key}'"))
    for key, rule in spec["lists"].items():
        if key not in doc.data:
            continue
        value = doc.data[key]
        if not isinstance(value, list):
            report.issues.append(Issue(doc.path, f"'{key}' must be a list"))
            continue
        if len(value) < rule["min"]:
            report.issues.append(
                Issue(doc.path, f"'{key}' needs at least {rule['min']} item(s)")
            )
        for item in value:
            if isinstance(item, str) and PLACEHOLDER in item:
                continue
            if not isinstance(item, str) or is_blank(item):
                report.issues.append(Issue(doc.path, f"'{key}' contains an empty item"))
    for key, values_name in spec["enums"].items():
        if key not in doc.data or doc.data[key] in (None, ""):
            continue
        allowed_values = enum_values(schema, values_name)
        if doc.data[key] not in allowed_values:
            report.issues.append(
                Issue(
                    doc.path,
                    f"'{key}' must be one of: {', '.join(allowed_values)}",
                )
            )
    for key in spec.get("require_true", []):
        if doc.data.get(key) is not True:
            report.issues.append(Issue(doc.path, f"'{key}' must be true"))
    filename_field = spec.get("filename_date_field")
    if filename_field and isinstance(doc.data.get(filename_field), str):
        if not Path(doc.path).stem.startswith(doc.data[filename_field]):
            report.issues.append(
                Issue(
                    doc.path,
                    f"filename must start with {filename_field} {doc.data[filename_field]}",
                )
            )
    for heading in spec["body_headings"]:
        if not heading_present(doc.body, heading):
            report.issues.append(Issue(doc.path, f"missing heading '{heading}'"))
    doc_id = doc.data.get("id")
    if (
        isinstance(doc_id, str)
        and doc_id
        and PLACEHOLDER not in doc_id
        and not re.fullmatch(schema["id_pattern"], doc_id)
    ):
        report.issues.append(
            Issue(doc.path, f"id '{doc_id}' must match {schema['id_pattern']}")
        )
    if "synthetic" in spec["required"] and "synthetic" in doc.data and not isinstance(
        doc.data["synthetic"], bool
    ):
        report.issues.append(Issue(doc.path, "'synthetic' must be true or false"))


def check_dates(report: Report, schema: dict, doc: Doc) -> None:
    parsed = {}
    for key in schema["date_fields"]:
        if key not in doc.data or doc.data[key] in (None, ""):
            continue
        value = parse_date(doc.data[key])
        if value is None:
            report.issues.append(Issue(doc.path, f"'{key}' must be a real YYYY-MM-DD date"))
        else:
            parsed[key] = value
    if "date_posted" in parsed and "date_captured" in parsed:
        if parsed["date_captured"] < parsed["date_posted"]:
            report.issues.append(Issue(doc.path, "date_captured is earlier than date_posted"))
    if "covers_from" in parsed and "covers_to" in parsed:
        if parsed["covers_to"] < parsed["covers_from"]:
            report.issues.append(Issue(doc.path, "covers_to is earlier than covers_from"))
    if "date" in parsed and "review_date" in parsed:
        if parsed["review_date"] < parsed["date"]:
            report.issues.append(Issue(doc.path, "review_date is earlier than date"))


def check_conviction(report: Report, doc: Doc) -> None:
    if "conviction" not in doc.data:
        return
    value = doc.data["conviction"]
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
        report.issues.append(Issue(doc.path, "'conviction' must be an integer from 1 to 5"))


def track_identity(report, doc, seen_source_link, seen_source_post, seen_library_link, seen_library_post):
    kind = doc.data.get("type")
    link = doc.data.get("link")
    post_id = doc.data.get("post_id")
    if kind == "source":
        remember(report, doc, seen_source_link, "link", link)
        remember(report, doc, seen_source_post, "post_id", post_id)
    elif kind == "library":
        remember(report, doc, seen_library_link, "link", link)
        remember(report, doc, seen_library_post, "post_id", post_id)


def remember(report: Report, doc: Doc, seen: dict, label: str, value) -> None:
    if not isinstance(value, str) or is_blank(value):
        return
    if value in seen:
        report.issues.append(
            Issue(doc.path, f"duplicate {label} '{value}' also used by {seen[value]}")
        )
    else:
        seen[value] = doc.path


def check_refs(report: Report, vault: Path, schema: dict, doc: Doc, by_id: dict) -> None:
    spec = schema["types"][doc.data["type"]]
    for key, rule in spec["refs"].items():
        if key not in doc.data or is_blank(doc.data.get(key)):
            continue
        kind = rule["kind"]
        expect = rule.get("expect_type")
        if kind == "path":
            check_path_ref(report, vault, doc, key, doc.data[key], expect, by_id)
        elif kind == "id":
            check_id_ref(report, doc, key, doc.data[key], expect, by_id)
        elif kind == "id_list":
            value = doc.data[key]
            if not isinstance(value, list):
                continue
            for item in value:
                check_id_ref(report, doc, key, item, expect, by_id)


def check_path_ref(report, vault, doc, key, value, expect, by_id) -> None:
    if not isinstance(value, str):
        report.issues.append(Issue(doc.path, f"'{key}' must be a vault-relative path"))
        return
    target = resolve_vault_path(vault, value)
    if target is None:
        report.issues.append(Issue(doc.path, f"'{key}' escapes the vault or is not a relative path: {value}"))
        return
    if not target.is_file():
        report.issues.append(Issue(doc.path, f"dangling path in '{key}': {value}"))
        return
    if expect:
        try:
            data, _body = parse_frontmatter(target.read_text(encoding="utf-8"))
        except (OSError, FrontmatterError):
            report.issues.append(Issue(doc.path, f"'{key}' target did not parse: {value}"))
            return
        if data.get("type") != expect:
            report.issues.append(
                Issue(doc.path, f"'{key}' must point at type {expect}, not {data.get('type')}")
            )


def check_id_ref(report, doc, key, value, expect, by_id) -> None:
    if not isinstance(value, str) or is_blank(value):
        report.issues.append(Issue(doc.path, f"'{key}' contains an empty reference"))
        return
    target = by_id.get(value)
    if target is None:
        report.issues.append(Issue(doc.path, f"dangling reference '{value}' in '{key}'"))
        return
    if expect and target.data.get("type") != expect:
        report.issues.append(
            Issue(
                doc.path,
                f"'{key}' reference '{value}' is type {target.data.get('type')}, expected {expect}",
            )
        )


def wiki_prefix_ok(path: str, schema: dict) -> bool:
    return any(path.startswith(prefix) for prefix in schema["writeback_wiki_prefixes"])


def check_semantics(report, schema, doc, by_id, example: bool) -> None:
    data = doc.data
    kind = data.get("type")
    if kind in {"source", "library"} and example:
        link = data.get("link")
        post_id = data.get("post_id")
        if isinstance(link, str) and not link.startswith("synthetic://"):
            report.issues.append(Issue(doc.path, "example link must start with synthetic://"))
        if isinstance(post_id, str) and not post_id.startswith("syn-"):
            report.issues.append(Issue(doc.path, "example post_id must start with syn-"))
    if kind == "library":
        check_library_provenance(report, doc, by_id)
        status = data.get("claim_status")
        if status == "superseded" and is_blank(data.get("superseded_by")):
            report.issues.append(Issue(doc.path, "superseded record needs superseded_by"))
        if data.get("superseded_by") and status != "superseded":
            report.issues.append(Issue(doc.path, "superseded_by is set but claim_status is not superseded"))
        if status == "superseded" and isinstance(data.get("superseded_by"), str):
            newer = data["superseded_by"]
            if not any(
                other.data.get("type") == "relation"
                and other.data.get("relation") == "supersedes"
                and other.data.get("from") == newer
                and other.data.get("to") == data.get("id")
                for other in by_id.values()
            ):
                report.issues.append(
                    Issue(
                        doc.path,
                        f"no supersedes relation from {newer} to {data.get('id')}",
                    )
                )
        if status == "contested":
            if not any(
                other.data.get("type") == "relation"
                and other.data.get("relation") == "contradicts"
                and data.get("id") in {other.data.get("from"), other.data.get("to")}
                for other in by_id.values()
            ):
                report.issues.append(
                    Issue(doc.path, "contested record needs a contradicts relation")
                )
    if kind == "principle" and data.get("maturity") == "recurring":
        evidence = data.get("evidence_for")
        minimum = schema["recurring_principle_min_evidence_for"]
        if isinstance(evidence, list) and len(evidence) < minimum:
            report.issues.append(
                Issue(
                    doc.path,
                    f"recurring principle needs at least {minimum} evidence_for records "
                    "(developing principles and ordinary facts do not)",
                )
            )
    if kind == "writeback_proposal":
        check_writeback_target(report, schema, doc, "target")
        if data.get("status") == "approved":
            if is_blank(data.get("human_reviewer")):
                report.issues.append(Issue(doc.path, "approved proposal needs human_reviewer"))
            if is_blank(data.get("review_date")):
                report.issues.append(Issue(doc.path, "approved proposal needs review_date"))
    if kind == "changelog":
        check_writeback_target(report, schema, doc, "target")
        proposal = by_id.get(data.get("proposal"))
        if proposal and proposal.data.get("type") == "writeback_proposal":
            if proposal.data.get("status") != "approved":
                report.issues.append(Issue(doc.path, "changelog proposal is not approved"))
            if proposal.data.get("target") != data.get("target"):
                report.issues.append(Issue(doc.path, "changelog target does not match its proposal"))
            proposal_date = parse_date(proposal.data.get("date"))
            change_date = parse_date(data.get("date"))
            if proposal_date and change_date and change_date < proposal_date:
                report.issues.append(Issue(doc.path, "changelog date is earlier than the proposal"))
    if data.get("last_writeback"):
        change = by_id.get(data.get("last_writeback"))
        if change and change.data.get("type") == "changelog" and change.data.get("target") != doc.path:
            report.issues.append(
                Issue(doc.path, "last_writeback changelog targets a different file")
            )


def check_library_provenance(report, doc, by_id) -> None:
    stub_path = doc.data.get("source_stub")
    if not isinstance(stub_path, str):
        return
    stub = next((item for item in by_id.values() if item.path == stub_path), None)
    if stub is None or stub.data.get("type") != "source":
        return
    if doc.data.get("link") != stub.data.get("link") or doc.data.get("post_id") != stub.data.get("post_id"):
        report.issues.append(
            Issue(doc.path, "link and post_id must match the source stub (one capture, one record)")
        )


def check_writeback_target(report, schema, doc, key) -> None:
    target = doc.data.get(key)
    if not isinstance(target, str) or is_blank(target):
        return
    if not wiki_prefix_ok(target, schema):
        report.issues.append(
            Issue(
                doc.path,
                f"'{key}' must be an in-place wiki page (not raw sources, library records, "
                f"journal, output, proposals, or changelog): {target}",
            )
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a markdown research vault.")
    parser.add_argument("vault", type=Path, help="Vault root, for example examples/low-oriole-metering")
    parser.add_argument(
        "--example",
        action="store_true",
        help="Require synthetic labels and reject http(s) links. Use on the shipped example.",
    )
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    if not args.schema.is_file():
        print(f"schema not found: {args.schema}", file=sys.stderr)
        return 2
    if not args.vault.exists():
        print(f"vault not found: {args.vault}", file=sys.stderr)
        return 2
    schema = load_schema(args.schema)
    report = validate_vault(args.vault, schema, example=args.example)
    prefix = args.vault.as_posix().rstrip("/")
    for issue in report.issues:
        loc = f"{prefix}/{issue.path}" if issue.path else prefix
        print(f"{loc}: {issue.message}")
    if report.issues:
        print(f"{len(report.issues)} error(s)")
        return 1
    print(f"ok: {report.scanned} markdown file(s), 0 errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
