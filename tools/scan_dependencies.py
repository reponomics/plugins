"""Resolve the maintainer tools without installation and scan their exact versions."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile


VERSION = "2.7.0"
PIN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*==[A-Za-z0-9][A-Za-z0-9.!+_-]*")


def resolve_python(work):
    """Allow registry pins only: input cannot enable an index, sdist or build hook."""
    lines = Path("requirements-dev.txt").read_text().splitlines()
    pins = [p for line in lines if (p := line.partition("#")[0].strip())]
    if not pins or not all(PIN.fullmatch(p) for p in pins):
        raise ValueError("requirements-dev.txt must contain exact name==version pins")
    report = work / "pip-report.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "install",
            "--dry-run",
            "--ignore-installed",
            "--only-binary=:all:",
            "--index-url",
            "https://pypi.org/simple",
            "--report",
            str(report),
            *pins,
        ],
        check=True,
    )
    packages = [row["metadata"] for row in json.loads(report.read_text())["install"]]
    inventory = {
        ("PyPI", re.sub(r"[-_.]+", "-", p["name"]).lower(), p["version"])
        for p in packages
    }
    if not inventory:
        raise ValueError("pip resolved no packages")
    (work / "requirements.txt").write_text(
        "".join(f"{n}=={v}\n" for _, n, v in sorted(inventory))
    )
    return inventory


def locked_npm():
    packages = json.loads(Path("package-lock.json").read_text())["packages"]
    return {
        (
            "npm",
            package.get("name", path.rsplit("node_modules/", 1)[-1]),
            package["version"],
        )
        for path, package in packages.items()
        if path
    }


def audit_result(code, result, expected):
    """Do not turn an incomplete extractor result into a successful release gate."""
    observed, findings = set(), set()
    for source in result["results"]:
        for item in source["packages"]:
            p = item["package"]
            observed.add((p["ecosystem"], p["name"], p["version"]))
            findings.update(v["id"] for v in item.get("vulnerabilities", []))
    if expected != observed:
        raise ValueError(
            f"inventory mismatch: missing {sorted(expected - observed)}; unexpected {sorted(observed - expected)}"
        )
    if bool(code) != bool(findings):
        raise ValueError("OSV-Scanner findings and exit status disagree")
    return sorted(findings)


def scan(scanner, work, report):
    version = subprocess.check_output([scanner, "--version"], text=True).splitlines()
    if f"osv-scanner version: {VERSION}" not in version:
        raise ValueError(f"expected OSV-Scanner {VERSION}")
    expected = resolve_python(work) | locked_npm()
    # Ignore no packages or advisories, including those marked unimportant by default.
    config = work / "osv-scanner.toml"
    config.write_text("")
    code = subprocess.run(
        [
            scanner,
            "scan",
            "source",
            "--no-resolve",
            "--all-packages",
            "--all-vulns",
            "--config",
            str(config),
            "--format",
            "json",
            "--output-file",
            str(report),
            "-L",
            "package-lock.json",
            "-L",
            str(work / "requirements.txt"),
        ]
    ).returncode
    if code not in (0, 1):
        raise ValueError(f"OSV-Scanner operational error (exit {code})")
    findings = audit_result(code, json.loads(report.read_text()), expected)
    return len(expected), findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scanner", default="osv-scanner")
    parser.add_argument("--output", type=Path, default=Path(".cache/dependency-scan"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = args.output / "osv-results.json"
    report.unlink(missing_ok=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    scope = (
        f"# Dependency scan\n\nCommit: `{commit}`\n\n"
        f"Scanned at {datetime.now(timezone.utc).isoformat()} using OSV-Scanner {VERSION}; "
        f"Python {platform.python_version()} on {platform.system()} {platform.machine()}.\n\n"
        "Scope: repository maintainer tooling in the root npm lockfile (including dev dependencies) "
        "and requirements-dev.txt, including transitive wheels resolved for this platform at scan time. "
        "This is not a scan of consumers' dependencies, sample workflows, action implementations, "
        "pre-commit hook environments, or host system packages. Results cover known OSV advisories.\n\n"
    )
    try:
        # A local rehearsal must not label modified inputs as belonging to HEAD.
        subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                "HEAD",
                "--",
                "requirements-dev.txt",
                "package-lock.json",
            ],
            check=True,
        )
        with tempfile.TemporaryDirectory() as directory:
            count, findings = scan(args.scanner, Path(directory), report)
        outcome = (
            "BLOCKED: " + ", ".join(findings)
            if findings
            else "PASS: no known vulnerabilities found."
        )
        status = int(bool(findings))
        scope += f"Compared {count} distinct ecosystem/name/version coordinates.\n\n{outcome}\n"
    except (
        OSError,
        subprocess.CalledProcessError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        scope += f"INCOMPLETE: {exc}. No release decision can rely on this scan.\n"
        status = 2
    (args.output / "scan-scope.md").write_text(scope)
    print(scope)
    return status


if __name__ == "__main__":
    sys.exit(main())
