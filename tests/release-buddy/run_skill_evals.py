"""Opt-in live skill smoke runs: make eval-release-skills EVAL_CASES=monorepo.

Uses the configured Claude client/model and may consume paid usage. It records
observations, not semantic grades; inspect responses and tool calls manually.
Word counts include all whitespace-separated response tokens, including code.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CASE_FILE = Path(__file__).with_name("skill_eval_cases.json")
TOOLS = "Skill,Read,Glob,Grep,WebFetch"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", default=[], help="Case ID; repeat to select several")
    parser.add_argument("--repeat", type=int, default=1, help="Fresh runs per case")
    parser.add_argument("--output", type=Path, default=ROOT / ".cache/releases/skill-evals.json")
    parser.add_argument("--claude", default="claude")
    parser.add_argument("--plugin", type=Path, default=ROOT / "plugins/release-buddy")
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    return args


def plugin_digest(plugin: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(plugin.rglob("*")):
        if path.is_file() and path.suffix in {".md", ".json", ".yml", ".yaml"}:
            digest.update(str(path.relative_to(plugin)).encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def repository_state(plugin: Path) -> dict:
    try:
        head = subprocess.run(["git", "-C", str(plugin), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        status = subprocess.run(["git", "-C", str(plugin), "status", "--porcelain", "--untracked-files=normal"],
                                capture_output=True, text=True, check=True).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        return {"head": None, "dirty": None, "changed_paths": []}
    return {"head": head, "dirty": bool(status), "changed_paths": [line[3:] for line in status]}


def command(args: argparse.Namespace, prompt: str) -> list[str]:
    return [args.claude, "--restricted", "--setting-sources", "", "--strict-mcp-config",
            "--no-session-persistence", "--plugin-dir", str(args.plugin), "--add-dir", str(args.plugin),
            "--tools", TOOLS, "--allowedTools", TOOLS, "--permission-mode", "dontAsk",
            "--output-format", "stream-json", "--verbose", "-p", prompt]


def scrub(text: str, plugin: Path, fixture: Path) -> str:
    for path, replacement in ((plugin, "<plugin>"), (fixture, "<fixture>"), (Path.home(), "<home>")):
        for spelling in {str(path), str(path.resolve())}:
            text = text.replace(spelling, replacement)
    return text


def read_path(value: str, plugin: Path, fixture: Path) -> str:
    path = Path(value).resolve()
    for base, label in ((plugin, "plugin"), (fixture, "fixture")):
        if path.is_relative_to(base.resolve()):
            return f"{label}/{path.relative_to(base.resolve())}"
    return "<outside-scope>/" + path.name


def tool_call(block: dict, plugin: Path, fixture: Path) -> dict:
    name, inputs = block.get("name", ""), block.get("input", {})
    call = {"tool": name}
    if name == "Skill":
        call["skill"] = inputs.get("skill")
    elif name == "Read":
        call["path"] = read_path(inputs.get("file_path", ""), plugin, fixture)
    elif name == "WebFetch":
        call["url"] = inputs.get("url")
    return call


def record_event(event: dict, summary: dict, plugin: Path, fixture: Path) -> None:
    kind = event.get("type")
    if kind == "system" and event.get("subtype") == "init":
        summary.update(model=event.get("model"), client=event.get("claude_code_version"))
    elif kind == "assistant":
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                summary["tool_calls"].append(tool_call(block, plugin, fixture))
    elif kind == "result":
        summary.update(result=scrub(event.get("result") or "", plugin, fixture),
                       result_status=event.get("subtype"), is_error=event.get("is_error", False))


def parse_transcript(output: str, summary: dict, plugin: Path, fixture: Path) -> None:
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            record_event(event, summary, plugin, fixture)


def execute(cmd: list[str], fixture: Path) -> tuple[str, str, int | None]:
    try:
        result = subprocess.run(cmd, cwd=fixture, capture_output=True, text=True, timeout=180)
        return result.stdout, "completed", result.returncode
    except subprocess.TimeoutExpired as error:
        output = error.stdout or b""
        return output.decode(errors="replace") if isinstance(output, bytes) else output, "timeout", None
    except OSError:
        return "", "launch_error", None


def run_case(args: argparse.Namespace, case: dict, repetition: int) -> dict:
    summary = {"case": case["id"], "repetition": repetition,
               "started_at": datetime.now(timezone.utc).isoformat(), "tool_calls": [], "is_error": True}
    with tempfile.TemporaryDirectory(prefix="release-skill-eval-") as directory:
        fixture = Path(directory)
        (fixture / "README.md").write_text(case["fixture"], encoding="utf-8")
        output, status, code = execute(command(args, case["prompt"]), fixture)
        summary.update(execution_status=status, exit_code=code)
        parse_transcript(output, summary, args.plugin, fixture)
    summary["word_count"] = len(summary.get("result", "").split())
    limit = case.get("diagnostic_max_words")
    if limit is not None:
        within = summary["word_count"] <= limit if "result" in summary else None
        summary.update(diagnostic_max_words=limit, within_word_budget=within)
    return summary


def save(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def main() -> int:
    args = arguments()
    args.plugin = args.plugin.resolve()
    cases = {case["id"]: case for case in json.loads(CASE_FILE.read_text(encoding="utf-8"))}
    selected = args.case or list(cases)
    unknown = set(selected) - cases.keys()
    if unknown:
        raise SystemExit("Unknown cases: " + ", ".join(sorted(unknown)))
    if not (args.plugin / ".claude-plugin/plugin.json").is_file():
        raise SystemExit("Plugin manifest not found")
    report = {"repository": repository_state(args.plugin), "plugin_sha256": plugin_digest(args.plugin),
              "cases": [cases[key] for key in selected], "runs": []}
    save(args.output, report)
    for key in selected:
        for repetition in range(1, args.repeat + 1):
            print(f"Running {key} ({repetition}/{args.repeat})", flush=True)
            result = run_case(args, cases[key], repetition)
            report["runs"].append(result)
            save(args.output, report)
            print(f"  {result['execution_status']}; {result['word_count']} words", flush=True)
    return int(any(run["exit_code"] != 0 or run["is_error"] for run in report["runs"]))


if __name__ == "__main__":
    raise SystemExit(main())
