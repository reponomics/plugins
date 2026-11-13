#!/usr/bin/env python3
"""Plan reviewed plugin versions and publish verified GitHub-native releases."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.parse import quote

MARKETPLACE = ".claude-plugin/marketplace.json"
NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, capture_output=True, text=True)


def git(*args: str) -> str:
    return run("git", *args).stdout.strip()


def resolve(ref: str) -> str:
    return git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}")


def _version(value: Any) -> tuple[str, bool]:
    match = SEMVER.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValueError(f"invalid plugin semantic version: {value!r}")
    prerelease = match.group(4)
    if prerelease and any(
        part.isdigit() and len(part) > 1 and part[0] == "0"
        for part in prerelease.split(".")
    ):
        raise ValueError(
            f"prerelease numeric identifiers cannot have leading zeroes: {value}"
        )
    return value, prerelease is not None


def _precedence(version: str) -> tuple:
    match = SEMVER.fullmatch(version)
    assert match is not None
    identifiers = tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in (match.group(4) or "").split(".")
    )
    return (*map(int, match.group(1, 2, 3)), match.group(4) is None, identifiers)


def _path(value: Any) -> str:
    if not isinstance(value, str) or not value.startswith("./"):
        raise ValueError("release entries must use local ./ plugin paths")
    raw = value[2:]
    if raw == "":
        return "."
    if not re.fullmatch(r"[A-Za-z0-9_.\-/]+", raw) or any(
        p in {"", ".", ".."} for p in raw.split("/")
    ):
        raise ValueError(f"unsafe plugin path: {value!r}")
    return str(PurePosixPath(raw))


def _json_at(ref: str, path: str) -> dict:
    payload = json.loads(git("show", f"{ref}:{path}"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _local_plugin(ref: str, entry: Any) -> dict | None:
    if not isinstance(entry, dict):
        raise ValueError("invalid marketplace entry")
    # External plugins have their own repository's release lifecycle.
    if isinstance(entry.get("source"), dict):
        return None
    name, path = entry.get("name"), _path(entry.get("source"))
    if not isinstance(name, str) or NAME.fullmatch(name) is None:
        raise ValueError(f"invalid plugin name: {name!r}")
    manifest = _json_at(ref, str(PurePosixPath(path) / ".claude-plugin/plugin.json"))
    if manifest.get("name") != name:
        raise ValueError(f"{name}: plugin and marketplace names disagree")
    version, prerelease = _version(manifest.get("version"))
    return {"name": name, "path": path, "version": version, "prerelease": prerelease}


def plugins_at(ref: str) -> dict[str, dict]:
    entries = _json_at(ref, MARKETPLACE).get("plugins")
    if not isinstance(entries, list):
        raise ValueError("marketplace must contain a plugins array")
    plugins, paths = {}, set()
    for entry in entries:
        plugin = _local_plugin(ref, entry)
        if plugin is None:
            continue
        name, path = plugin["name"], plugin["path"]
        if name in plugins or path in paths:
            raise ValueError(f"duplicate plugin name/path: {name!r}")
        plugins[name] = plugin
        paths.add(path)
    return plugins


def plan(base: str = "HEAD^", head: str = "HEAD") -> dict:
    head_sha = resolve(head)
    base_sha = None if base == "empty" else resolve(base)
    previous = plugins_at(base_sha) if base_sha else {}
    changed = []
    for name, plugin in plugins_at(head_sha).items():
        old = previous.get(name, {}).get("version")
        if old == plugin["version"]:
            _check_catalog_version(plugin, base_sha, head_sha)
            if not _first_reviewed_notes(plugin, base_sha, head_sha):
                continue
        if (
            old is not None
            and old != plugin["version"]
            and not _valid_transition(name, old, plugin["version"], head_sha)
        ):
            raise ValueError(
                f"{name}: changed version must increase in SemVer precedence"
            )
        release_notes(plugin, head_sha)
        changed.append(
            {**plugin, "previous_version": old, "tag": f"{name}--v{plugin['version']}"}
        )
    return {"base": base_sha, "head": head_sha, "plugins": changed}


def _valid_transition(name: str, previous: str, version: str, head: str) -> bool:
    before, after = _precedence(previous), _precedence(version)
    if after >= before:
        return after > before  # Build metadata alone cannot be a version bump.
    if git("rev-parse", "--is-shallow-repository") != "false":
        return False
    tags = git("tag", "--list", f"{name}--v*").splitlines()
    # The first publication can reset an inherited version. Its exact lightweight
    # tag preserves that decision on historical retries, even after later releases.
    own_tag = f"{name}--v{version}"
    return not tags or (
        own_tag in tags and git("rev-parse", f"refs/tags/{own_tag}") == head
    )


def _check_catalog_version(plugin: dict, base: str, head: str) -> None:
    if plugin["name"] != "badge-buddy":
        return
    path = str(PurePosixPath(plugin["path"]) / "assets/criteria/criteria.json")
    changed = run("git", "diff", "--quiet", base, head, "--", path, check=False)
    if changed.returncode == 1:
        raise ValueError(
            "badge-buddy criteria catalog changed without a plugin version bump"
        )
    if changed.returncode:
        raise subprocess.CalledProcessError(
            changed.returncode, changed.args, changed.stdout, changed.stderr
        )


def _notes_path(plugin: dict) -> str:
    return f"docs/release-notes/{plugin['name']}/{plugin['version']}.md"


def release_notes(plugin: dict, head: str) -> str:
    path = _notes_path(plugin)
    entry = git("ls-tree", head, "--", path)
    if not entry.startswith(("100644 blob ", "100755 blob ")):
        raise ValueError(f"missing regular reviewed release notes file: {path}")
    notes = run("git", "show", f"{head}:{path}").stdout
    if not notes.strip():
        raise ValueError(f"empty release notes: {path}")
    return notes


def _first_reviewed_notes(plugin: dict, base: str, head: str) -> bool:
    path = _notes_path(plugin)
    if git("ls-tree", base, "--", path) or not git("ls-tree", head, "--", path):
        return False
    # A tag at this exact event commit is an idempotent publication retry.
    tag = f"refs/tags/{plugin['name']}--v{plugin['version']}"
    existing = run("git", "rev-parse", "--verify", tag, check=False)
    return existing.returncode != 0 or existing.stdout.strip() == head


def api(endpoint: str, *args: str, missing: bool = False) -> dict | None:
    time.sleep(0.5)
    response = run("gh", "api", "--include", endpoint, *args, check=False)
    headers, _, body = response.stdout.replace("\r\n", "\n").partition("\n\n")
    status = re.match(r"HTTP/\S+ (\d+)", headers)
    if re.search(r"^x-ratelimit-remaining:\s*0\s*$", headers, re.I | re.M):
        raise ValueError(
            "GitHub API rate limit exhausted; inspect the draft before retrying"
        )
    if missing and status and status[1] == "404":
        return None
    if not status or not status[1].startswith("2") or response.returncode:
        raise ValueError(
            f"GitHub API {endpoint}: {response.stderr.strip() or headers.splitlines()[:1]}"
        )
    return json.loads(body)


ASSETS = ("osv-results.json", "scan-scope.md")


def evidence_digests(directory: Path) -> dict[str, str]:
    if {p.name for p in directory.iterdir()} != set(ASSETS):
        raise ValueError("expected exactly osv-results.json and scan-scope.md")
    hashes = {}
    for name in ASSETS:
        p = directory / name
        if p.is_symlink() or not p.is_file() or not p.stat().st_size:
            raise ValueError(f"empty or invalid evidence file: {name}")
        hashes[name] = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


def _validate_scan_package(item: Any) -> None:
    if not isinstance(item, dict) or not isinstance(item.get("package"), dict):
        raise ValueError("malformed OSV package")
    package = item["package"]
    coordinate = tuple(package.get(key) for key in ("ecosystem", "name", "version"))
    if not all(isinstance(value, str) and value for value in coordinate):
        raise ValueError("malformed OSV package coordinate")
    if coordinate[0] not in {"npm", "PyPI"}:
        raise ValueError("unexpected ecosystem in release evidence")
    vulnerabilities = item.get("vulnerabilities", [])
    if not isinstance(vulnerabilities, list) or vulnerabilities:
        raise ValueError("invalid or nonempty vulnerabilities in release evidence")


def _validate_scan_results(report: dict) -> None:
    results = report.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("missing completed OSV results")
    for source in results:
        packages = source.get("packages") if isinstance(source, dict) else None
        if not isinstance(packages, list) or not packages:
            raise ValueError("missing OSV package inventory")
        for item in packages:
            _validate_scan_package(item)


def validate_evidence(directory: Path, head: str) -> dict[str, str]:
    hashes = evidence_digests(directory)
    report = json.loads((directory / "osv-results.json").read_text())
    if not isinstance(report, dict):
        raise ValueError("OSV report must be an object")
    _validate_scan_results(report)
    scope = (directory / "scan-scope.md").read_text()
    # The successful scan job and same-run artifact identity establish completeness.
    # These checks bind its evidence to the release without parsing editorial prose.
    lines = [line.strip() for line in scope.splitlines()]
    commits = [line for line in lines if line.startswith("Commit:")]
    outcomes = [line for line in lines if line.startswith("PASS:")]
    if (
        commits != [f"Commit: `{head}`"]
        or outcomes != ["PASS: no known vulnerabilities found."]
        or "BLOCKED" in scope
        or "INCOMPLETE" in scope
    ):
        raise ValueError(
            "scan scope must record one exact commit and a successful PASS outcome"
        )
    return hashes


def check_checkout(base: str, head: str) -> None:
    if not re.fullmatch(r"[a-f0-9]{40}", head) or head != resolve("HEAD"):
        raise ValueError("publish requires the full event SHA equal to checkout HEAD")
    if base != "empty" and re.fullmatch(r"[a-f0-9]{40}", base) is None:
        raise ValueError("publish requires the full event base SHA or empty")
    if git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("publication requires full history and tags")
    for ancestor, descendant in ((head, "refs/remotes/origin/main"), (base, head)):
        if ancestor == "empty":
            continue
        if run(
            "git", "merge-base", "--is-ancestor", ancestor, descendant, check=False
        ).returncode:
            raise ValueError(
                "release commit must be on origin/main and descend from the event base"
            )


def remote_ref(repository: str, plugin: dict) -> dict | None:
    ref = api(
        f"repos/{repository}/git/ref/tags/{quote(plugin['tag'], safe='')}", missing=True
    )
    if ref is not None:
        target = ref.get("object", {})
        if target.get("sha") != plugin["head"] or target.get("type") != "commit":
            raise ValueError("remote release tag conflicts with the exact event commit")
    return ref


def _existing_release(repository: str, tag: str) -> dict | None:
    record = api(
        f"repos/{repository}/releases/tags/{quote(tag, safe='')}", missing=True
    )
    if record is not None:
        if record.get("draft") is not False:
            raise ValueError(
                "existing draft; inspect and explicitly recover it before retrying"
            )
        return record
    # REST's by-tag endpoint can hide drafts. GraphQL includes drafts for push callers.
    owner, repo = repository.split("/")
    data = api(
        "graphql",
        "-f",
        "query=query($o:String!,$r:String!,$t:String!){repository(owner:$o,name:$r){release(tagName:$t){id}}}",
        "-f",
        f"o={owner}",
        "-f",
        f"r={repo}",
        "-f",
        f"t={tag}",
    )
    if data["data"]["repository"]["release"] is not None:
        raise ValueError(
            "existing draft; inspect and explicitly recover it before retrying"
        )
    return None


def _asset_digests(record: dict) -> dict[str, str]:
    assets = record.get("assets")
    if not isinstance(assets, list) or len(assets) != len(ASSETS):
        raise ValueError("release must contain exactly the expected evidence assets")
    hashes = {}
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("state") != "uploaded":
            raise ValueError("release evidence asset is not uploaded")
        name, digest = asset.get("name"), asset.get("digest")
        if (
            name not in ASSETS
            or name in hashes
            or not isinstance(digest, str)
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest)
        ):
            raise ValueError("release evidence asset names or digests are invalid")
        hashes[name] = digest
    return hashes


def _check_release_subject(record: dict, plugin: dict) -> None:
    expected = {"tag_name": plugin["tag"], "target_commitish": plugin["head"]}
    if any(record.get(key) != value for key, value in expected.items()):
        raise ValueError(
            "release subject differs from the exact reviewed tag and commit"
        )


def check_release(record: dict, plugin: dict, hashes: dict[str, str]) -> None:
    _check_release_subject(record, plugin)
    expected = {
        "name": f"{plugin['name']} {plugin['version']}",
        "prerelease": plugin["prerelease"],
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise ValueError("release metadata differs from the exact reviewed release")
    notes = release_notes(plugin, plugin["head"]).replace("\r\n", "\n").strip()
    body = record.get("body")
    if not isinstance(body, str) or body.replace("\r\n", "\n").strip() != notes:
        raise ValueError("release notes differ from the reviewed commit")
    if _asset_digests(record) != hashes:
        raise ValueError("release evidence digests differ; leave draft unpublished")


def verify_published(
    repository: str, plugin: dict, record: dict, hashes: dict[str, str] | None = None
) -> None:
    if record.get("immutable") is not True or record.get("draft") is not False:
        raise ValueError(
            "GitHub did not confirm an immutable published release; inspect repository immutability settings and this release"
        )
    _check_release_subject(record, plugin)
    if remote_ref(repository, plugin) is None:
        raise ValueError("published release tag is missing")
    if hashes is None:
        # A rerun verifies the original assets, not a fresh scan's timestamped bytes.
        hashes = _asset_digests(record)
        with tempfile.TemporaryDirectory(prefix="release-evidence-") as temp:
            run(
                "gh",
                "release",
                "download",
                plugin["tag"],
                "--repo",
                repository,
                "--dir",
                temp,
                "--pattern",
                ASSETS[0],
                "--pattern",
                ASSETS[1],
            )
            if validate_evidence(Path(temp), plugin["head"]) != hashes:
                raise ValueError(
                    "published evidence bytes do not match recorded digests"
                )
    else:
        # New publication still must match reviewed notes and all draft metadata.
        check_release(record, plugin, hashes)
    run("gh", "release", "verify", plugin["tag"], "--repo", repository)
    print(f"Verified immutable release: {record['html_url']}")


def _create_draft(repository: str, plugin: dict) -> int:
    payload = {
        "tag_name": plugin["tag"],
        "name": f"{plugin['name']} {plugin['version']}",
        "body": release_notes(plugin, plugin["head"]),
        "target_commitish": plugin["head"],
        "draft": True,
        "prerelease": plugin["prerelease"],
        "make_latest": "false",
    }
    with tempfile.TemporaryDirectory() as temp:
        request = Path(temp) / "draft.json"
        request.write_text(json.dumps(payload))
        created = api(
            f"repos/{repository}/releases",
            "--method",
            "POST",
            "-H",
            "Content-Type: application/json",
            "--input",
            str(request),
        )
    release_id = created.get("id")
    if (
        created.get("draft") is not True
        or created.get("tag_name") != plugin["tag"]
        or type(release_id) is not int
        or release_id <= 0
    ):
        raise ValueError("unexpected GitHub draft response; inspect before retrying")
    return release_id


def _upload_evidence(
    repository: str, release_id: int, directory: Path, hashes: dict[str, str]
) -> None:
    for name in ASSETS:
        path = directory / name
        endpoint = f"https://uploads.github.com/repos/{repository}/releases/{release_id}/assets?name={name}"
        asset = api(
            endpoint,
            "--method",
            "POST",
            "-H",
            "Content-Type: application/octet-stream",
            "-H",
            f"Content-Length: {path.stat().st_size}",
            "--input",
            str(path),
        )
        if asset.get("digest") != hashes[name] or asset.get("state") != "uploaded":
            raise ValueError(
                f"uploaded evidence mismatch for {name}; leave draft unpublished"
            )


def _publish_new(
    repository: str, plugin: dict, directory: Path, hashes: dict[str, str]
) -> None:
    if remote_ref(repository, plugin) is None:
        api(
            f"repos/{repository}/git/refs",
            "--method",
            "POST",
            "-f",
            f"ref=refs/tags/{plugin['tag']}",
            "-f",
            f"sha={plugin['head']}",
        )
    if remote_ref(repository, plugin) is None:
        raise ValueError("release tag creation was not confirmed")
    release_id = _create_draft(repository, plugin)
    _upload_evidence(repository, release_id, directory, hashes)
    endpoint = f"repos/{repository}/releases/{release_id}"
    record = api(endpoint)
    if record.get("id") != release_id or record.get("draft") is not True:
        raise ValueError("new draft identity changed; inspect before retrying")
    check_release(record, plugin, hashes)
    if remote_ref(repository, plugin) is None:
        raise ValueError("release tag disappeared; leave draft unpublished")
    api(endpoint, "--method", "PATCH", "-F", "draft=false", "-f", "make_latest=false")
    verify_published(repository, plugin, api(endpoint), hashes)


def publish(base: str, head: str, repository: str, directory: Path) -> None:
    if not REPOSITORY.fullmatch(repository) or ".." in repository:
        raise ValueError("expected OWNER/REPO")
    check_checkout(base, head)
    selected = [{**plugin, "head": head} for plugin in plan(base, head)["plugins"]]
    hashes = validate_evidence(directory, head)
    pending = []
    for plugin in selected:
        remote_ref(repository, plugin)
        existing = _existing_release(repository, plugin["tag"])
        if existing is not None:
            verify_published(repository, plugin, existing)
        else:
            pending.append(plugin)
    for plugin in pending:
        _publish_new(repository, plugin, directory, hashes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("plan")
    prepare.add_argument("--base", default="HEAD^")
    prepare.add_argument("--head", default="HEAD")
    prepare.add_argument("--output", type=Path, required=True)
    publication = commands.add_parser("publish")
    publication.add_argument("--base", required=True)
    publication.add_argument("--head", required=True)
    publication.add_argument("--repository", required=True)
    publication.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            result = plan(args.base, args.head)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
            print(f"Planned {len(result['plugins'])} plugin release(s): {args.output}")
        else:
            publish(args.base, args.head, args.repository, args.evidence)
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Plugin release failed: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
