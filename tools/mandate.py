#!/usr/bin/env python3
"""Investment-mandate profile: validate, map, and refuse overwrites.

The interview is a prompt a person pastes into an agent they already use.
This module does not ask questions, call a model, or write a confirmed
mandate over a file that already exists. It checks the markdown the person
saved and names which workflow prompts fit those answers.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import validate_vault as vaultlib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schema" / "mandate.schema.json"
MANDATE_NAME = "mandate.md"
OPEN_VALUES = {"unknown", "skipped"}
SHORT_HOLDS = {"days", "months"}
LONG_HOLDS = {"three_to_seven_years", "seven_years_plus"}


@dataclass
class ProfileReport:
    issues: list[vaultlib.Issue] = field(default_factory=list)
    mandate: dict | None = None
    strategies: list[dict] = field(default_factory=list)


def load_schema(path: Path | None = None) -> dict:
    return vaultlib.load_schema(path or DEFAULT_SCHEMA)


def check_new(path: Path) -> tuple[bool, str]:
    """True when the path is absent and safe to create."""
    if path.exists():
        return False, f"refusing to overwrite {path.as_posix()}"
    return True, f"absent {path.as_posix()}"


def init_profile(dest: Path, root: Path | None = None) -> list[tuple[str, str]]:
    """Copy the blank mandate into a vault if that file is not already there.

    Existing files are left byte for byte. Strategy files are not invented.
    """
    root = root or ROOT
    actions: list[tuple[str, str]] = []
    dest = dest.resolve()
    (dest / "strategies").mkdir(parents=True, exist_ok=True)
    (dest / "revisions").mkdir(parents=True, exist_ok=True)
    target = dest / MANDATE_NAME
    source = root / "templates" / "mandate" / "mandate.md"
    if target.exists():
        actions.append(("skipped", target.as_posix()))
        return actions
    shutil.copyfile(source, target)
    actions.append(("copied", target.as_posix()))
    return actions


def validate_profile(profile: Path, schema: dict | None = None, example: bool = False) -> ProfileReport:
    schema = schema or load_schema()
    report = ProfileReport()
    profile = profile.resolve()
    mandate_path = profile / MANDATE_NAME
    if not mandate_path.is_file():
        report.issues.append(vaultlib.Issue("", "missing mandate.md"))
        return report

    mandate_doc = _read_doc(report, profile, mandate_path)
    if mandate_doc is None:
        return report
    data, body = mandate_doc
    report.mandate = data
    _check_forbidden(report, profile, mandate_path, data, schema)
    _check_mandate_fields(report, schema, profile, mandate_path, data, body, example)

    strategies: list[dict] = []
    named = data.get("strategies") if isinstance(data.get("strategies"), list) else []
    seen_ids = {data.get("id"): MANDATE_NAME}
    for strategy_id in named:
        if not isinstance(strategy_id, str) or vaultlib.is_blank(strategy_id):
            continue
        rel = f"strategies/{strategy_id}.md"
        path = profile / rel
        if not path.is_file():
            report.issues.append(vaultlib.Issue(MANDATE_NAME, f"missing strategy file {rel}"))
            continue
        loaded = _read_doc(report, profile, path)
        if loaded is None:
            continue
        sdata, sbody = loaded
        strategies.append(sdata)
        _check_forbidden(report, profile, path, sdata, schema)
        _check_strategy(report, schema, data, path, sdata, sbody, example)
        _remember_id(report, seen_ids, sdata.get("id"), rel)

    if isinstance(named, list):
        expected = {item for item in named if isinstance(item, str)}
        folder = profile / "strategies"
        if folder.is_dir():
            for path in sorted(folder.glob("*.md")):
                if path.stem not in expected:
                    report.issues.append(
                        vaultlib.Issue(
                            f"strategies/{path.name}",
                            "strategy file is not named by the mandate",
                        )
                    )

    revisions = profile / "revisions"
    if revisions.is_dir():
        for path in sorted(revisions.glob("*.md")):
            loaded = _read_doc(report, profile, path)
            if loaded is None:
                continue
            rdata, rbody = loaded
            _check_forbidden(report, profile, path, rdata, schema)
            _check_revision(report, schema, path, rdata, rbody, example)
            _remember_id(report, seen_ids, rdata.get("id"), f"revisions/{path.name}")

    if data.get("status") == "confirmed":
        _check_confirmed_links(report, schema, profile, data, body, strategies)

    report.strategies = strategies
    report.issues.sort(key=lambda issue: (issue.path, issue.message))
    return report


def select_workflows(profile: Path, schema: dict | None = None) -> dict:
    """Choose workflow prompts from a saved profile.

    A missing, draft, unknown, or invalid profile returns generic mode.
    Generic mode does not invent an institution or a checklist.
    """
    schema = schema or load_schema()
    profile = Path(profile)
    if not (profile / MANDATE_NAME).is_file():
        return _generic(
            "No mandate file. Use prompts/onboard.md, or stay in generic mode. "
            "Do not invent a mandate."
        )
    report = validate_profile(profile, schema, example=False)
    if report.issues or report.mandate is None:
        return _generic(
            "Profile has validation errors. Fix them or stay in generic mode. "
            "Do not invent a mandate."
        )
    data = report.mandate
    reason = _tailoring_block(data, report.strategies)
    if reason:
        return _generic(reason)

    emphasis = schema["emphasis"]
    catalog = schema["workflows"]
    order = schema["workflow_order"]
    explicit = _explicit_outputs(data)
    produced: list[dict] = []
    contradictions: list[str] = []
    notes: list[str] = []

    for strategy in report.strategies:
        kind = strategy.get("strategy_kind")
        voice = emphasis.get(kind) or emphasis["other"]
        for workflow_id in order:
            spec = catalog[workflow_id]
            if not spec.get("per_strategy"):
                continue
            kinds = spec.get("kinds")
            if kinds and kind not in kinds:
                continue
            if explicit is not None and workflow_id not in explicit:
                continue
            produced.append(_item(workflow_id, spec, strategy, voice, data, ""))

    authority = data.get("decision_authority")
    include_ic = (explicit is None and authority in {"vote", "decide"}) or (
        explicit is not None and "ic_memo" in explicit
    )
    if include_ic:
        note = (
            "The confirmed authority allows this memo to be prepared. "
            "A person still approves any wiki change."
        )
        if authority == "recommend_only":
            note = (
                "Authority is recommend_only. This memo must say it does not decide. "
                "Do not rewrite the mandate to say decide."
            )
            contradictions.append(
                "output_formats includes ic_memo, but decision_authority is recommend_only. "
                "The memo must say it does not decide. The mandate was not changed to decide."
            )
        elif authority in OPEN_VALUES or not authority:
            note = (
                "Decision authority is unknown or skipped. "
                "The memo must not assume this seat decides."
            )
            contradictions.append(
                "ic_memo was requested but decision_authority is not a stated seat. "
                "The memo was not treated as a decision."
            )
        produced.append(_item("ic_memo", catalog["ic_memo"], None, None, data, note))

    if not any(item["id"] == "decision_journal" for item in produced):
        produced.append(
            _item("decision_journal", catalog["decision_journal"], None, None, data, "")
        )
    if explicit is not None and "decision_journal" not in explicit:
        notes.append(
            "decision-journal stays on the map because a decision is not left only in chat. "
            "The mandate was not changed."
        )

    if explicit:
        produced_ids = {item["id"] for item in produced}
        for name in sorted(explicit):
            if name in produced_ids or name == "decision_journal":
                continue
            contradictions.append(
                f"output_formats includes {name}, but no confirmed subprofile qualifies. "
                "It was not added and the mandate was not changed."
            )

    produced.sort(key=lambda item: (order.index(item["id"]), item.get("strategy_id") or ""))
    return {
        "mode": "confirmed",
        "reason": None,
        "contradictions": contradictions,
        "notes": notes,
        "workflows": produced,
    }


def constraint_conflicts(mandate: dict, request: dict) -> list[str]:
    """Name conflicts between a saved constraint and a requested action.

    The mandate dict is not modified.
    """
    conflicts = []
    leverage = mandate.get("leverage")
    asked = request.get("leverage")
    if leverage == "none" and asked in {"permitted", "used", "limited"}:
        conflicts.append(
            "Request uses leverage, but the mandate says leverage is none. "
            "Keep the mandate. Do not proceed as if the constraint moved."
        )
    if leverage == "limited" and asked in {"permitted", "used"}:
        conflicts.append(
            "Request uses more leverage than the mandate, which says leverage is limited. "
            "Show the conflict. Do not rewrite the mandate."
        )
    hold = mandate.get("holding_period")
    asked_hold = request.get("holding_period")
    if hold in LONG_HOLDS and asked_hold in SHORT_HOLDS:
        conflicts.append(
            f"Request holding period is {asked_hold}. The mandate says {hold}. "
            "Show both. Do not overwrite the mandate."
        )
    if mandate.get("decision_authority") == "recommend_only" and request.get("decides") is True:
        conflicts.append(
            "Request treats this seat as the decision. The mandate says recommend_only. "
            "The note can recommend. It must say it does not decide."
        )
    concentration = mandate.get("concentration")
    if (
        request.get("concentration") == "above_stated"
        and isinstance(concentration, str)
        and concentration not in OPEN_VALUES
        and concentration != ""
    ):
        conflicts.append(
            f"Request exceeds the stated concentration constraint ({concentration}). "
            "Keep the constraint and show the conflict."
        )
    return conflicts


def scaffold_profile(profile: Path, vault: Path, schema: dict | None = None, root: Path | None = None) -> list[str]:
    """Write missing wiki starters for a confirmed map. Never replace a file."""
    schema = schema or load_schema()
    root = root or ROOT
    chosen = select_workflows(profile, schema)
    lines: list[str] = []
    if chosen["mode"] != "confirmed":
        lines.append(f"mode: generic")
        lines.append(chosen["reason"] or "generic mode")
        lines.append("No wiki starter written.")
        return lines
    vault = vault.resolve()
    for item in chosen["workflows"]:
        destination = vault / item["starter_output"]
        ok, message = check_new(destination)
        if not ok:
            lines.append(message)
            continue
        template = root / item["starter_template"]
        text = template.read_text(encoding="utf-8")
        rendered = _fill(text, item)
        if "{{" in rendered:
            lines.append(f"unfilled token in {item['starter_template']}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
        lines.append(f"copied {destination.as_posix()}")
    for note in chosen["contradictions"]:
        lines.append(f"contradiction: {note}")
    for note in chosen["notes"]:
        lines.append(f"note: {note}")
    return lines


def format_map(result: dict) -> str:
    lines = [f"mode: {result['mode']}"]
    if result.get("reason"):
        lines.append(f"reason: {result['reason']}")
    for item in result.get("workflows", []):
        label = item["id"]
        if item.get("strategy_id"):
            label += f" {item['strategy_id']} ({item.get('strategy_kind')})"
        lines.append(f"workflow: {label}")
        lines.append(f"  prompt: {item['prompt']}")
        lines.append(f"  starter: {item['starter_output']}")
        if item.get("asks"):
            lines.append(f"  asks: {item['asks']}")
        if item.get("does_not_ask"):
            lines.append(f"  does_not_ask: {item['does_not_ask']}")
    for note in result.get("contradictions", []):
        lines.append(f"contradiction: {note}")
    for note in result.get("notes", []):
        lines.append(f"note: {note}")
    return "\n".join(lines) + "\n"


def example_profiles(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    base = root / "examples" / "profiles"
    found = []
    if not base.is_dir():
        return found
    for path in sorted(base.iterdir()):
        if path.is_dir() and (path / MANDATE_NAME).is_file():
            found.append(path)
    return found


def _generic(reason: str) -> dict:
    return {
        "mode": "generic",
        "reason": reason,
        "contradictions": [],
        "notes": [],
        "workflows": [],
    }


def _tailoring_block(data: dict, strategies: list[dict]) -> str | None:
    if data.get("status") != "confirmed":
        return (
            "Mandate is not confirmed. Use prompts/onboard.md, or stay in generic mode. "
            "Do not invent a mandate."
        )
    institutions = data.get("institution_types") or []
    if not any(item not in OPEN_VALUES for item in institutions):
        return (
            "Institution type is unknown or skipped. Generic mode. "
            "Do not guess SFO, MFO, VC, PE, or a hedge fund."
        )
    if data.get("activity") in OPEN_VALUES:
        return (
            "Activity is unknown or skipped. Direct and fund-selection workflows differ, "
            "so nothing tailored was selected."
        )
    if not strategies:
        return "Confirmed mandate has no strategy subprofile. Generic mode until one is confirmed."
    return None


def _explicit_outputs(data: dict) -> set[str] | None:
    formats = data.get("output_formats")
    if not isinstance(formats, list) or not formats:
        return None
    if any(item in OPEN_VALUES for item in formats):
        return None
    return {item for item in formats if isinstance(item, str)}


def _item(workflow_id: str, spec: dict, strategy: dict | None, voice: dict | None, mandate: dict, authority_note: str) -> dict:
    kind = strategy.get("strategy_kind") if strategy else None
    strategy_id = strategy.get("id") if strategy else None
    slug = workflow_id.replace("_", "-")
    if spec.get("per_strategy"):
        output = f"wiki/playbooks/wf-{slug}-{strategy_id}.md"
    else:
        output = f"wiki/playbooks/wf-{slug}.md"
    voice = voice or {}
    strategy_ids = mandate.get("strategies") if isinstance(mandate.get("strategies"), list) else []
    return {
        "id": workflow_id,
        "strategy_id": strategy_id,
        "strategy_kind": kind,
        "prompt": spec["prompt"],
        "starter_template": spec["starter"],
        "starter_output": output,
        "asks": voice.get("asks", ""),
        "does_not_ask": voice.get("does_not_ask", ""),
        "monitor": voice.get("monitor", ""),
        "counterthesis": voice.get("counterthesis", ""),
        "decision_authority": str(mandate.get("decision_authority") or ""),
        "authority_note": authority_note,
        "strategy_list": ", ".join(str(item) for item in strategy_ids),
    }


def _fill(text: str, item: dict) -> str:
    values = {
        "strategy_id": item.get("strategy_id") or "mandate",
        "strategy_kind": item.get("strategy_kind") or "mandate",
        "asks": item.get("asks") or "see the confirmed mandate",
        "does_not_ask": item.get("does_not_ask") or "do not borrow another strategy's checklist",
        "monitor": item.get("monitor") or "only what a source states",
        "counterthesis": item.get("counterthesis") or "a mechanism the thesis does not already use",
        "decision_authority": item.get("decision_authority") or "unknown",
        "authority_note": item.get("authority_note") or "A person still approves any wiki change.",
        "strategy_list": item.get("strategy_list") or "none",
        "workflow_id": item["id"],
    }
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _read_doc(report: ProfileReport, profile: Path, path: Path):
    rel = path.relative_to(profile).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        report.issues.append(vaultlib.Issue(rel, f"could not read file: {exc}"))
        return None
    try:
        data, body = vaultlib.parse_frontmatter(text)
    except vaultlib.FrontmatterError as exc:
        report.issues.append(vaultlib.Issue(rel, f"frontmatter: {exc}"))
        return None
    return data, body


def _check_forbidden(report: ProfileReport, profile: Path, path: Path, data: dict, schema: dict) -> None:
    banned = {item.casefold() for item in schema["forbidden_keys"]}
    rel = path.relative_to(profile).as_posix()
    for key in data:
        if str(key).casefold() in banned:
            report.issues.append(
                vaultlib.Issue(
                    rel,
                    f"do not store '{key}' on a profile (no firm name, client, AUM, holdings, or credentials)",
                )
            )


def _check_mandate_fields(report, schema, profile, path, data, body, example: bool) -> None:
    rel = MANDATE_NAME
    allowed = set(schema["mandate_required"]) | set(schema["mandate_optional"])
    for key, value in data.items():
        if key not in allowed:
            report.issues.append(vaultlib.Issue(rel, f"unknown field '{key}'"))
        if vaultlib.contains_placeholder(value):
            report.issues.append(vaultlib.Issue(rel, f"placeholder REPLACE_ME in '{key}'"))
    for key in schema["mandate_required"]:
        if key not in data or vaultlib.is_blank(data.get(key)):
            report.issues.append(vaultlib.Issue(rel, f"missing required field '{key}'"))
    if data.get("type") != "mandate":
        report.issues.append(vaultlib.Issue(rel, "type must be mandate"))
    if data.get("operating_context") is not True:
        report.issues.append(vaultlib.Issue(rel, "operating_context must be true"))
    if type(data.get("synthetic")) is not bool:
        report.issues.append(vaultlib.Issue(rel, "'synthetic' must be true or false"))
    _check_id(report, schema, rel, data.get("id"))
    revision = data.get("revision")
    if type(revision) is not int or revision < 1:
        report.issues.append(vaultlib.Issue(rel, "'revision' must be an integer of 1 or more"))
    for key, enum_name in schema["mandate_enums"].items():
        if key not in data or data.get(key) in (None, ""):
            continue
        values = schema["enums"][enum_name]
        if data[key] not in values:
            report.issues.append(
                vaultlib.Issue(rel, f"'{key}' must be one of: {', '.join(values)}")
            )
    for key, enum_name in schema["mandate_lists"].items():
        if key not in data:
            continue
        value = data[key]
        if not isinstance(value, list) or not value:
            report.issues.append(vaultlib.Issue(rel, f"'{key}' must be a non-empty list"))
            continue
        for item in value:
            if not isinstance(item, str) or vaultlib.is_blank(item):
                report.issues.append(vaultlib.Issue(rel, f"'{key}' contains an empty item"))
                continue
            if enum_name and item not in schema["enums"][enum_name]:
                report.issues.append(
                    vaultlib.Issue(rel, f"'{key}' item '{item}' is not an allowed value")
                )
            if enum_name is None:
                _check_id(report, schema, rel, item)
    confirmed_by = data.get("confirmed_by")
    if isinstance(confirmed_by, str) and "@" in confirmed_by:
        report.issues.append(vaultlib.Issue(rel, "confirmed_by is a role, not an email address"))
    _check_return_objective(report, rel, data, body)
    _check_client_rule(report, rel, data)
    if data.get("evidence_rule") not in schema["enums"]["evidence_rule"] and "evidence_rule" in data:
        pass
    if example:
        _check_example(report, rel, data, body, path)
    status = data.get("status")
    confirmed_on = data.get("confirmed_on")
    if status == "confirmed":
        if vaultlib.parse_date(confirmed_on) is None:
            report.issues.append(vaultlib.Issue(rel, "confirmed mandate needs confirmed_on as YYYY-MM-DD"))
        if not isinstance(data.get("strategies"), list) or not data.get("strategies"):
            report.issues.append(vaultlib.Issue(rel, "confirmed mandate needs at least one strategy id"))
        sentence = schema["required_sentence"]
        if sentence not in body:
            report.issues.append(vaultlib.Issue(rel, f"confirmed mandate must say: {sentence}"))
    elif status == "draft" and confirmed_on not in OPEN_VALUES and vaultlib.parse_date(confirmed_on) is None:
        if "confirmed_on" in data and not vaultlib.contains_placeholder(confirmed_on):
            report.issues.append(
                vaultlib.Issue(rel, "draft confirmed_on must be a date, unknown, or skipped")
            )


def _check_return_objective(report, rel, data, body) -> None:
    objective = data.get("return_objective")
    words = data.get("return_objective_words")
    if objective == "user_stated":
        if not isinstance(words, str) or vaultlib.is_blank(words):
            report.issues.append(
                vaultlib.Issue(rel, "user_stated return objective needs return_objective_words")
            )
        elif words not in body or "## User-stated objective" not in body:
            report.issues.append(
                vaultlib.Issue(
                    rel,
                    "user-stated return words must appear under ## User-stated objective",
                )
            )
    elif objective in {"not_stated", "skipped"} and words not in (None, ""):
        report.issues.append(
            vaultlib.Issue(rel, "return_objective_words set but return_objective is not user_stated")
        )


def _check_client_rule(report, rel, data) -> None:
    institutions = data.get("institution_types")
    if not isinstance(institutions, list):
        return
    separation = data.get("client_separation")
    if (
        data.get("status") == "confirmed"
        and "mfo" in institutions
        and separation != "separate_files"
    ):
        report.issues.append(
            vaultlib.Issue(
                rel,
                "MFO profiles keep clients in separate files and this starter does not store "
                "a shared client list. Set client_separation to separate_files.",
            )
        )
    if "mfo" not in institutions and data.get("status") == "confirmed" and separation == "unknown":
        report.issues.append(
            vaultlib.Issue(
                rel,
                "state client_separation. Use not_applicable when the institution is not an MFO.",
            )
        )


def _check_strategy(report, schema, mandate, path, data, body, example: bool) -> None:
    rel = f"strategies/{path.name}"
    if data.get("type") != "strategy":
        report.issues.append(vaultlib.Issue(rel, "type must be strategy"))
    kind = data.get("strategy_kind")
    fields = schema["strategy_fields"].get(kind)
    if fields is None:
        report.issues.append(vaultlib.Issue(rel, f"strategy_kind '{kind}' is not an allowed value"))
        fields = {}
    allowed = set(schema["strategy_common"]) | set(fields)
    for key, value in data.items():
        if key not in allowed:
            report.issues.append(vaultlib.Issue(rel, f"unknown field '{key}'"))
        if vaultlib.contains_placeholder(value):
            report.issues.append(vaultlib.Issue(rel, f"placeholder REPLACE_ME in '{key}'"))
    for key in schema["strategy_common"]:
        if key not in data or vaultlib.is_blank(data.get(key)):
            report.issues.append(vaultlib.Issue(rel, f"missing required field '{key}'"))
    for key, rule in fields.items():
        if key not in data or vaultlib.is_blank(data.get(key)):
            report.issues.append(vaultlib.Issue(rel, f"missing required field '{key}'"))
            continue
        value = data[key]
        if rule == "text":
            if not isinstance(value, str):
                report.issues.append(vaultlib.Issue(rel, f"'{key}' must be text"))
        elif value not in schema["enums"][rule]:
            report.issues.append(
                vaultlib.Issue(rel, f"'{key}' must be one of: {', '.join(schema['enums'][rule])}")
            )
    if data.get("mandate") != mandate.get("id"):
        report.issues.append(vaultlib.Issue(rel, "strategy mandate id does not match mandate.md"))
    if data.get("id") != path.stem:
        report.issues.append(vaultlib.Issue(rel, "strategy id must match its filename"))
    _check_id(report, schema, rel, data.get("id"))
    if type(data.get("synthetic")) is not bool:
        report.issues.append(vaultlib.Issue(rel, "'synthetic' must be true or false"))
    if example:
        _check_example(report, rel, data, body, path)


def _check_revision(report, schema, path, data, body, example: bool) -> None:
    rel = f"revisions/{path.name}"
    required = ["id", "type", "title", "date", "revision", "mandate", "synthetic"]
    for key in required:
        if key not in data or vaultlib.is_blank(data.get(key)):
            report.issues.append(vaultlib.Issue(rel, f"missing required field '{key}'"))
    if data.get("type") != "mandate_revision":
        report.issues.append(vaultlib.Issue(rel, "type must be mandate_revision"))
    if vaultlib.parse_date(data.get("date")) is None:
        report.issues.append(vaultlib.Issue(rel, "'date' must be a real YYYY-MM-DD date"))
    elif not path.stem.startswith(str(data.get("date"))):
        report.issues.append(vaultlib.Issue(rel, "revision filename must start with its date"))
    if type(data.get("revision")) is not int:
        report.issues.append(vaultlib.Issue(rel, "'revision' must be an integer"))
    for heading in ("## Before", "## After"):
        if heading not in body:
            report.issues.append(vaultlib.Issue(rel, f"missing heading '{heading}'"))
    before, after = _section(body, "Before"), _section(body, "After")
    if before and after and before.strip() == after.strip():
        report.issues.append(vaultlib.Issue(rel, "Before and After are the same text"))
    if example:
        _check_example(report, rel, data, body, path)


def _check_confirmed_links(report, schema, profile, data, body, strategies: list[dict]) -> None:
    rel = MANDATE_NAME
    revision = data.get("revision")
    prior = data.get("prior_revision")
    if revision == 1:
        if prior not in (None, ""):
            report.issues.append(vaultlib.Issue(rel, "revision 1 must not set prior_revision"))
    elif type(revision) is int and revision > 1:
        if not isinstance(prior, str) or vaultlib.is_blank(prior):
            report.issues.append(vaultlib.Issue(rel, "revision above 1 needs prior_revision"))
        else:
            target = _safe_join(profile, prior)
            if target is None or not target.is_file():
                report.issues.append(vaultlib.Issue(rel, f"prior_revision does not resolve: {prior}"))
            else:
                loaded = _read_doc(report, profile, target)
                if loaded is not None:
                    rdata, _rbody = loaded
                    if rdata.get("revision") != revision:
                        report.issues.append(
                            vaultlib.Issue(rel, "prior_revision file revision does not match the mandate")
                        )
                    if rdata.get("date") != data.get("confirmed_on"):
                        report.issues.append(
                            vaultlib.Issue(rel, "prior_revision date does not match confirmed_on")
                        )
    activity = data.get("activity")
    if activity in OPEN_VALUES or activity not in schema["enums"]["activities"]:
        return
    direct_kinds = set(schema["direct_kinds"])
    direct = [item for item in strategies if item.get("strategy_kind") in direct_kinds]
    funds = [item for item in strategies if item.get("strategy_kind") == "fund_selection"]
    if activity == "direct" and funds:
        report.issues.append(
            vaultlib.Issue(
                rel,
                "activity is direct but a fund_selection subprofile is present. "
                "Set activity to both or remove that subprofile. Do not collapse them.",
            )
        )
    if activity == "direct" and not direct:
        report.issues.append(
            vaultlib.Issue(rel, "activity is direct but no direct subprofile is listed")
        )
    if activity == "fund_selection" and direct:
        report.issues.append(
            vaultlib.Issue(
                rel,
                "activity is fund_selection but a direct subprofile is present. "
                "Set activity to both or remove that subprofile. Do not collapse them.",
            )
        )
    if activity == "fund_selection" and not funds:
        report.issues.append(
            vaultlib.Issue(rel, "activity is fund_selection but no fund_selection subprofile is listed")
        )
    if activity == "both" and (not direct or not funds):
        report.issues.append(
            vaultlib.Issue(
                rel,
                "activity is both: add one direct subprofile and one fund_selection subprofile. "
                "Do not collapse them.",
            )
        )


def _check_example(report, rel, data, body, path: Path) -> None:
    if data.get("synthetic") is not True:
        report.issues.append(vaultlib.Issue(rel, "example profile requires synthetic: true"))
    text = path.read_text(encoding="utf-8")
    if re.search(r"https?://", text, re.I):
        report.issues.append(vaultlib.Issue(rel, "example profile must not contain http:// or https://"))
    if not re.search(r"fictional", body, re.I):
        report.issues.append(vaultlib.Issue(rel, "example profile body must say that it is fictional"))


def _check_id(report, schema, rel, value) -> None:
    if not isinstance(value, str) or vaultlib.contains_placeholder(value):
        return
    if not re.fullmatch(schema["id_pattern"], value):
        report.issues.append(vaultlib.Issue(rel, f"id '{value}' must match {schema['id_pattern']}"))


def _remember_id(report, seen: dict, value, rel: str) -> None:
    if not isinstance(value, str) or not value:
        return
    if value in seen:
        report.issues.append(vaultlib.Issue(rel, f"duplicate id '{value}' also used by {seen[value]}"))
    else:
        seen[value] = rel


def _safe_join(profile: Path, raw: str) -> Path | None:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        return None
    target = (profile / path).resolve()
    try:
        target.relative_to(profile.resolve())
    except ValueError:
        return None
    return target


def _section(body: str, name: str) -> str:
    marker = f"## {name}"
    if marker not in body:
        return ""
    rest = body.split(marker, 1)[1]
    next_heading = re.search(r"\n## ", rest)
    if next_heading:
        rest = rest[: next_heading.start()]
    return rest.strip()
